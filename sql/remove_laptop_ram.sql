-- 데스크톱 메모리 서비스에서 제외할 노트북용 RAM 데이터 정리
-- DB 스키마는 변경하지 않는다.
-- PRODUCT 이름에 노트북용 / SO-DIMM / SODIMM이 포함된 RAM만 삭제한다.

BEGIN;

DELETE FROM price_history ph
USING product_offer po, product p, category c
WHERE ph.offer_id = po.offer_id
  AND po.product_id = p.product_id
  AND p.category_id = c.category_id
  AND c.category_code = 'RAM'
  AND (
      p.product_name ILIKE '%노트북용%'
      OR p.product_name ILIKE '%SO-DIMM%'
      OR p.product_name ILIKE '%SODIMM%'
  );

DELETE FROM product_offer po
USING product p, category c
WHERE po.product_id = p.product_id
  AND p.category_id = c.category_id
  AND c.category_code = 'RAM'
  AND (
      p.product_name ILIKE '%노트북용%'
      OR p.product_name ILIKE '%SO-DIMM%'
      OR p.product_name ILIKE '%SODIMM%'
  );

DELETE FROM ram_spec rs
USING product p, category c
WHERE rs.product_id = p.product_id
  AND p.category_id = c.category_id
  AND c.category_code = 'RAM'
  AND (
      p.product_name ILIKE '%노트북용%'
      OR p.product_name ILIKE '%SO-DIMM%'
      OR p.product_name ILIKE '%SODIMM%'
  );

DELETE FROM product p
USING category c
WHERE p.category_id = c.category_id
  AND c.category_code = 'RAM'
  AND (
      p.product_name ILIKE '%노트북용%'
      OR p.product_name ILIKE '%SO-DIMM%'
      OR p.product_name ILIKE '%SODIMM%'
  );

COMMIT;

SELECT
    p.product_id,
    p.product_name,
    rs.capacity_gb,
    rs.memory_type,
    rs.module_count
FROM product p
JOIN category c
    ON c.category_id = p.category_id
LEFT JOIN ram_spec rs
    ON rs.product_id = p.product_id
WHERE c.category_code = 'RAM'
ORDER BY p.product_id;
