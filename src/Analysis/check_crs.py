from sedona.spark import *

def main():
    spark = SedonaContext.create(SedonaContext.builder().getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    
    print("=== Geometry CRS Diagnostics ===")
    try:
        mb = spark.table("org_catalog.fgsdb.precinct_abs_meshblocks")
        print("Meshblock sample point:", mb.selectExpr("ST_AsText(ST_Centroid(geometry))").first()[0])
    except Exception as e:
        print("Meshblock error:", e)
        
    try:
        demo = spark.table("org_catalog.fgsdb.abs_demographics")
        print("Demographics sample point:", demo.selectExpr("ST_AsText(ST_Centroid(geometry))").first()[0])
        print("Demographics distinct years:")
        demo.select("year").distinct().show()
    except Exception as e:
        print("Demographics error:", e)

if __name__ == "__main__":
    main()
