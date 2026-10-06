-- =====================================================
-- Reports by reporting area
-- =====================================================

SELECT
    neighborhood,
    COUNT(*) AS total_reports
FROM coastal.reports
GROUP BY neighborhood
ORDER BY total_reports DESC;


-- =====================================================
-- Reports by impact type
-- =====================================================

SELECT
    impact_type,
    COUNT(*) AS total_reports
FROM coastal.reports
GROUP BY impact_type
ORDER BY total_reports DESC;


-- =====================================================
-- Environmental conditions by impact type
-- =====================================================

SELECT
    r.impact_type,
    ROUND(AVG(e.hs_m), 2) AS avg_hs_m,
    ROUND(MAX(e.hs_m), 2) AS max_hs_m,
    ROUND(AVG(e.tp_s), 2) AS avg_tp_s,
    ROUND(AVG(e.wave_energy_kw), 2) AS avg_wave_energy_kw,
    COUNT(*) AS total_reports
FROM coastal.reports r
JOIN coastal.environmental_conditions e
    ON r.report_id = e.report_id
GROUP BY r.impact_type
ORDER BY avg_hs_m DESC;


-- =====================================================
-- Environmental summary by reporting area
-- =====================================================

SELECT
    report_area,
    total_reports,
    avg_hs_m,
    max_hs_m,
    avg_tp_s,
    avg_wave_energy_kw
FROM coastal.v_area_environment_summary
ORDER BY total_reports DESC;


-- =====================================================
-- Dominant impact by reporting area
-- =====================================================

SELECT
    report_area,
    dominant_impact,
    impact_count,
    tied_categories
FROM coastal.v_dominant_impact_by_area
ORDER BY report_area;


-- =====================================================
-- Spatial validation
-- =====================================================

SELECT
    report_area,
    ST_GeometryType(geom) AS geometry_type,
    ST_SRID(geom) AS srid,
    ROUND(
        (ST_Area(geom) / 1000000.0)::numeric,
        2
    ) AS area_km2
FROM coastal.v_report_areas
ORDER BY report_area;