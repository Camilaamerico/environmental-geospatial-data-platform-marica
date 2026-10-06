CREATE OR REPLACE VIEW coastal.v_reports_by_neighborhood AS
SELECT
    neighborhood,
    COUNT(*) AS total_reports
FROM coastal.reports
GROUP BY neighborhood;


CREATE OR REPLACE VIEW coastal.v_reports_by_impact AS
SELECT
    impact_type,
    COUNT(*) AS total_reports
FROM coastal.reports
GROUP BY impact_type;


CREATE OR REPLACE VIEW coastal.v_impact_environment_summary AS
SELECT
    r.impact_type,
    COUNT(*) AS total_reports,
    ROUND(AVG(e.hs_m), 2) AS avg_hs_m,
    ROUND(MAX(e.hs_m), 2) AS max_hs_m,
    ROUND(AVG(e.tp_s), 2) AS avg_tp_s,
    ROUND(AVG(e.wave_energy_kw), 2) AS avg_wave_energy_kw
FROM coastal.reports r
JOIN coastal.environmental_conditions e
    ON r.report_id = e.report_id
GROUP BY r.impact_type;


CREATE OR REPLACE VIEW coastal.v_report_areas AS
SELECT
    ng.report_area,
    ST_Multi(
        ST_Union(n.geom)
    )::geometry(MultiPolygon, 31983) AS geom
FROM coastal.neighborhood_groups ng
JOIN coastal.neighborhoods n
    ON n.id = ng.neighborhood_id
GROUP BY ng.report_area;


CREATE OR REPLACE VIEW coastal.v_area_environment_summary AS
SELECT
    a.report_area,
    COUNT(r.report_id) AS total_reports,
    ROUND(AVG(e.hs_m), 2) AS avg_hs_m,
    ROUND(MAX(e.hs_m), 2) AS max_hs_m,
    ROUND(AVG(e.tp_s), 2) AS avg_tp_s,
    ROUND(AVG(e.wind_speed_kmh), 2) AS avg_wind_speed_kmh,
    ROUND(AVG(e.tide_m), 2) AS avg_tide_m,
    ROUND(AVG(e.wave_energy_kw), 2) AS avg_wave_energy_kw,
    a.geom
FROM coastal.v_report_areas a
LEFT JOIN coastal.reports r
    ON r.neighborhood = a.report_area
LEFT JOIN coastal.environmental_conditions e
    ON e.report_id = r.report_id
GROUP BY
    a.report_area,
    a.geom;


CREATE OR REPLACE VIEW coastal.v_dominant_impact_by_area AS
WITH impact_counts AS (
    SELECT
        neighborhood AS report_area,
        impact_type,
        COUNT(*) AS impact_count
    FROM coastal.reports
    GROUP BY neighborhood, impact_type
),
max_counts AS (
    SELECT
        report_area,
        MAX(impact_count) AS max_count
    FROM impact_counts
    GROUP BY report_area
)
SELECT
    a.report_area,

    STRING_AGG(
        ic.impact_type,
        ' / '
        ORDER BY ic.impact_type
    ) AS dominant_impact,

    mc.max_count AS impact_count,

    a.geom,

    COUNT(*) AS tied_categories

FROM coastal.v_report_areas a

JOIN max_counts mc
    ON a.report_area = mc.report_area

JOIN impact_counts ic
    ON ic.report_area = mc.report_area
   AND ic.impact_count = mc.max_count

GROUP BY
    a.report_area,
    mc.max_count,
    a.geom;

CREATE OR REPLACE VIEW coastal.v_dashboard_kpis AS
    SELECT
    COUNT(DISTINCT r.report_id) AS total_reports,
    COUNT(DISTINCT r.neighborhood) AS total_reporting_areas,
    ROUND(AVG(e.hs_m), 2) AS avg_hs_m,
    ROUND(AVG(e.wave_energy_kw), 2) AS avg_wave_energy_kw
FROM coastal.reports r
JOIN coastal.environmental_conditions e
    ON e.report_id = r.report_id;

CREATE OR REPLACE VIEW coastal.v_dashboard_reports AS
SELECT
    report_id,
    occurrence_month,

    neighborhood AS reporting_area,

    CASE impact_type
        WHEN 'Ondas Violentas na Areia (Sem Danos Severos)'
            THEN 'Violent waves'
        WHEN 'Água no Calçadão/Pista'
            THEN 'Water on promenade/road'
        WHEN 'Danos a Estruturas Físicas'
            THEN 'Structural damage'
        WHEN 'Erosão Severa'
            THEN 'Severe erosion'
        ELSE impact_type
    END AS impact_type_en,

    CASE EXTRACT(MONTH FROM occurrence_month)
        WHEN 1 THEN 'January'
        WHEN 2 THEN 'February'
        WHEN 3 THEN 'March'
        WHEN 4 THEN 'April'
        WHEN 5 THEN 'May'
        WHEN 6 THEN 'June'
        WHEN 7 THEN 'July'
        WHEN 8 THEN 'August'
        WHEN 9 THEN 'September'
        WHEN 10 THEN 'October'
        WHEN 11 THEN 'November'
        WHEN 12 THEN 'December'
    END
    || ' ' ||
    EXTRACT(YEAR FROM occurrence_month)::int
    AS occurrence_month_en

FROM coastal.reports;