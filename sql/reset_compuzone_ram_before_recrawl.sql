-- 컴퓨존 RAM만 깨끗하게 재수집하기 위한 데이터 정리
-- 다나와 RAM은 유지한다.
-- 현재 DB 검증에서 RAM의 컴퓨존/다나와 공통 PRODUCT가 0건임을 확인한 뒤 실행하는 용도다.
-- DB 스키마는 변경하지 않는다.

BEGIN;

CREATE TEMP TABLE tmp_compuzone_ram_products
ON COMMIT DROP
AS
SELECT DISTINCT p.product_id
FROM product p
JOIN category c
    ON c.category_id = p.category_id
JOIN product_offer po
    ON po.product_id = p.product_id
JOIN seller s
    ON s.seller_id = po.seller_id
WHERE c.category_code = 'RAM'
  AND s.seller_name = '컴퓨존'
  AND NOT EXISTS (
      SELECT 1
      FROM product_offer po2
      JOIN seller s2
          ON s2.seller_id = po2.seller_id
      WHERE po2.product_id = p.product_id
        AND s2.seller_name <> '컴퓨존'
  );

DELETE FROM price_history ph
USING product_offer po,
      tmp_compuzone_ram_products t
WHERE ph.offer_id = po.offer_id
  AND po.product_id = t.product_id;

DELETE FROM product_offer po
USING tmp_compuzone_ram_products t
WHERE po.product_id = t.product_id;

DELETE FROM ram_spec rs
USING tmp_compuzone_ram_products t
WHERE rs.product_id = t.product_id;

DELETE FROM product p
USING tmp_compuzone_ram_products t
WHERE p.product_id = t.product_id;

COMMIT;

SELECT
    c.category_code,
    COUNT(*) AS product_count
FROM product p
JOIN category c
    ON c.category_id = p.category_id
WHERE c.category_code = 'RAM'
GROUP BY c.category_code;
