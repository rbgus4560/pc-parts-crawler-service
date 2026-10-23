"""크롤링 실행 상태를 CRAWL_LOG에 기록하는 Repository."""

from src.db.base_repository import BaseRepository
from src.db.connection import get_connection


class CrawlLogRepository(BaseRepository):
    DEFAULT_SELLER_CONFIG = {
        "컴퓨존": ("https://www.compuzone.co.kr", "STATIC"),
        "다나와": ("https://www.danawa.com", "DYNAMIC"),
    }

    # 크롤링 시작: RUNNING 기록
    def start_log(
        self,
        seller_name: str,
        category_code: str,
        site_url: str = None,
        crawl_type: str = None,
    ) -> int:
        if site_url is None or crawl_type is None:
            try:
                site_url, crawl_type = self.DEFAULT_SELLER_CONFIG[seller_name]
            except KeyError as exc:
                raise ValueError(
                    "알 수 없는 seller입니다. site_url과 crawl_type을 지정해주세요."
                ) from exc

        if crawl_type not in {"STATIC", "DYNAMIC"}:
            raise ValueError("crawl_type은 STATIC 또는 DYNAMIC이어야 합니다.")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                seller_id = self.get_or_create_seller(
                    cur, seller_name, site_url, crawl_type
                )
                category_id = self.get_or_create_category(cur, category_code)
                cur.execute(
                    """
                    INSERT INTO crawl_log (
                        seller_id,
                        category_id,
                        status,
                        collected_count
                    )
                    VALUES (%s, %s, 'RUNNING', 0)
                    RETURNING crawl_log_id;
                    """,
                    (seller_id, category_id),
                )
                crawl_log_id = cur.fetchone()[0]

            conn.commit()
            return crawl_log_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # 크롤링 정상 종료: SUCCESS 기록
    def finish_success(self, crawl_log_id: int, collected_count: int) -> None:
        self._finish(
            crawl_log_id=crawl_log_id,
            status="SUCCESS",
            collected_count=collected_count,
            error_message=None,
        )

    # 크롤링 실패/부분 실패: FAILED 기록
    def finish_failed(
        self,
        crawl_log_id: int,
        collected_count: int,
        error_message: str,
    ) -> None:
        self._finish(
            crawl_log_id=crawl_log_id,
            status="FAILED",
            collected_count=collected_count,
            error_message=error_message,
        )

    @staticmethod
    def _finish(
        crawl_log_id: int,
        status: str,
        collected_count: int,
        error_message: str = None,
    ) -> None:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE crawl_log
                    SET
                        finished_at = NOW(),
                        status = %s,
                        collected_count = %s,
                        error_message = %s
                    WHERE crawl_log_id = %s;
                    """,
                    (status, collected_count, error_message, crawl_log_id),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
