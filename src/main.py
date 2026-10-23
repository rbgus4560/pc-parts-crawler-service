"""컴퓨존/다나와 통합 크롤러 실행 진입점."""

import argparse

from src.crawler_config import CATEGORY_CODES, SITE_CONFIG
from src.db.crawl_log_repository import CrawlLogRepository


# 사이트 요청 간 랜덤 대기 범위
MIN_DELAY = 20.0
MAX_DELAY = 25.0


# ==========================================================
# 상품 목록 URL 수집
#
# 두 사이트 모두 category_config["list_url"]을 사용한다.
# 사이트별 페이지 처리 방식은 각 ListCrawler 내부에서 담당한다.
# ==========================================================
def collect_product_urls(
    category_config: dict,
    list_crawler,
    limit: int,
) -> list[str]:
    list_url = category_config["list_url"]

    print("목록 URL:", list_url)

    return list_crawler.get_product_urls(
        list_url,
        limit=limit,
    )


# ==========================================================
# 사이트 + 카테고리 1개 크롤링 실행
# 목록 수집 → 상세 파싱 → DB 저장 → CRAWL_LOG 기록
# ==========================================================
def crawl_category(seller_key: str, category_code: str, limit: int):
    site_config = SITE_CONFIG[seller_key]
    category_config = site_config["categories"][category_code]
    seller_name = site_config["seller_name"]

    _print_start(seller_name, category_code, limit)

    product_repository = site_config["repository_class"]()
    log_repository = CrawlLogRepository()
    collected_count = 0
    failed_count = 0
    skipped_count = 0
    error_messages = []
    crawl_log_id = None

    try:
        crawl_log_id = log_repository.start_log(
            seller_name=seller_name,
            category_code=category_code,
            site_url=site_config["site_url"],
            crawl_type=site_config["crawl_type"],
        )
        print("CRAWL_LOG ID:", crawl_log_id)

        list_crawler = site_config["list_crawler_class"](
            min_delay=MIN_DELAY,
            max_delay=MAX_DELAY,
        )

        urls = collect_product_urls(
            category_config=category_config,
            list_crawler=list_crawler,
            limit=limit,
        )

        print("\n상품 URL 수:", len(urls))

        if not urls:
            raise RuntimeError("상품 URL을 수집하지 못했습니다.")

        crawler = category_config["crawler_class"](
            min_delay=MIN_DELAY,
            max_delay=MAX_DELAY,
        )
        save_method = getattr(
            product_repository,
            category_config["save_method"],
        )

        for index, url in enumerate(urls, start=1):
            print("\n" + "-" * 70)
            print(f"[{index}/{len(urls)}]")
            print("URL:", url)

            try:
                product = crawler.crawl_product(url)
                _print_product(product)

                save_result = save_method(product)
                product_id, saved_offer_count = _parse_save_result(
                    save_result
                )
                collected_count += 1

                print("DB 저장 성공")
                print("product_id:", product_id)

                if saved_offer_count is not None:
                    print("DB 저장 Offer 수:", saved_offer_count)

            except ValueError as exc:
                if "판매가를 찾지 못했습니다" in str(exc):
                    skipped_count += 1
                    print("판매 종료/가격 정보 없음")
                    print("→ DB 저장 없이 다음 상품 계속")
                    continue

                failed_count += 1
                error_messages.append(
                    f"{url} | {type(exc).__name__}: {exc}"
                )
                print("상품 처리 실패")
                print("오류 종류:", type(exc).__name__)
                print("오류 내용:", exc)
                print("→ 다음 상품 계속")

            except Exception as exc:
                failed_count += 1
                error_messages.append(
                    f"{url} | {type(exc).__name__}: {exc}"
                )
                print("상품 처리 실패")
                print("오류 종류:", type(exc).__name__)
                print("오류 내용:", exc)
                print("→ 다음 상품 계속")

        status = _finish_log(
            log_repository=log_repository,
            crawl_log_id=crawl_log_id,
            collected_count=collected_count,
            failed_count=failed_count,
            error_messages=error_messages,
        )

        _print_finish(
            seller_name,
            category_code,
            status,
            collected_count,
            failed_count,
            skipped_count,
        )

        return {
            "seller": seller_name,
            "category": category_code,
            "status": status,
            "collected": collected_count,
            "failed": failed_count,
            "skipped": skipped_count,
        }

    except Exception as exc:
        if crawl_log_id is not None:
            log_repository.finish_failed(
                crawl_log_id=crawl_log_id,
                collected_count=collected_count,
                error_message=f"{type(exc).__name__}: {exc}",
            )

        print("\n" + "=" * 70)
        print(f"{seller_name} {category_code} 크롤링 전체 실패")
        print("오류 종류:", type(exc).__name__)
        print("오류 내용:", exc)
        print("=" * 70)

        return {
            "seller": seller_name,
            "category": category_code,
            "status": "FAILED",
            "collected": collected_count,
            "failed": failed_count + 1,
            "skipped": skipped_count,
        }


# ==========================================================
# 실행 보조 함수
# ==========================================================
def _parse_save_result(save_result):
    if isinstance(save_result, tuple):
        return save_result[0], save_result[1]
    return save_result, None


def _finish_log(
    log_repository,
    crawl_log_id: int,
    collected_count: int,
    failed_count: int,
    error_messages: list,
) -> str:
    if failed_count == 0:
        log_repository.finish_success(
            crawl_log_id=crawl_log_id,
            collected_count=collected_count,
        )
        return "SUCCESS"

    log_repository.finish_failed(
        crawl_log_id=crawl_log_id,
        collected_count=collected_count,
        error_message="\n".join(error_messages)[:5000],
    )
    return "FAILED"


def _print_product(product) -> None:
    print("상품:", product.product_name)

    if hasattr(product, "price"):
        print("가격:", f"{product.price:,}원")

    if hasattr(product, "offers"):
        print("Offer 수:", len(product.offers))


def _print_start(
    seller_name: str,
    category_code: str,
    limit: int,
) -> None:
    print("\n" + "=" * 70)
    print(f"{seller_name} {category_code} 크롤링 시작")
    print("카테고리 전체 수집 제한:", limit)
    print("=" * 70)


def _print_finish(
    seller_name: str,
    category_code: str,
    status: str,
    collected_count: int,
    failed_count: int,
    skipped_count: int,
) -> None:
    print("\n" + "=" * 70)
    print(f"{seller_name} {category_code} 크롤링 종료")
    print("상태:", status)
    print("DB 저장 성공:", collected_count)
    print("처리 실패:", failed_count)
    print("건너뜀:", skipped_count)
    print("=" * 70)


# ==========================================================
# CLI 인자 처리
# ==========================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="컴퓨존 + 다나와 PC 부품 크롤러"
    )
    parser.add_argument(
        "--seller",
        default="COMPUZONE",
        choices=["COMPUZONE", "DANAWA", "ALL"],
        help="수집 사이트",
    )
    parser.add_argument(
        "--category",
        default="MOTHERBOARD",
        choices=[*CATEGORY_CODES, "ALL"],
        help="수집 카테고리",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="사이트별 카테고리 전체 수집 상품 수",
    )
    return parser.parse_args()


# ==========================================================
# 프로그램 시작점
# ==========================================================
def main():
    args = parse_args()

    if args.limit <= 0:
        raise ValueError("--limit은 1 이상이어야 합니다.")

    seller_keys = (
        list(SITE_CONFIG)
        if args.seller == "ALL"
        else [args.seller]
    )
    category_codes = (
        CATEGORY_CODES
        if args.category == "ALL"
        else [args.category]
    )

    results = [
        crawl_category(
            seller_key,
            category_code,
            args.limit,
        )
        for seller_key in seller_keys
        for category_code in category_codes
    ]

    print("\n" + "=" * 70)
    print("전체 크롤링 결과")
    print("=" * 70)

    for result in results:
        print(
            result["seller"],
            "|",
            result["category"],
            "|",
            result["status"],
            "| 성공:",
            result["collected"],
            "| 실패:",
            result["failed"],
            "| 건너뜀:",
            result["skipped"],
        )

    print("=" * 70)


if __name__ == "__main__":
    main()
