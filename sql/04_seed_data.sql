-- =====================================================
-- Seed data: neighborhood groups
-- =====================================================

INSERT INTO coastal.neighborhood_groups (
    neighborhood_id,
    report_area
)
SELECT
    id,
    'Itaipuaçu'
FROM coastal.neighborhoods
WHERE bairro IN (
    'BARROCO',
    'JARDIM ATLÂNTICO CENTRAL',
    'JARDIM ATLÂNTICO LESTE',
    'JARDIM ATLÂNTICO OESTE',
    'PRAIA DE ITAIPUAÇU',
    'RECANTO DE ITAIPUAÇU'
)
ON CONFLICT DO NOTHING;


INSERT INTO coastal.neighborhood_groups (
    neighborhood_id,
    report_area
)
SELECT
    id,
    'Cordeirinho'
FROM coastal.neighborhoods
WHERE bairro = 'CORDEIRINHO'
ON CONFLICT DO NOTHING;


INSERT INTO coastal.neighborhood_groups (
    neighborhood_id,
    report_area
)
SELECT
    id,
    'Guaratiba'
FROM coastal.neighborhoods
WHERE bairro = 'GUARATIBA'
ON CONFLICT DO NOTHING;


INSERT INTO coastal.neighborhood_groups (
    neighborhood_id,
    report_area
)
SELECT
    id,
    'Ponta Negra'
FROM coastal.neighborhoods
WHERE bairro = 'PONTA NEGRA'
ON CONFLICT DO NOTHING;