"""다나와 PC 부품 카테고리 목록에서 상품 상세 URL을 수집한다."""

import random
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class DanawaListCrawler:
    """카테고리별 DOM 차이를 흡수하면서 상품 상세 URL을 수집한다."""

    DETAIL_LINK_SELECTOR = 'a[href*="prod.danawa.com/info/"]'

    FALLBACK_ITEM_SELECTORS = (
        "div.main_prodlist li.prod_item",
        "li.prod_item",
    )

    FALLBACK_TITLE_SELECTORS = (
        "p.prod_name a",
        "div.prod_info p.prod_name a",
        "a.click_log_product_standard_title_",
    )

    def __init__(
        self,
        min_delay=5.0,
        max_delay=10.0,
        page_size=40,
        max_pages=10,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.page_size = page_size
        self.max_pages = max_pages

    def wait_random(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        print(f"대기: {delay:.2f}초")
        time.sleep(delay)

    # ==========================================================
    # 페이지 URL 생성
    # ==========================================================
    def _build_page_url(self, list_url: str, page: int) -> str:
        parsed = urlparse(list_url)
        query = parse_qs(parsed.query, keep_blank_values=True)

        query["page"] = [str(page)]
        query["limit"] = [str(self.page_size)]
        query["list"] = ["list"]

        encoded_query = urlencode(query, doseq=True)

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                encoded_query,
                parsed.fragment,
            )
        )

    # ==========================================================
    # 현재 카테고리 번호
    # ==========================================================
    @staticmethod
    def _get_target_category(list_url: str) -> str:
        query = parse_qs(urlparse(list_url).query)
        category = query.get("cate", [None])[0]

        if not category:
            raise ValueError(
                "다나와 카테고리 URL에서 cate 값을 찾을 수 없습니다."
            )

        return category

    # ==========================================================
    # 접근 제한 감지
    # ==========================================================
    @staticmethod
    def _is_blocked(driver) -> bool:
        try:
            body_text = driver.find_element(
                By.TAG_NAME,
                "body",
            ).text.lower()
        except Exception:
            return False

        blocked_keywords = (
            "too many requests",
            "access denied",
            "비정상적인 접근",
            "접근이 제한",
            "요청이 너무 많",
            "captcha",
        )

        return any(
            keyword in body_text
            for keyword in blocked_keywords
        )

    # ==========================================================
    # URL에서 pcode 추출
    # ==========================================================
    @staticmethod
    def _parse_product_link(href: str):
        if not href or "prod.danawa.com/info/" not in href:
            return None, None

        query = parse_qs(urlparse(href).query)
        pcode = query.get("pcode", [None])[0]
        category = query.get("cate", [None])[0]

        return pcode, category

    # ==========================================================
    # 1차: cate+pcode가 명시된 상품 링크 수집
    # RAM/SSD/메인보드처럼 카드 class가 다른 페이지 대응
    # ==========================================================
    def _extract_category_links(
        self,
        driver,
        target_category: str,
        seen_pcodes: set[str],
        remaining: int,
    ) -> list[str]:
        links = driver.find_elements(
            By.CSS_SELECTOR,
            self.DETAIL_LINK_SELECTOR,
        )

        page_urls = []

        for link in links:
            href = link.get_attribute("href")
            pcode, category = self._parse_product_link(href)

            if not pcode or category != target_category:
                continue

            if pcode in seen_pcodes:
                continue

            seen_pcodes.add(pcode)
            page_urls.append(
                "https://prod.danawa.com/info/"
                f"?cate={target_category}&pcode={pcode}"
            )

            if len(page_urls) >= remaining:
                break

        if page_urls:
            print(
                "카테고리 일치 상품 URL:",
                len(page_urls),
                "개",
            )

        return page_urls

    # ==========================================================
    # 2차 fallback: CPU/GPU에서 검증된 상품 카드 방식
    # ==========================================================
    def _extract_fallback_links(
        self,
        driver,
        target_category: str,
        seen_pcodes: set[str],
        remaining: int,
    ) -> list[str]:
        for item_selector in self.FALLBACK_ITEM_SELECTORS:
            items = driver.find_elements(
                By.CSS_SELECTOR,
                item_selector,
            )

            if not items:
                continue

            page_urls = []

            for item in items:
                href = None

                for title_selector in self.FALLBACK_TITLE_SELECTORS:
                    title_links = item.find_elements(
                        By.CSS_SELECTOR,
                        title_selector,
                    )

                    for title_link in title_links:
                        candidate = title_link.get_attribute("href")

                        if (
                            candidate
                            and "prod.danawa.com/info/" in candidate
                        ):
                            href = candidate
                            break

                    if href:
                        break

                if not href:
                    continue

                pcode, _ = self._parse_product_link(href)

                if not pcode or pcode in seen_pcodes:
                    continue

                seen_pcodes.add(pcode)
                page_urls.append(
                    "https://prod.danawa.com/info/"
                    f"?cate={target_category}&pcode={pcode}"
                )

                if len(page_urls) >= remaining:
                    break

            if page_urls:
                print(
                    f"fallback 상품 카드: {item_selector} "
                    f"({len(page_urls)}개)"
                )
                return page_urls

        return []

    # ==========================================================
    # 현재 페이지 상품 URL 추출
    # ==========================================================
    def _extract_product_urls(
        self,
        driver,
        target_category: str,
        seen_pcodes: set[str],
        remaining: int,
    ) -> list[str]:
        WebDriverWait(driver, 15).until(
            lambda current_driver: (
                len(
                    current_driver.find_elements(
                        By.CSS_SELECTOR,
                        self.DETAIL_LINK_SELECTOR,
                    )
                ) > 0
                or len(
                    current_driver.find_elements(
                        By.TAG_NAME,
                        "body",
                    )
                ) > 0
            )
        )

        page_urls = self._extract_category_links(
            driver,
            target_category,
            seen_pcodes,
            remaining,
        )

        if page_urls:
            return page_urls

        return self._extract_fallback_links(
            driver,
            target_category,
            seen_pcodes,
            remaining,
        )

    # ==========================================================
    # 카테고리 페이지 순회
    # ==========================================================
    def get_product_urls(
        self,
        list_url: str,
        limit: int = 3,
    ) -> list[str]:
        if limit <= 0:
            return []

        target_category = self._get_target_category(
            list_url
        )

        product_urls = []
        seen_pcodes = set()

        driver = webdriver.Chrome()

        try:
            for page in range(
                1,
                self.max_pages + 1,
            ):
                if len(product_urls) >= limit:
                    break

                page_url = self._build_page_url(
                    list_url,
                    page,
                )

                print(
                    f"카테고리 페이지: {page} "
                    f"(현재 {len(product_urls)}/{limit})"
                )
                print("페이지 URL:", page_url)

                driver.get(page_url)
                self.wait_random()

                if self._is_blocked(driver):
                    print(
                        "접근 제한 또는 CAPTCHA가 감지되어 "
                        "목록 수집을 중단합니다."
                    )
                    break

                remaining = (
                    limit - len(product_urls)
                )

                page_urls = self._extract_product_urls(
                    driver,
                    target_category,
                    seen_pcodes,
                    remaining,
                )

                if not page_urls:
                    print(
                        "현재 페이지에서 새로운 상품 URL을 "
                        "찾지 못해 종료합니다."
                    )
                    break

                product_urls.extend(page_urls)

                print(
                    f"페이지 신규 URL: {len(page_urls)}개 / "
                    f"누적: {len(product_urls)}개"
                )

            return product_urls[:limit]

        finally:
            driver.quit()
