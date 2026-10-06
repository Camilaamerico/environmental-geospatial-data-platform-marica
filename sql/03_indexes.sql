CREATE INDEX IF NOT EXISTS idx_neighborhoods_geom
ON coastal.neighborhoods
USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_reports_neighborhood
ON coastal.reports (neighborhood);

CREATE INDEX IF NOT EXISTS idx_reports_impact_type
ON coastal.reports (impact_type);

CREATE INDEX IF NOT EXISTS idx_reports_occurrence_month
ON coastal.reports (occurrence_month);