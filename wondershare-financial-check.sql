WITH reviewed(category,period,revenue_cny,cost_cny) AS (
VALUES ('文档创意','2025上半年',55779138.18,3267253.70),
('文档创意','2026上半年',46337312.04,5328645.48),
('绘图创意','2025上半年',44205049.09,2511764.35),
('绘图创意','2026上半年',34045921.58,1814700.40)
)
SELECT category,period,revenue_cny,cost_cny,revenue_cny/10000.0 AS revenue_wan FROM reviewed;
