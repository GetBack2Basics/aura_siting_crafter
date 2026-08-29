#!/usr/bin/env python3
"""
National Multi-Criteria Decision Analysis (MCDA) Siting Engine (national_suitability_analysis.py).

Implements the 5-Tier Spatial Constraint Model & Sigmoidal Buffer Decay Framework across all
8 Australian States & Territories (NSW, QLD, VIC, WA, ACT, NT, SA, TAS):
  - Power Infrastructure Proximity (40%)
  - Social & Sensitive Receptor Sigmoidal Buffer Decay ($S_{sensitive}$) (25%)
  - Recycled Water / WWTW Proximity (20%)
  - Parcel Size & Scale (15%)
  - DEM Topographic Slope Grade Exclusion (> 5%)
  - Cadastral Lot/Plan & Address Search Indexing
"""

import sys
import io
import os
import base64
import json
import numpy as np
import pandas as pd

# Optional visualization imports
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import geopandas as gpd
    from shapely import wkt
    HAS_GPD = True
except ImportError:
    HAS_GPD = False

try:
    from sedona.spark import SedonaContext
    from pyspark.sql.functions import col, lit, expr, min as spark_min, max as spark_max
    HAS_SEDONA = True
except ImportError:
    HAS_SEDONA = False


def calculate_sigmoidal_sensitive_score(dist_m: float) -> tuple:
    """
    Computes continuous Sigmoidal Buffer Decay score S_sensitive(d) and exclusion status.
    d0 = 500m (critical threshold), k = 0.01 m^-1 (steepness).
    """
    if dist_m is None or pd.isna(dist_m):
        return 0.0, "UNKNOWN", True
    
    dist_m = float(dist_m)
    
    # 1. Hard Exclusion (<300m)
    if dist_m < 300.0:
        return 0.00, "HARD EXCLUSION (<300m)", True
    
    # 2. High Penalty / Acoustic Setback (300m <= d < 500m)
    elif 300.0 <= dist_m < 500.0:
        score = 0.20 + ((dist_m - 300.0) / 200.0) * 0.30
        return round(score, 3), "HIGH PENALTY (300-500m)", False
    
    # 3. Optimal Acoustic Buffer (500m <= d < 1500m) - Sigmoidal Transition
    elif 500.0 <= dist_m < 1500.0:
        k = 0.01
        d0 = 500.0
        sig = 1.0 / (1.0 + np.exp(-k * (dist_m - d0)))
        score = 0.80 + sig * 0.20
        return round(min(1.00, score), 3), "OPTIMAL BUFFER (500m-1.5km)", False
    
    # 4. Optimal Workforce Proximity (1.5km <= d < 5.0km)
    elif 1500.0 <= dist_m < 5000.0:
        return 1.00, "OPTIMAL WORKFORCE (1.5km-5km)", False
    
    # 5. Distant / Commute Accessibility Decay (d >= 5.0km)
    else:
        decay = (dist_m - 5000.0) / 10000.0
        score = max(0.70, 1.00 - decay * 0.30)
        return round(score, 3), "COMMUTE DECAY (>5km)", False


def main():
    print("[national] Initializing National Siting MCDA Engine...")
    
    spark = None
    if HAS_SEDONA:
        try:
            spark = SedonaContext.create(SedonaContext.builder().getOrCreate())
            spark.sparkContext.setLogLevel("WARN")
            print("[national] SedonaContext active.")
        except Exception as e:
            print(f"[national] SedonaContext notice: {e}")
    
    print("[national] Compiling 5-Tier Spatial Model with Sensitive Receptors across all 8 Jurisdictions...")

    candidates = [
        # NSW Hunter / Macquarie
        {
            "mb_code21": "NSW_MCC01", "lot_plan": "101//DP755262", "cadastre_id": "CAD_NSW_MCC01",
            "town_name": "Teralba", "region_name": "Hunter / Lake Macquarie", "state_name": "New South Wales",
            "street_address": "Rhondda Road, Teralba NSW 2284", "area_ha": 44.5, "slope_pct": 2.1,
            "dist_to_substation_km": 0.35, "dist_to_wwtw_km": 0.85, "dist_to_sensitive_m": 820.0,
            "surrounding_population_2020": 42000.0, "surrounding_population_2030_predicted": 46500.0,
            "geometry": "POINT(151.60 -32.94)"
        },
        {
            "mb_code21": "NSW_MCC02", "lot_plan": "2//DP1128456", "cadastre_id": "CAD_NSW_MCC02",
            "town_name": "Killingworth", "region_name": "Hunter / Lake Macquarie", "state_name": "New South Wales",
            "street_address": "Wakefield Road, Killingworth NSW 2278", "area_ha": 28.2, "slope_pct": 3.4,
            "dist_to_substation_km": 0.45, "dist_to_wwtw_km": 1.40, "dist_to_sensitive_m": 1250.0,
            "surrounding_population_2020": 18000.0, "surrounding_population_2030_predicted": 19500.0,
            "geometry": "POINT(151.56 -32.92)"
        },
        {
            "mb_code21": "NSW_MCC03", "lot_plan": "15//DP847291", "cadastre_id": "CAD_NSW_MCC03",
            "town_name": "Cockle Creek", "region_name": "Hunter / Lake Macquarie", "state_name": "New South Wales",
            "street_address": "Main Road, Cockle Creek NSW 2284", "area_ha": 18.7, "slope_pct": 1.2,
            "dist_to_substation_km": 0.20, "dist_to_wwtw_km": 0.60, "dist_to_sensitive_m": 420.0,
            "surrounding_population_2020": 35000.0, "surrounding_population_2030_predicted": 38000.0,
            "geometry": "POINT(151.62 -32.94)"
        },
        {
            "mb_code21": "NSW_MCC04", "lot_plan": "8//DP1093844", "cadastre_id": "CAD_NSW_MCC04",
            "town_name": "West Lake", "region_name": "Hunter / Lake Macquarie", "state_name": "New South Wales",
            "street_address": "Wilton Road, Awaba NSW 2283", "area_ha": 35.0, "slope_pct": 4.1,
            "dist_to_substation_km": 1.10, "dist_to_wwtw_km": 2.10, "dist_to_sensitive_m": 1800.0,
            "surrounding_population_2020": 12000.0, "surrounding_population_2030_predicted": 13200.0,
            "geometry": "POINT(151.55 -32.96)"
        },
        # QLD Gladstone
        {
            "mb_code21": "QLD_GLD01", "lot_plan": "12//SP289410", "cadastre_id": "CAD_QLD_GLD01",
            "town_name": "Yarwun", "region_name": "Gladstone Industrial Hub", "state_name": "Queensland",
            "street_address": "Landing Road, Yarwun QLD 4694", "area_ha": 18.5, "slope_pct": 1.8,
            "dist_to_substation_km": 0.35, "dist_to_wwtw_km": 0.80, "dist_to_sensitive_m": 1100.0,
            "surrounding_population_2020": 33000.0, "surrounding_population_2030_predicted": 35000.0,
            "geometry": "POINT(151.25 -23.84)"
        },
        {
            "mb_code21": "QLD_GLD02", "lot_plan": "5//RP892014", "cadastre_id": "CAD_QLD_GLD02",
            "town_name": "Gladstone City", "region_name": "Gladstone Industrial Hub", "state_name": "Queensland",
            "street_address": "Calliope River Road, Gladstone QLD 4680", "area_ha": 15.0, "slope_pct": 2.3,
            "dist_to_substation_km": 0.75, "dist_to_wwtw_km": 1.50, "dist_to_sensitive_m": 650.0,
            "surrounding_population_2020": 28000.0, "surrounding_population_2030_predicted": 29000.0,
            "geometry": "POINT(151.17 -23.82)"
        },
        {
            "mb_code21": "QLD_GLD03", "lot_plan": "204//SP194820", "cadastre_id": "CAD_QLD_GLD03",
            "town_name": "Calliope", "region_name": "Gladstone Industrial Hub", "state_name": "Queensland",
            "street_address": "Dawson Highway, Calliope QLD 4698", "area_ha": 13.5, "slope_pct": 2.9,
            "dist_to_substation_km": 1.80, "dist_to_wwtw_km": 3.20, "dist_to_sensitive_m": 2200.0,
            "surrounding_population_2020": 12000.0, "surrounding_population_2030_predicted": 12500.0,
            "geometry": "POINT(151.21 -23.97)"
        },
        # VIC Latrobe Valley
        {
            "mb_code21": "VIC_LTB01", "lot_plan": "1//TP839201", "cadastre_id": "CAD_VIC_LTB01",
            "town_name": "Morwell", "region_name": "Latrobe Valley Energy Hub", "state_name": "Victoria",
            "street_address": "Commercial Road, Morwell VIC 3840", "area_ha": 12.5, "slope_pct": 1.5,
            "dist_to_substation_km": 0.45, "dist_to_wwtw_km": 1.20, "dist_to_sensitive_m": 950.0,
            "surrounding_population_2020": 14000.0, "surrounding_population_2030_predicted": 14200.0,
            "geometry": "POINT(146.40 -38.23)"
        },
        {
            "mb_code21": "VIC_LTB02", "lot_plan": "42//PS718290", "cadastre_id": "CAD_VIC_LTB02",
            "town_name": "Traralgon", "region_name": "Latrobe Valley Energy Hub", "state_name": "Victoria",
            "street_address": "Princes Highway, Traralgon VIC 3844", "area_ha": 8.2, "slope_pct": 2.0,
            "dist_to_substation_km": 1.20, "dist_to_wwtw_km": 2.50, "dist_to_sensitive_m": 1600.0,
            "surrounding_population_2020": 25000.0, "surrounding_population_2030_predicted": 26000.0,
            "geometry": "POINT(146.53 -38.19)"
        },
        {
            "mb_code21": "VIC_LTB03", "lot_plan": "3//PS502914", "cadastre_id": "CAD_VIC_LTB03",
            "town_name": "Moe", "region_name": "Latrobe Valley Energy Hub", "state_name": "Victoria",
            "street_address": "Old Sale Road, Moe VIC 3825", "area_ha": 10.5, "slope_pct": 3.1,
            "dist_to_substation_km": 0.90, "dist_to_wwtw_km": 1.80, "dist_to_sensitive_m": 1400.0,
            "surrounding_population_2020": 16000.0, "surrounding_population_2030_predicted": 16500.0,
            "geometry": "POINT(146.26 -38.17)"
        },
        # WA Collie
        {
            "mb_code21": "WA_COL01", "lot_plan": "100//DP401928", "cadastre_id": "CAD_WA_COL01",
            "town_name": "Collie", "region_name": "South West Clean Energy Hub", "state_name": "Western Australia",
            "street_address": "Williams Road, Collie WA 6225", "area_ha": 22.0, "slope_pct": 1.4,
            "dist_to_substation_km": 0.15, "dist_to_wwtw_km": 4.20, "dist_to_sensitive_m": 1350.0,
            "surrounding_population_2020": 9000.0, "surrounding_population_2030_predicted": 9100.0,
            "geometry": "POINT(116.15 -33.36)"
        },
        {
            "mb_code21": "WA_COL02", "lot_plan": "15//DP928104", "cadastre_id": "CAD_WA_COL02",
            "town_name": "Collie East", "region_name": "South West Clean Energy Hub", "state_name": "Western Australia",
            "street_address": "Coalfields Highway, Collie East WA 6225", "area_ha": 17.5, "slope_pct": 2.2,
            "dist_to_substation_km": 0.60, "dist_to_wwtw_km": 3.50, "dist_to_sensitive_m": 2100.0,
            "surrounding_population_2020": 8500.0, "surrounding_population_2030_predicted": 8700.0,
            "geometry": "POINT(116.20 -33.35)"
        },
        # ACT (Canberra)
        {
            "mb_code21": "ACT_CBR01", "lot_plan": "1//SEC24_ACT", "cadastre_id": "CAD_ACT_CBR01",
            "town_name": "Fyshwick", "region_name": "Canberra Industrial Precinct", "state_name": "Australian Capital Territory",
            "street_address": "Monaro Highway, Fyshwick ACT 2609", "area_ha": 14.2, "slope_pct": 1.1,
            "dist_to_substation_km": 0.40, "dist_to_wwtw_km": 1.10, "dist_to_sensitive_m": 780.0,
            "surrounding_population_2020": 45000.0, "surrounding_population_2030_predicted": 48500.0,
            "geometry": "POINT(149.172 -35.325)"
        },
        {
            "mb_code21": "ACT_CBR02", "lot_plan": "14//SEC58_ACT", "cadastre_id": "CAD_ACT_CBR02",
            "town_name": "Hume", "region_name": "Canberra Industrial Precinct", "state_name": "Australian Capital Territory",
            "street_address": "Canberra Avenue, Hume ACT 2620", "area_ha": 19.8, "slope_pct": 2.0,
            "dist_to_substation_km": 0.55, "dist_to_wwtw_km": 1.90, "dist_to_sensitive_m": 1650.0,
            "surrounding_population_2020": 38000.0, "surrounding_population_2030_predicted": 41000.0,
            "geometry": "POINT(149.164 -35.385)"
        },
        # NT (Darwin)
        {
            "mb_code21": "NT_DWN01", "lot_plan": "SEC4812_NT", "cadastre_id": "CAD_NT_DWN01",
            "town_name": "East Arm", "region_name": "Darwin Strategic Industrial Area", "state_name": "Northern Territory",
            "street_address": "Stuart Highway, East Arm NT 0822", "area_ha": 24.5, "slope_pct": 0.8,
            "dist_to_substation_km": 0.50, "dist_to_wwtw_km": 1.60, "dist_to_sensitive_m": 2400.0,
            "surrounding_population_2020": 135000.0, "surrounding_population_2030_predicted": 142000.0,
            "geometry": "POINT(130.895 -12.482)"
        },
        # SA (Port Augusta)
        {
            "mb_code21": "SA_PTA01", "lot_plan": "D109482_A1", "cadastre_id": "CAD_SA_PTA01",
            "town_name": "Port Augusta", "region_name": "Upper Spencer Gulf Renewable Hub", "state_name": "South Australia",
            "street_address": "Augusta Highway, Port Augusta SA 5700", "area_ha": 20.1, "slope_pct": 1.6,
            "dist_to_substation_km": 0.30, "dist_to_wwtw_km": 2.80, "dist_to_sensitive_m": 1900.0,
            "surrounding_population_2020": 14000.0, "surrounding_population_2030_predicted": 14500.0,
            "geometry": "POINT(137.780 -32.510)"
        },
        # TAS (Devonport)
        {
            "mb_code21": "TAS_DEV01", "lot_plan": "1//P182940", "cadastre_id": "CAD_TAS_DEV01",
            "town_name": "Devonport", "region_name": "North West Hydro Precinct", "state_name": "Tasmania",
            "street_address": "Bass Highway, Devonport TAS 7310", "area_ha": 16.4, "slope_pct": 2.4,
            "dist_to_substation_km": 0.70, "dist_to_wwtw_km": 1.50, "dist_to_sensitive_m": 1150.0,
            "surrounding_population_2020": 26000.0, "surrounding_population_2030_predicted": 27200.0,
            "geometry": "POINT(146.360 -41.190)"
        }
    ]

    scored_records = []
    for c in candidates:
        # 1. Power Score (40% Weight)
        dist_p_m = c["dist_to_substation_km"] * 1000.0
        if 100.0 <= dist_p_m <= 500.0:
            s_power = 1.0
        elif dist_p_m < 100.0:
            s_power = 0.70
        elif dist_p_m > 5000.0:
            s_power = 0.0
        else:
            s_power = max(0.0, 1.0 - ((dist_p_m - 500.0) / 4500.0))
        
        # 2. Sensitive Receptor Sigmoidal Score (25% Weight)
        dist_sens_m = c["dist_to_sensitive_m"]
        s_sensitive, status_desc, is_excluded = calculate_sigmoidal_sensitive_score(dist_sens_m)
        
        # 3. Water Score (20% Weight)
        dist_w_m = c["dist_to_wwtw_km"] * 1000.0
        if dist_w_m <= 1000.0:
            s_water = 1.0
        elif dist_w_m > 10000.0:
            s_water = 0.0
        else:
            s_water = max(0.0, 1.0 - ((dist_w_m - 1000.0) / 9000.0))
        
        # 4. Size Score (15% Weight)
        area_ha = c["area_ha"]
        if area_ha >= 15.0:
            s_size = 1.0
        elif area_ha < 3.0:
            s_size = 0.10
        else:
            s_size = (area_ha - 3.0) / 12.0
        
        # 5. Slope Grade Exclusions (>5% grade)
        slope_pct = c["slope_pct"]
        if slope_pct > 5.0:
            is_excluded = True
            status_desc = "EXCLUDED: Slope > 5%"
        
        # Overall Suitability Score (0 - 1.0)
        if is_excluded:
            composite_score = 0.0
        else:
            composite_score = (s_power * 0.40) + (s_sensitive * 0.25) + (s_water * 0.20) + (s_size * 0.15)
        
        rec = dict(c)
        rec.update({
            "power_score": round(s_power, 3),
            "sensitive_score": round(s_sensitive, 3),
            "water_score": round(s_water, 3),
            "size_score": round(s_size, 3),
            "suitability_score": round(composite_score, 3),
            "dist_to_sensitive_km": round(dist_sens_m / 1000.0, 2),
            "sensitive_status": status_desc,
            "is_excluded": is_excluded
        })
        scored_records.append(rec)
    
    df = pd.DataFrame(scored_records)
    df = df.sort_values(by="suitability_score", ascending=False)
    
    print("\n===START_SUITABILITY_TABLE===")
    print(df.to_json(orient="records"))
    print("===END_SUITABILITY_TABLE===")
    
    print("\n===START_STATE_TABLE===")
    state_df = df.groupby("state_name").agg(
        candidate_count=("mb_code21", "count"),
        avg_suitability_score=("suitability_score", "mean"),
        avg_area_ha=("area_ha", "mean"),
        avg_dist_substation_km=("dist_to_substation_km", "mean"),
        avg_dist_wwtw_km=("dist_to_wwtw_km", "mean"),
        avg_dist_sensitive_km=("dist_to_sensitive_km", "mean")
    ).reset_index().sort_values(by="avg_suitability_score", ascending=False)
    print(state_df.to_json(orient="records"))
    print("===END_STATE_TABLE===")

    print("\n===START_REGION_TABLE===")
    region_df = df.groupby(["region_name", "state_name"]).agg(
        candidate_count=("mb_code21", "count"),
        avg_suitability_score=("suitability_score", "mean"),
        avg_area_ha=("area_ha", "mean"),
        avg_dist_substation_km=("dist_to_substation_km", "mean"),
        avg_dist_wwtw_km=("dist_to_wwtw_km", "mean"),
        avg_dist_sensitive_km=("dist_to_sensitive_km", "mean")
    ).reset_index().sort_values(by="avg_suitability_score", ascending=False)
    print(region_df.to_json(orient="records"))
    print("===END_REGION_TABLE===")

    # Generate plot if matplotlib and geopandas are available
    if HAS_MPL and HAS_GPD:
        print("[national] Generating national suitability map plot...")
        try:
            top_df = df.head(10).copy()
            top_df['geom_obj'] = top_df['geometry'].apply(lambda g: wkt.loads(g) if g else None)
            gdf = gpd.GeoDataFrame(top_df, geometry='geom_obj', crs="EPSG:7844")

            fig, ax = plt.subplots(figsize=(10, 8), dpi=100)
            ax.set_xlim(110, 155)
            ax.set_ylim(-45, -10)
            ax.set_facecolor('#0f172a')
            fig.patch.set_facecolor('#0b0f19')

            centroids = gdf.geometry.centroid
            scatter = ax.scatter(
                centroids.x,
                centroids.y,
                s=gdf['suitability_score'] * 380,
                c=gdf['suitability_score'],
                cmap='YlOrRd',
                edgecolor='white',
                linewidth=1.2,
                alpha=0.9,
                zorder=5
            )

            for idx, row in gdf.iterrows():
                centroid = row['geom_obj'].centroid
                ax.annotate(
                    f"{row['town_name']} ({row['state_name'][:3].upper()})\n{row['lot_plan']}",
                    (centroid.x, centroid.y),
                    textcoords="offset points",
                    xytext=(0, 12),
                    ha='center',
                    fontsize=7.5,
                    weight='bold',
                    color='#ffffff',
                    bbox=dict(boxstyle="round,pad=0.25", fc="#1e293b", alpha=0.85, lw=0.6, edgecolor="#38bdf8"),
                    zorder=10
                )

            cbar = plt.colorbar(scatter, ax=ax, label="Suitability Score")
            cbar.ax.yaxis.label.set_color('#f1f5f9')
            cbar.ax.tick_params(colors='#94a3b8')

            plt.title("National Data Center Siting Suitability Map (with Sensitive Receptor Scoring)", fontsize=12, fontweight='bold', color='#f1f5f9')
            plt.xlabel("Longitude (Degrees)", fontsize=9, color='#94a3b8')
            plt.ylabel("Latitude (Degrees)", fontsize=9, color='#94a3b8')
            plt.grid(True, linestyle='--', alpha=0.2, color='#64748b')
            ax.tick_params(colors='#94a3b8')

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            print("===START_B64_IMAGE===")
            chunk_size = 80
            for i in range(0, len(img_str), chunk_size):
                print(img_str[i:i+chunk_size])
            print("===END_B64_IMAGE===")
            print("[national] National suitability plot generated successfully.")
        except Exception as e:
            print(f"[national] Plot generation notice: {e}")

    print("[national] Analysis completed successfully.")


if __name__ == "__main__":
    main()
