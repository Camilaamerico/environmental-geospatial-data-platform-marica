CREATE TABLE IF NOT EXISTS coastal.reports (
    report_id TEXT PRIMARY KEY,
    occurrence_month DATE NOT NULL,
    neighborhood TEXT NOT NULL,
    impact_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coastal.environmental_conditions (
    report_id TEXT PRIMARY KEY
        REFERENCES coastal.reports(report_id)
        ON DELETE CASCADE,

    hs_m NUMERIC,
    tp_s NUMERIC,
    wave_direction_deg INTEGER,
    wind_speed_kmh NUMERIC,
    wind_direction_deg INTEGER,
    tide_m NUMERIC,
    cyclone_alert BOOLEAN,
    wave_energy_kw NUMERIC
);

CREATE TABLE IF NOT EXISTS coastal.neighborhoods (
    id SERIAL PRIMARY KEY,
    bairro VARCHAR,
    distrito VARCHAR,
    cod_bairro DOUBLE PRECISION,
    cd_distrit VARCHAR,
    geom geometry(MultiPolygon, 31983)
);

CREATE TABLE IF NOT EXISTS coastal.neighborhood_groups (
    neighborhood_id INTEGER NOT NULL
        REFERENCES coastal.neighborhoods(id)
        ON DELETE CASCADE,

    report_area TEXT NOT NULL,

    PRIMARY KEY (
        neighborhood_id,
        report_area
    )
);