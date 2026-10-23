"""컴퓨존 카테고리 목록에서 여러 페이지의 상품 상세 URL을 수집한다."""

import math
import random
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class CompuzoneListCrawler:
    """컴퓨존 목록 페이지를 순회하며 중복 없는 상품 URL을 수집한다."""

    def __init__(
        self,
        min_delay=5.0,
        max_delay=10.0,
        page_size=20,
        max_pages=10,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.page_size = page_size
        self.max_pages = max_pages

    def _delay(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        print(f"대기: {delay:.2f}초")
        time.sleep(delay)

    # ==========================================================
    # 페이지 URL 생성
    # ==========================================================
    def _build_page_url(self, list_url: str, page: int) -> str:
        parsed = urlparse(list_url)
        query = parse_qs(parsed.query, keep_blank_values=True)

        query["actype"] = ["getTotalPageCount"]
        query["PageCount"] = [str(self.page_size)]
        query["select_page_cnt"] = [str(self.page_size)]
        query["StartNum"] = [str((page - 1) * self.page_size)]
        query["PageNum"] = [str(page)]
        query["ScrollPage"] = [str(page + 1)]
        query["ProductType"] = ["list"]
        query["PageType"] = ["ProductList"]

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
    # 비정상 응답 확인
    # ==========================================================
    @staticmethod
    def _is_blocked(driver) -> bool:
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
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

        return any(keyword in body_text for keyword in blocked_keywords)

    # ==========================================================
    # 현재 페이지의 상품 URL 추출
    # ==========================================================
    def _extract_product_urls(
        self,
        driver,
        target_medium_div_no: str,
        seen_product_nos: set[str],
        remaining: int,
    ) -> list[str]:
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'a[href*="product_detail.htm"]')
                )
            )
        except TimeoutException:
            return []

        links = driver.find_elements(
            By.CSS_SELECTOR,
            'a[href*="product_detail.htm"]',
        )

        page_urls = []

        for link in links:
            href = link.get_attribute("href")

            if not href or "ProductNo=" not in href:
                continue

            query = parse_qs(urlparse(href).query)
            medium_div_no = query.get("MediumDivNo", [None])[0]

            if medium_div_no != target_medium_div_no:
                continue

            product_no = query.get("ProductNo", [None])[0]

            if not product_no or product_no in seen_product_nos:
                continue

            seen_product_nos.add(product_no)
            page_urls.append(href)

            if len(page_urls) >= remaining:
                break

        return page_urls

    # ==========================================================
    # 목록 페이지 순회
    # ==========================================================
    def get_product_urls(
        self,
        list_url: str,
        limit: int = 5,
    ) -> list[str]:
        if limit <= 0:
            return []

        list_query = parse_qs(urlparse(list_url).query)
        target_medium_div_no = list_query.get(
            "MediumDivNo",
            [None],
        )[0]

        if target_medium_div_no is None:
            raise ValueError(
                "목록 URL에서 MediumDivNo를 찾을 수 없습니다."
            )

        product_urls = []
        seen_product_nos = set()

        required_pages = max(
            1,
            math.ceil(limit / self.page_size),
        )
        page_limit = min(
            self.max_pages,
            required_pages + 1,
        )

        driver = webdriver.Chrome()

        try:
            for page in range(1, page_limit + 1):
                if len(product_urls) >= limit:
                    break

                page_url = self._build_page_url(
                    list_url,
                    page,
                )

                print(
                    f"목록 페이지: {page} "
                    f"(현재 {len(product_urls)}/{limit})"
                )
                print(f"페이지 URL: {page_url}")

                driver.get(page_url)
                self._delay()

                if self._is_blocked(driver):
                    print(
                        "접근 제한 또는 CAPTCHA가 감지되어 "
                        "목록 수집을 중단합니다."
                    )
                    break

                remaining = limit - len(product_urls)

                page_urls = self._extract_product_urls(
                    driver,
                    target_medium_div_no,
                    seen_product_nos,
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
