from pathlib import Path
import os
import sys

import geopandas as gpd
from geoalchemy2 import Geometry
from shapely.geometry import MultiPolygon
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ============================================================
# Project paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "spatial"
    / "orla_marica.geojson"
)


# ============================================================
# Database configuration
# ============================================================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "environmental_gis")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

SCHEMA = "coastal"
TABLE = "neighborhoods"

EXPECTED_CRS = "EPSG:31983"
EXPECTED_FEATURES = 12


# ============================================================
# Database engine
# ============================================================

def create_database_engine():
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    )

    return create_engine(url)


# ============================================================
# Read and validate spatial data
# ============================================================

def load_geojson():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Spatial file not found: {INPUT_FILE}"
        )

    print(f"Reading: {INPUT_FILE}")

    gdf = gpd.read_file(INPUT_FILE)

    print(f"Features found: {len(gdf)}")
    print(f"Source CRS: {gdf.crs}")

    if len(gdf) != EXPECTED_FEATURES:
        raise ValueError(
            f"Expected {EXPECTED_FEATURES} features, "
            f"but found {len(gdf)}."
        )

    if gdf.crs is None:
        raise ValueError("The GeoJSON has no CRS information.")

    if gdf.crs.to_epsg() != 31983:
        print(
            f"Reprojecting from {gdf.crs} "
            f"to {EXPECTED_CRS}..."
        )

        gdf = gdf.to_crs(EXPECTED_CRS)

    if gdf.geometry.isna().any():
        raise ValueError(
            "The dataset contains null geometries."
        )

    invalid_count = (~gdf.geometry.is_valid).sum()

    if invalid_count > 0:
        raise ValueError(
            f"The dataset contains {invalid_count} "
            "invalid geometries."
        )

    return gdf


# ============================================================
# Prepare attributes
# ============================================================

def prepare_data(gdf):
    required_columns = [
        "bairro",
        "distrito",
        "cod_bairro",
        "cd_distrit",
        "geometry",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in gdf.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    gdf = gdf[required_columns].copy()

    # Rename geometry column to the name used in PostGIS.
    gdf = gdf.rename_geometry("geom")

    # Guarantee MultiPolygon geometry.
    gdf["geom"] = gdf["geom"].apply(
    lambda geom:
        geom
        if geom.geom_type == "MultiPolygon"
        else MultiPolygon([geom])
)

    # Rebuild as GeoDataFrame after geometry processing.
    gdf = gpd.GeoDataFrame(
        gdf,
        geometry="geom",
        crs=EXPECTED_CRS,
    )

    print("\nColumns prepared:")
    for column in gdf.columns:
        print(f"- {column}")

    print(
        "\nGeometry types:",
        sorted(gdf.geom_type.unique())
    )

    return gdf


# ============================================================
# Prepare database table
# ============================================================

def prepare_database(engine):
    sql = f"""
    CREATE EXTENSION IF NOT EXISTS postgis;

    CREATE SCHEMA IF NOT EXISTS {SCHEMA};

    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
        id SERIAL PRIMARY KEY,
        bairro VARCHAR,
        distrito VARCHAR,
        cod_bairro DOUBLE PRECISION,
        cd_distrit VARCHAR,
        geom geometry(MultiPolygon, 31983)
    );

    TRUNCATE TABLE
        {SCHEMA}.neighborhood_groups,
        {SCHEMA}.{TABLE}
    RESTART IDENTITY;
    """

    with engine.begin() as connection:
        connection.execute(text(sql))


# ============================================================
# Import GeoJSON into PostGIS
# ============================================================

def import_to_postgis(gdf, engine):
    print(
        f"\nImporting spatial data into "
        f"{SCHEMA}.{TABLE}..."
    )

    gdf.to_postgis(
        name=TABLE,
        con=engine,
        schema=SCHEMA,
        if_exists="append",
        index=False,
        dtype={
            "geom": Geometry(
                geometry_type="MULTIPOLYGON",
                srid=31983,
            )
        },
    )


# ============================================================
# Spatial index
# ============================================================

def create_spatial_index(engine):
    sql = f"""
    CREATE INDEX IF NOT EXISTS idx_neighborhoods_geom
    ON {SCHEMA}.{TABLE}
    USING GIST (geom);
    """

    with engine.begin() as connection:
        connection.execute(text(sql))


# ============================================================
# Validate database import
# ============================================================

def validate_import(engine):
    sql = f"""
    SELECT
        COUNT(*) AS feature_count,
        COUNT(*) FILTER (
            WHERE geom IS NULL
        ) AS null_geometries,
        COUNT(*) FILTER (
            WHERE NOT ST_IsValid(geom)
        ) AS invalid_geometries,
        COUNT(DISTINCT ST_SRID(geom)) AS srid_count,
        MIN(ST_SRID(geom)) AS srid
    FROM {SCHEMA}.{TABLE};
    """

    with engine.connect() as connection:
        result = connection.execute(
            text(sql)
        ).mappings().one()

    feature_count = result["feature_count"]

    print("\nImport validation")
    print("-----------------")
    print(f"Features: {feature_count}")
    print(
        f"Null geometries: "
        f"{result['null_geometries']}"
    )
    print(
        f"Invalid geometries: "
        f"{result['invalid_geometries']}"
    )
    print(f"SRID: {result['srid']}")

    if feature_count != EXPECTED_FEATURES:
        raise ValueError(
            f"Expected {EXPECTED_FEATURES} features "
            f"in PostGIS, but found {feature_count}."
        )

    if result["null_geometries"] != 0:
        raise ValueError(
            "Null geometries found after import."
        )

    if result["invalid_geometries"] != 0:
        raise ValueError(
            "Invalid geometries found after import."
        )

    if result["srid_count"] != 1:
        raise ValueError(
            "Multiple SRIDs found after import."
        )

    if result["srid"] != 31983:
        raise ValueError(
            f"Unexpected SRID: {result['srid']}"
        )


# ============================================================
# Main
# ============================================================

def main():
    print(
        "Environmental Geospatial Data Platform — Maricá"
    )
    print("Spatial data loader")
    print("=" * 50)

    try:
        gdf = load_geojson()

        gdf = prepare_data(gdf)

        engine = create_database_engine()

        prepare_database(engine)

        import_to_postgis(
            gdf,
            engine,
        )

        create_spatial_index(engine)

        validate_import(engine)

        print(
            "\nSpatial data import completed successfully."
        )

    except Exception as error:
        print(
            f"\nERROR: {error}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()