from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "private"
    / "vgi_marica_export_2026-10-05.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "sample"
    / "vgi_reports_anonymized.csv"
)


def main():
    df = pd.read_csv(
    INPUT_FILE,
    sep=";",
    encoding="utf-8-sig"
)

    # --------------------------------------------------
    # 1. Keep only approved records, when available
    # --------------------------------------------------
    if "aprovado" in df.columns:
        approved = (
            df["aprovado"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "sim", "yes"])
        )
        df = df.loc[approved].copy()

    # --------------------------------------------------
    # 2. Remove identifying / unnecessary information
    # --------------------------------------------------
    columns_to_remove = [
        "id",
        "descricao",
        "link_foto",
        "data_registo",
        "horario_envio",
        "timestamp_completo",
        "evento_id",
        "reanalisado",
        "reanalise_tentativas",
        "reanalise_ultima_tentativa",
        "lat",
        "lon",
        "latitude",
        "longitude",
        "geom",
        "geometry",
        "aprovado",
    ]

    existing_columns = [
        col for col in columns_to_remove if col in df.columns
    ]

    df = df.drop(columns=existing_columns)

    # --------------------------------------------------
    # 3. Rename useful variables
    # --------------------------------------------------
    rename_map = {
        "bairro": "neighborhood",
        "impacto": "impact_type",
        "data_ocorrencia": "occurrence_date",
        "api_hs": "hs_m",
        "api_tp": "tp_s",
        "api_direcao": "wave_direction_deg",
        "vento_vel_kmh": "wind_speed_kmh",
        "vento_dir_graus": "wind_direction_deg",
        "mare_m": "tide_m",
        "ciclone_alerta": "cyclone_alert",
        "energia_onda_kw": "wave_energy_kw",
    }

    df = df.rename(
        columns={
            old: new
            for old, new in rename_map.items()
            if old in df.columns
        }
    )

    # --------------------------------------------------
    # 4. Reduce temporal precision
    # --------------------------------------------------
    if "occurrence_date" in df.columns:
        df["occurrence_date"] = pd.to_datetime(
            df["occurrence_date"],
            errors="coerce"
        )

        df["occurrence_month"] = (
            df["occurrence_date"]
            .dt.to_period("M")
            .astype(str)
        )

        df = df.drop(columns=["occurrence_date"])

    # --------------------------------------------------
    # 5. Create new anonymous IDs
    # --------------------------------------------------
    df = df.reset_index(drop=True)

    df.insert(
        0,
        "report_id",
        [f"R{i:03d}" for i in range(1, len(df) + 1)]
    )

    # --------------------------------------------------
    # 6. Keep only portfolio variables
    # --------------------------------------------------
    preferred_columns = [
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

    final_columns = [
        col for col in preferred_columns if col in df.columns
    ]

    df = df[final_columns]

    # --------------------------------------------------
    # 7. Export public version
    # --------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
    )

    print(f"Anonymous records: {len(df)}")
    print(f"Output: {OUTPUT_FILE}")
    print("\nColumns:")
    for column in df.columns:
        print(f"- {column}")


if __name__ == "__main__":
    main()