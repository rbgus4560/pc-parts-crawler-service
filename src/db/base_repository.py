"""여러 사이트 Repository가 공통으로 사용하는 기본 DB 저장 기능."""

import re


class BaseRepository:
    """여러 Repository에서 공통으로 사용하는 DB 저장 기능."""

    @staticmethod
    # ======================================================
    # 기준정보: CATEGORY / BRAND / SELLER / RETAILER
    # ======================================================
    def get_or_create_category(cur, category_code: str) -> int:
        cur.execute(
            """
            INSERT INTO category (category_code, category_name)
            VALUES (%s, %s)
            ON CONFLICT (category_code)
            DO UPDATE SET category_name = EXCLUDED.category_name
            RETURNING category_id;
            """,
            (category_code, category_code),
        )
        return cur.fetchone()[0]

    @staticmethod
    def get_or_create_brand(cur, brand_name: str) -> int:
        if not brand_name:
            raise ValueError("brand 정보가 없습니다.")

        cur.execute(
            """
            INSERT INTO brand (brand_name)
            VALUES (%s)
            ON CONFLICT (brand_name)
            DO UPDATE SET brand_name = EXCLUDED.brand_name
            RETURNING brand_id;
            """,
            (brand_name,),
        )
        return cur.fetchone()[0]

    @staticmethod
    def get_or_create_seller(
        cur,
        seller_name: str,
        site_url: str,
        crawl_type: str,
    ) -> int:
        cur.execute(
            """
            INSERT INTO seller (seller_name, site_url, crawl_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (seller_name)
            DO UPDATE SET
                site_url = EXCLUDED.site_url,
                crawl_type = EXCLUDED.crawl_type,
                is_active = TRUE
            RETURNING seller_id;
            """,
            (seller_name, site_url, crawl_type),
        )
        return cur.fetchone()[0]

    @staticmethod
    def get_or_create_retailer(
        cur,
        retailer_name: str,
        retailer_url: str = None,
    ) -> int:
        if not retailer_name:
            raise ValueError("retailer 정보가 없습니다.")

        cur.execute(
            """
            INSERT INTO retailer (retailer_name, retailer_url)
            VALUES (%s, %s)
            ON CONFLICT (retailer_name)
            DO UPDATE SET
                retailer_url = COALESCE(EXCLUDED.retailer_url, retailer.retailer_url),
                is_active = TRUE
            RETURNING retailer_id;
            """,
            (retailer_name, retailer_url),
        )
        return cur.fetchone()[0]

    @staticmethod
    # ======================================================
    # 기준 상품 PRODUCT
    # ======================================================
    def upsert_product(
        cur,
        category_id: int,
        brand_id: int,
        product_name: str,
        model_name: str,
        normalized_name: str,
        image_url: str = None,
    ) -> int:
        cur.execute(
            """
            INSERT INTO product (
                category_id,
                brand_id,
                product_name,
                model_name,
                normalized_name,
                image_url
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (category_id, brand_id, normalized_name)
            DO UPDATE SET
                product_name = EXCLUDED.product_name,
                model_name = EXCLUDED.model_name,
                image_url = COALESCE(EXCLUDED.image_url, product.image_url),
                updated_at = NOW()
            RETURNING product_id;
            """,
            (
                category_id,
                brand_id,
                product_name,
                model_name,
                normalized_name,
                image_url,
            ),
        )
        return cur.fetchone()[0]

    @staticmethod
    def fill_product_image(cur, product_id: int, image_url: str = None) -> None:
        cur.execute(
            """
            UPDATE product
            SET
                image_url = COALESCE(image_url, %s),
                updated_at = NOW()
            WHERE product_id = %s;
            """,
            (image_url, product_id),
        )

    @staticmethod
    # ======================================================
    # 쇼핑몰 판매정보 PRODUCT_OFFER
    # ======================================================
    def save_offer(
        cur,
        product_id: int,
        seller_id: int,
        retailer_id: int,
        source_product_id: str,
        raw_product_name: str,
        product_url: str,
    ) -> int:
        cur.execute(
            """
            INSERT INTO product_offer (
                product_id,
                seller_id,
                retailer_id,
                source_product_id,
                raw_product_name,
                product_url
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (seller_id, retailer_id, source_product_id)
            DO UPDATE SET
                product_id = EXCLUDED.product_id,
                raw_product_name = EXCLUDED.raw_product_name,
                product_url = EXCLUDED.product_url,
                last_seen_at = NOW(),
                is_active = TRUE
            RETURNING offer_id;
            """,
            (
                product_id,
                seller_id,
                retailer_id,
                source_product_id,
                raw_product_name,
                product_url,
            ),
        )
        return cur.fetchone()[0]

    @staticmethod
    # ======================================================
    # 가격 이력 PRICE_HISTORY
    # ======================================================
    def save_price(cur, offer_id: int, price: int) -> None:
        cur.execute(
            """
            INSERT INTO price_history (offer_id, price)
            VALUES (%s, %s);
            """,
            (offer_id, price),
        )

    @staticmethod
    def deactivate_existing_offers(cur, product_id: int, seller_id: int) -> None:
        cur.execute(
            """
            UPDATE product_offer
            SET is_active = FALSE
            WHERE product_id = %s
              AND seller_id = %s;
            """,
            (product_id, seller_id),
        )

    @staticmethod
    def strip_leading_brand(product_name: str, brand: str) -> str:
        """상품명 맨 앞의 `[브랜드]` 또는 일반 브랜드 표기를 제거한다."""
        if not product_name:
            return ""

        name = product_name.strip()
        if not brand:
            return name

        escaped = re.escape(brand)
        name = re.sub(
            rf"^\[\s*{escaped}\s*\]\s*",
            "",
            name,
            count=1,
            flags=re.IGNORECASE,
        )
        name = re.sub(
            rf"^{escaped}\s+",
            "",
            name,
            count=1,
            flags=re.IGNORECASE,
        )
        return name.strip()
