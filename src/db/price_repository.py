"""가격 이력/통계 조회 Repository."""

from src.db.connection import get_connection


class PriceRepository:
    """상품 가격 이력과 통계를 조회한다."""

    # 현재 활성 판매처 기준 최저가
    def get_current_min_price(self, product_id: int):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH latest_offer_price AS (
                        SELECT DISTINCT ON (po.offer_id)
                            po.offer_id,
                            s.seller_name,
                            r.retailer_name,
                            ph.price,
                            ph.collected_at
                        FROM product_offer po
                        JOIN seller s ON po.seller_id = s.seller_id
                        JOIN retailer r ON po.retailer_id = r.retailer_id
                        JOIN price_history ph ON po.offer_id = ph.offer_id
                        WHERE po.product_id = %s
                          AND po.is_active = TRUE
                        ORDER BY po.offer_id, ph.collected_at DESC
                    )
                    SELECT offer_id, seller_name, retailer_name, price, collected_at
                    FROM latest_offer_price
                    ORDER BY price ASC, collected_at DESC
                    LIMIT 1;
                    """,
                    (product_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                return {
                    "offer_id": row[0],
                    "seller_name": row[1],
                    "retailer_name": row[2],
                    "price": row[3],
                    "collected_at": row[4],
                }
        finally:
            conn.close()

    # 최근 N일 / 평균 / 최고 최저가 통계
    def get_price_statistics(self, product_id: int, recent_days: int = 7):
        if recent_days <= 0:
            raise ValueError("recent_days는 1 이상이어야 합니다.")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH daily_min_price AS (
                        SELECT
                            ph.collected_at::date AS price_date,
                            MIN(ph.price) AS min_price
                        FROM product_offer po
                        JOIN price_history ph ON po.offer_id = ph.offer_id
                        WHERE po.product_id = %s
                        GROUP BY ph.collected_at::date
                    ),
                    current_prices AS (
                        SELECT DISTINCT ON (po.offer_id)
                            po.offer_id,
                            ph.price
                        FROM product_offer po
                        JOIN price_history ph ON po.offer_id = ph.offer_id
                        WHERE po.product_id = %s
                          AND po.is_active = TRUE
                        ORDER BY po.offer_id, ph.collected_at DESC
                    )
                    SELECT
                        (SELECT MIN(price) FROM current_prices),
                        (
                            SELECT MIN(min_price)
                            FROM daily_min_price
                            WHERE price_date >= CURRENT_DATE - %s
                        ),
                        ROUND((SELECT AVG(min_price) FROM daily_min_price)),
                        (SELECT MAX(min_price) FROM daily_min_price),
                        (SELECT MIN(price_date) FROM daily_min_price),
                        (SELECT MAX(price_date) FROM daily_min_price),
                        (SELECT COUNT(*) FROM daily_min_price);
                    """,
                    (product_id, product_id, recent_days - 1),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                return {
                    "current_min_price": self._to_int(row[0]),
                    "recent_min_price": self._to_int(row[1]),
                    "average_min_price": self._to_int(row[2]),
                    "highest_min_price": self._to_int(row[3]),
                    "first_price_date": self._to_iso(row[4]),
                    "last_price_date": self._to_iso(row[5]),
                    "price_day_count": int(row[6]),
                }
        finally:
            conn.close()

    # 가격 그래프용 날짜별 최저가
    def get_daily_min_prices(self, product_id: int):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        ph.collected_at::date AS price_date,
                        MIN(ph.price) AS min_price
                    FROM product_offer po
                    JOIN price_history ph ON po.offer_id = ph.offer_id
                    WHERE po.product_id = %s
                    GROUP BY ph.collected_at::date
                    ORDER BY price_date ASC;
                    """,
                    (product_id,),
                )
                return [
                    {"price_date": row[0].isoformat(), "min_price": int(row[1])}
                    for row in cur.fetchall()
                ]
        finally:
            conn.close()

    @staticmethod
    def _to_int(value):
        return int(value) if value is not None else None

    @staticmethod
    def _to_iso(value):
        return value.isoformat() if value is not None else None
