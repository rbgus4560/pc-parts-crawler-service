"""다나와 크롤러 공통 기능.

상품별 크롤러가 공통으로 사용하는 대기, 텍스트 정리, pcode 추출,
판매처(Offer) 파싱 로직을 한 곳에서 관리한다.
"""

import hashlib
import random
import re
import time
from urllib.parse import parse_qs, urlparse

from src.models.danawa_product import DanawaOffer

class DanawaBaseCrawler:
    """다나와 상세 페이지 크롤러의 공통 기반 클래스."""

    def __init__(self, min_delay=5.0, max_delay=10.0):
        self.min_delay = min_delay
        self.max_delay = max_delay

    # ------------------------------------------------------
    # 요청 간 랜덤 대기 / 문자열 정리
    # ------------------------------------------------------
    def wait_random(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        print(f"대기: {delay:.2f}초")
        time.sleep(delay)

    @staticmethod
    def clean_text(text: str) -> str:
        return " ".join(text.split())

    # ------------------------------------------------------
    # 다나와 상품 식별자 pcode
    # ------------------------------------------------------
    @staticmethod
    def get_pcode(url: str) -> str:
        query = parse_qs(urlparse(url).query)
        pcode = query.get("pcode", [None])[0]
        if not pcode:
            raise ValueError("다나와 pcode를 찾지 못했습니다.")
        return pcode

    # ------------------------------------------------------
    # 판매처 이름 추출
    # ------------------------------------------------------
    def parse_retailer(self, block):
        mall = block.select_one("div.d_mall")
        if mall is None:
            return None

        image = mall.find("img", alt=True)
        if image:
            alt = self.clean_text(image.get("alt", ""))
            if alt:
                return alt

        logo_text = mall.select_one(".txt_logo")
        if logo_text:
            retailer = self.clean_text(logo_text.get_text(" ", strip=True))
            if retailer:
                return retailer

        link = mall.select_one("a.link.priceCompareBuyLink")
        if link:
            retailer = self.clean_text(link.get_text(" ", strip=True))
            retailer = retailer.replace("네이버페이", "").strip()
            if retailer:
                return retailer

        return None

    # ------------------------------------------------------
    # 다나와 판매처별 Offer 고유 ID 생성
    # ------------------------------------------------------
    @staticmethod
    def make_source_offer_id(pcode: str, offer_url: str):
        query = parse_qs(urlparse(offer_url).query)
        cmpnyc = query.get("cmpnyc", [None])[0]
        link_pcode = query.get("link_pcode", [None])[0]

        if cmpnyc and link_pcode:
            return f"{pcode}:{cmpnyc}:{link_pcode}"

        member_id = query.get("memberId", [None])[0]
        seller_seq = query.get("sellerSeq", [None])[0]
        if member_id or seller_seq:
            return f"{pcode}:{member_id or 'NONE'}:{seller_seq or 'NONE'}"

        digest = hashlib.sha1(offer_url.encode("utf-8")).hexdigest()[:16]
        return f"{pcode}:{digest}"

    # ------------------------------------------------------
    # 판매처별 가격 / 링크 / source_offer_id 수집
    # ------------------------------------------------------
    def parse_offers(self, soup, pcode: str):
        offers = []
        seen_offer_ids = set()

        for block in soup.select("div.diff_box"):
            retailer = self.parse_retailer(block)
            if not retailer:
                continue

            price_element = block.select_one("div.prc_line em.prc_c")
            if price_element is None:
                price_element = block.select_one("em.prc_c")
            if price_element is None:
                continue

            price_text = price_element.get_text(strip=True).replace(",", "")
            price_match = re.search(r"\d+", price_text)
            if not price_match:
                continue

            price = int(price_match.group())
            if price <= 0:
                continue

            buy_link = block.select_one("a.btn_buy.priceCompareBuyLink[href]")
            if buy_link is None:
                buy_link = block.select_one("a.priceCompareBuyLink[href]")
            if buy_link is None:
                continue

            offer_url = buy_link.get("href")
            if not offer_url or offer_url == "#":
                continue

            source_offer_id = self.make_source_offer_id(pcode, offer_url)
            if source_offer_id in seen_offer_ids:
                continue

            seen_offer_ids.add(source_offer_id)
            offers.append(
                DanawaOffer(
                    retailer=retailer,
                    source_offer_id=source_offer_id,
                    price=price,
                    product_url=offer_url,
                )
            )

        return offers
