"""다나와 메인보드 상세 페이지에서 소켓·칩셋·메모리·폼팩터와 판매처를 추출한다."""

import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.crawlers.danawa.base_crawler import DanawaBaseCrawler
from src.models.danawa_product import DanawaMotherboardProduct

class DanawaMotherboardCrawler(DanawaBaseCrawler):
    """MOTHERBOARD 스펙 파싱과 판매처 정보를 수집한다."""

    # ======================================================
    # MOTHERBOARD 스펙 파싱
    # ======================================================
    @staticmethod
    def parse_socket(spec_text: str):
        match = re.search('소켓\\s*([A-Z0-9]+)', spec_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def parse_chipset(spec_text: str):
        match = re.search(
            '(?:AMD|INTEL|인텔)\\s+([A-Z]{1,4}\\d{2,4}[A-Z]?)\\b',
            spec_text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).upper()
        match = re.search('\\b([ABHQWXZ]\\d{3}[A-Z]?)\\b', spec_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def parse_memory_type(spec_text: str):
        match = re.search('\\bDDR([4-5])\\b', spec_text, re.IGNORECASE)
        if match:
            return f'DDR{match.group(1)}'
        return None

    @staticmethod
    def parse_form_factor(spec_text: str):
        patterns = [
            ('\\bE-ATX\\b', 'E-ATX'),
            ('\\bM-ATX\\b', 'M-ATX'),
            ('\\bM-ITX\\b', 'M-ITX'),
            ('\\bATX\\b', 'ATX'),
            ('\\bITX\\b', 'ITX'),
        ]
        for pattern, value in patterns:
            if re.search(pattern, spec_text, re.IGNORECASE):
                return value
        return None

    # MOTHERBOARD 상세 정보 + Offer 파싱
    def crawl_product(self, url: str) -> DanawaMotherboardProduct:
        # 1. Selenium으로 상품 상세 페이지 로드
        driver = webdriver.Chrome()
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            self.wait_random()
            soup = BeautifulSoup(driver.page_source, 'lxml')
            # 2. 상품 기본 정보(pcode / 상품명 / 브랜드 / 이미지)
            pcode = self.get_pcode(url)
            product_name = None
            title_element = soup.select_one('h2.f_tit')
            if title_element:
                product_name = self.clean_text(title_element.get_text(' ', strip=True))
            if not product_name:
                title_element = soup.select_one('h1.blind')
                if title_element:
                    product_name = self.clean_text(title_element.get_text(' ', strip=True))
                    product_name = product_name.replace(': 다나와 가격비교', '').strip()
            if not product_name:
                raise ValueError('다나와 메인보드 상품명을 찾지 못했습니다.')
            words = product_name.split()
            brand = words[0] if words else None
            spec_element = soup.select_one('div.spec_list')
            if spec_element is None:
                raise ValueError('다나와 메인보드 spec_list를 찾지 못했습니다.')
            raw_spec_text = self.clean_text(spec_element.get_text(' ', strip=True))
            # 3. 부품별 스펙 파싱
            socket = self.parse_socket(raw_spec_text)
            chipset = self.parse_chipset(raw_spec_text)
            memory_type = self.parse_memory_type(raw_spec_text)
            form_factor = self.parse_form_factor(raw_spec_text)
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image.get('content')
            # 4. 판매처별 Offer 수집
            offers = self.parse_offers(soup, pcode)
            if not offers:
                raise ValueError('다나와 메인보드 판매처를 찾지 못했습니다.')
            # 5. 크롤링 결과 객체 생성
            return DanawaMotherboardProduct(
                seller='다나와',
                category='MOTHERBOARD',
                pcode=pcode,
                product_name=product_name,
                brand=brand,
                product_url=url,
                image_url=image_url,
                socket=socket,
                chipset=chipset,
                memory_type=memory_type,
                form_factor=form_factor,
                raw_spec_text=raw_spec_text,
                offers=offers,
            )
        finally:
            driver.quit()
