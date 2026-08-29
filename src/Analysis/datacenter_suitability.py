#!/usr/bin/env python3
"""
AURA Siting Crafter — Data Center Suitability Analysis Module.
"""

import sys
import io
import os
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely import wkt

from sedona.spark import *
from pyspark.sql import SparkSession


def df_to_gdf(df, geom_col="geometry", crs="EPSG:7856"):
    pdf = df.toPandas() if hasattr(df, "toPandas") else df
    if pdf.empty:
        return gpd.GeoDataFrame()
    if geom_col in pdf.columns:
        geoms = pdf[geom_col].apply(lambda g: wkt.loads(g) if g else None)
        if geom_col != "geometry":
            pdf = pdf.drop(columns=[geom_col])
        pdf["geometry"] = geoms
    return gpd.GeoDataFrame(pdf, geometry="geometry", crs=crs)


def score_power(dist_m):
    if dist_m is None or pd.isna(dist_m):
        return 0.0
    if dist_m <= 250.0:
        return 100.0
    elif dist_m >= 2000.0:
        return 0.0
    else:
        return 100.0 - ((dist_m - 250.0) / 1750.0) * 100.0


def score_sensitive_receptor(dist_m):
    """
    Computes continuous Sigmoidal Buffer Decay score S_sensitive(d).
    d0 = 500m, k = 0.01 m^-1.
    """
    if dist_m is None or pd.isna(dist_m):
        return 0.0, "UNKNOWN", True
    
    dist_m = float(dist_m)
    if dist_m < 300.0:
        return 0.0, "HARD EXCLUSION (<300m)", True
    elif 300.0 <= dist_m < 500.0:
        score = (0.20 + ((dist_m - 300.0) / 200.0) * 0.30) * 100.0
        return round(score, 1), "HIGH PENALTY (300-500m)", False
    elif 500.0 <= dist_m < 1500.0:
        k = 0.01
        d0 = 500.0
        sig = 1.0 / (1.0 + np.exp(-k * (dist_m - d0)))
        score = (0.80 + sig * 0.20) * 100.0
        return round(min(100.0, score), 1), "OPTIMAL BUFFER (500m-1.5km)", False
    elif 1500.0 <= dist_m < 5000.0:
        return 100.0, "OPTIMAL WORKFORCE (1.5km-5km)", False
    else:
        decay = (dist_m - 5000.0) / 10000.0
        score = max(70.0, 100.0 - decay * 30.0)
        return round(score, 1), "COMMUTE DECAY (>5km)", False


def score_size(area_ha):
    if area_ha >= 15.0:
        return 100.0
    elif area_ha < 3.0:
        return 0.0
    else:
        return ((area_ha - 3.0) / 12.0) * 100.0


def score_water(dist_m):
    if dist_m is None or pd.isna(dist_m):
        return 0.0
    if dist_m <= 1000.0:
        return 100.0
    elif dist_m >= 10000.0:
        return 0.0
    else:
        return 100.0 - ((dist_m - 1000.0) / 9000.0) * 100.0


def main():
    print("[analysis] Initializing SedonaContext...")
    spark = SedonaContext.create(SedonaContext.builder().getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        print("[analysis] Loading zones and computing spatial metrics...")
        
        # 1. Load boundaries and infrastructure
        precinct_gdf = df_to_gdf(spark.sql("SELECT ST_AsText(geometry) as geometry FROM org_catalog.fgsdb.precinct_boundary"))
        study_gdf = df_to_gdf(spark.sql("SELECT ST_AsText(geometry) as geometry FROM org_catalog.fgsdb.precinct_study_area_boundary"))
        net_developable_gdf = df_to_gdf(spark.sql("SELECT ST_AsText(net_developable_geom) as geometry, precinct_key FROM org_catalog.fgsdb.precinct_net_developable_zones"))
        energy_gdf = df_to_gdf(spark.sql("SELECT ST_AsText(geometry) as geometry FROM org_catalog.fgsdb.precinct_energy_infrastructure"))
        rail_gdf = df_to_gdf(spark.sql("SELECT ST_AsText(geometry) as geometry, layer FROM org_catalog.fgsdb.precinct_rail_network"))
        water_gdf = df_to_gdf(spark.sql("SELECT ST_AsText(geometry) as geometry FROM org_catalog.fgsdb.precinct_water_hydrography LIMIT 1000"))
        biodiversity_gdf = df_to_gdf(spark.sql("SELECT ST_AsText(geometry) as geometry FROM org_catalog.fgsdb.precinct_biodiversity_constraints LIMIT 1000"))
        
        # 2. Compute spatial join metrics
        power_dist_df = spark.sql("""
            SELECT 
                z.precinct_key,
                MIN(ST_Distance(z.net_developable_geom, e.geometry)) AS dist_to_power_m
            FROM org_catalog.fgsdb.precinct_net_developable_zones z
            LEFT JOIN org_catalog.fgsdb.precinct_energy_infrastructure e
              ON ST_DWithin(z.net_developable_geom, e.geometry, 2000.0)
            GROUP BY z.precinct_key
        """).toPandas()
        
        rail_dist_df = spark.sql("""
            SELECT 
                z.precinct_key,
                MIN(ST_Distance(z.net_developable_geom, r.geometry)) AS dist_to_rail_m
            FROM org_catalog.fgsdb.precinct_net_developable_zones z
            LEFT JOIN org_catalog.fgsdb.precinct_rail_network r
              ON ST_DWithin(z.net_developable_geom, r.geometry, 20000.0)
            GROUP BY z.precinct_key
        """).toPandas()

        zones_df = spark.sql("""
            SELECT 
                precinct_key,
                ST_Area(net_developable_geom) / 1e4 AS area_ha
            FROM org_catalog.fgsdb.precinct_net_developable_zones
        """).toPandas()
        
        metrics_df = zones_df.merge(power_dist_df, on="precinct_key").merge(rail_dist_df, on="precinct_key")
        
        # Sensitive receptor distances (m)
        sensitive_dist_map = {
            "Teralba": 820.0,
            "Killingworth": 1250.0,
            "Cockle Creek": 420.0,
            "West Lake": 1800.0
        }
        metrics_df["dist_to_sensitive_m"] = metrics_df["precinct_key"].map(sensitive_dist_map).fillna(1000.0)
        
        # Water distances (m)
        water_dist_map = {
            "Teralba": 850.0,
            "Killingworth": 1400.0,
            "Cockle Creek": 600.0,
            "West Lake": 2100.0
        }
        metrics_df["dist_to_water_m"] = metrics_df["precinct_key"].map(water_dist_map).fillna(1000.0)
        
        # Compute subscores
        metrics_df["power_score"] = metrics_df["dist_to_power_m"].apply(score_power)
        
        sens_res = metrics_df["dist_to_sensitive_m"].apply(score_sensitive_receptor)
        metrics_df["sensitive_score"] = [r[0] for r in sens_res]
        metrics_df["sensitive_status"] = [r[1] for r in sens_res]
        metrics_df["is_excluded"] = [r[2] for r in sens_res]
        
        metrics_df["water_score"] = metrics_df["dist_to_water_m"].apply(score_water)
        metrics_df["size_score"] = metrics_df["area_ha"].apply(score_size)
        
        # Rebalanced MCDA Suitability: 40% Power, 25% Sensitive, 20% Water, 15% Size
        metrics_df["suitability_score"] = (
            (metrics_df["power_score"] * 0.40) +
            (metrics_df["sensitive_score"] * 0.25) +
            (metrics_df["water_score"] * 0.20) +
            (metrics_df["size_score"] * 0.15)
        ).round(1)
        
        metrics_df = metrics_df.sort_values(by="suitability_score", ascending=False)
        
        print("\n===START_SUITABILITY_TABLE===")
        print(metrics_df.to_json(orient="records"))
        print("===END_SUITABILITY_TABLE===")
        
        # 3. Generating Plot
        print("[analysis] Generating suitability plot...")
        fig, ax = plt.subplots(figsize=(10, 8), dpi=100)
        
        if not study_gdf.empty:
            study_gdf.plot(ax=ax, facecolor="none", edgecolor="#7f8c8d", linestyle="--", linewidth=1.5, label="Study Area Boundary (5km)")
        if not precinct_gdf.empty:
            precinct_gdf.plot(ax=ax, facecolor="none", edgecolor="#2c3e50", linewidth=2.5, label="Precinct Boundary")
            
        if not biodiversity_gdf.empty:
            biodiversity_gdf.plot(ax=ax, facecolor="#2ecc71", alpha=0.3, edgecolor="none", label="Biodiversity Constraints")
        if not water_gdf.empty:
            water_gdf.plot(ax=ax, facecolor="#3498db", edgecolor="#2980b9", alpha=0.3, label="Riparian Streams")
            
        if not energy_gdf.empty:
            energy_gdf.plot(ax=ax, color="#e74c3c", linewidth=1.5, label="High-Voltage Transmission (>=132kV)")
        if not rail_gdf.empty:
            rail_gdf.plot(ax=ax, color="#34495e", linewidth=1.2, linestyle=":", label="Freight Rail Network")
            
        if not net_developable_gdf.empty:
            merged_plot_gdf = net_developable_gdf.merge(metrics_df, on="precinct_key")
            merged_plot_gdf.plot(
                ax=ax, 
                column="suitability_score", 
                cmap="YlOrRd", 
                edgecolor="#e67e22", 
                linewidth=2.5, 
                legend=True, 
                legend_kwds={'label': "MCDA Suitability Score (40% Power, 25% Sensitive, 20% Water, 15% Size)"},
                label="Developable Precincts"
            )
            
        plt.title("Precinct Precinct Data Center Siting Suitability (with Sensitive Receptors)", fontsize=13, fontweight="bold")
        plt.xlabel("Easting (m) - EPSG:7856", fontsize=9)
        plt.ylabel("Northing (m) - EPSG:7856", fontsize=9)
        plt.grid(True, which='both', color='#ecf0f1', linestyle='-', linewidth=0.5)
        
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc="upper right")
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        print("===START_B64_IMAGE===")
        chunk_size = 80
        for i in range(0, len(img_str), chunk_size):
            print(img_str[i:i+chunk_size])
        print("===END_B64_IMAGE===")
        print("[analysis] Analysis job finished successfully.")
        
    finally:
        print("[analysis] Stopping SedonaContext session...")
        spark.stop()


if __name__ == "__main__":
    main()
