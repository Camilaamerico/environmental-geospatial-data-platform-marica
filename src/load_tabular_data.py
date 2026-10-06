from pathlib import Path
import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "sample"
    / "vgi_reports_anonymized.csv"
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "environmental_gis")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

EXPECTED_RECORDS = 25


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


def load_csv():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig"
    )

    print(f"Reading: {INPUT_FILE}")
    print(f"Records found: {len(df)}")

    if len(df) != EXPECTED_RECORDS:
        raise ValueError(
            f"Expected {EXPECTED_RECORDS} records, "
            f"but found {len(df)}."
        )

    required_columns = [
        "report_id",
        "occurrence_month",
        "neighborhood",
        "impact_type",
        "hs_m",
        "tp_s",
        "wave_direction_deg",
        "wind_speed_kmh",
        "wind_direction_deg",
        "tide_m",
        "cyclone_alert",
        "wave_energy_kw",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    return df


def prepare_data(df):
    df = df.copy()

    df["occurrence_month"] = pd.to_datetime(
        df["occurrence_month"],
        format="%Y-%m",
        errors="raise",
    )

    if df["report_id"].duplicated().any():
        duplicates = (
            df.loc[
                df["report_id"].duplicated(),
                "report_id"
            ]
            .tolist()
        )

        raise ValueError(
            f"Duplicate report IDs found: {duplicates}"
        )

    allowed_areas = {
        "Itaipuaçu",
        "Cordeirinho",
        "Guaratiba",
        "Ponta Negra",
    }

    invalid_areas = set(
        df["neighborhood"].dropna().unique()
    ) - allowed_areas

    if invalid_areas:
        raise ValueError(
            "Unexpected reporting areas: "
            + ", ".join(sorted(invalid_areas))
        )

    return df


def clear_existing_data(engine):
    sql = """
    TRUNCATE TABLE
        coastal.environmental_conditions,
        coastal.reports
    CASCADE;
    """

    with engine.begin() as connection:
        connection.execute(text(sql))


def load_reports(df, engine):
    reports = df[
        [
            "report_id",
            "occurrence_month",
            "neighborhood",
            "impact_type",
        ]
    ].copy()

    reports.to_sql(
        name="reports",
        con=engine,
        schema="coastal",
        if_exists="append",
        index=False,
        method="multi",
    )


def load_environmental_conditions(df, engine):
    environmental = df[
        [
            "report_id",
            "hs_m",
            "tp_s",
            "wave_direction_deg",
            "wind_speed_kmh",
            "wind_direction_deg",
            "tide_m",
            "cyclone_alert",
            "wave_energy_kw",
        ]
    ].copy()

    environmental.to_sql(
        name="environmental_conditions",
        con=engine,
        schema="coastal",
        if_exists="append",
        index=False,
        method="multi",
    )


def validate_import(engine):
    sql = """
    SELECT
        (SELECT COUNT(*)
         FROM coastal.reports) AS report_count,

        (SELECT COUNT(*)
         FROM coastal.environmental_conditions)
            AS environmental_count,

        (
            SELECT COUNT(*)
            FROM coastal.reports r
            LEFT JOIN coastal.environmental_conditions e
                ON r.report_id = e.report_id
            WHERE e.report_id IS NULL
        ) AS unmatched_reports;
    """

    with engine.connect() as connection:
        result = (
            connection.execute(text(sql))
            .mappings()
            .one()
        )

    print("\nImport validation")
    print("-----------------")
    print(
        f"Reports: {result['report_count']}"
    )
    print(
        "Environmental conditions: "
        f"{result['environmental_count']}"
    )
    print(
        f"Unmatched reports: "
        f"{result['unmatched_reports']}"
    )

    if result["report_count"] != EXPECTED_RECORDS:
        raise ValueError(
            "Unexpected number of records in reports."
        )

    if result["environmental_count"] != EXPECTED_RECORDS:
        raise ValueError(
            "Unexpected number of records in "
            "environmental_conditions."
        )

    if result["unmatched_reports"] != 0:
        raise ValueError(
            "Some reports have no environmental conditions."
        )


def main():
    print(
        "Environmental Geospatial Data Platform — Maricá"
    )
    print("Tabular data loader")
    print("=" * 50)

    try:
        df = load_csv()
        df = prepare_data(df)

        engine = create_database_engine()

        clear_existing_data(engine)

        print("\nLoading coastal.reports...")
        load_reports(df, engine)

        print(
            "Loading coastal.environmental_conditions..."
        )
        load_environmental_conditions(
            df,
            engine,
        )

        validate_import(engine)

        print(
            "\nTabular data import completed successfully."
        )

    except Exception as error:
        print(
            f"\nERROR: {error}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()