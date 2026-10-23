"""다나와 RAM 상세 페이지에서 용량·DDR 규격·속도·모듈 수와 판매처를 추출한다."""

import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.crawlers.danawa.base_crawler import DanawaBaseCrawler
from src.models.danawa_product import DanawaRamProduct

class DanawaRamCrawler(DanawaBaseCrawler):
    """RAM 스펙 파싱과 판매처 정보를 수집한다."""

    # ======================================================
    # RAM 스펙 파싱
    # ======================================================
    @staticmethod
    def parse_capacity(product_name: str):
        match = re.search('\\(\\s*(\\d+)\\s*GB', product_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search('(\\d+)\\s*GB', product_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def parse_memory_type(spec_text: str):
        match = re.search('\\bDDR([3-6])\\b', spec_text, re.IGNORECASE)
        if match:
            return f'DDR{match.group(1)}'
        return None

    @staticmethod
    def parse_speed(spec_text: str):
        match = re.search('\\b(\\d{4,5})\\s*MHz\\b', spec_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search('\\b(\\d{4,5})\\s*MT/s\\b', spec_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def parse_module_count(spec_text: str, product_name: str):
        match = re.search('램\\s*개수\\s*:\\s*(\\d+)\\s*개', spec_text)
        if match:
            return int(match.group(1))
        match = re.search('\\d+\\s*G(?:B)?\\s*[xX×]\\s*(\\d+)', product_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    # RAM 상세 정보 + Offer 파싱
    def crawl_product(self, url: str) -> DanawaRamProduct:
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
                raise ValueError('다나와 RAM 상품명을 찾지 못했습니다.')
            words = product_name.split()
            brand = words[0] if words else None
            spec_element = soup.select_one('div.spec_list')
            if spec_element is None:
                raise ValueError('다나와 RAM spec_list를 찾지 못했습니다.')
            raw_spec_text = self.clean_text(spec_element.get_text(' ', strip=True))
            # 3. 부품별 스펙 파싱
            capacity_gb = self.parse_capacity(product_name)
            memory_type = self.parse_memory_type(raw_spec_text)
            speed_mts = self.parse_speed(raw_spec_text)
            module_count = self.parse_module_count(raw_spec_text, product_name)
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image.get('content')
            # 4. 판매처별 Offer 수집
            offers = self.parse_offers(soup, pcode)
            if not offers:
                raise ValueError('다나와 RAM 판매처를 찾지 못했습니다.')
            # 5. 크롤링 결과 객체 생성
            return DanawaRamProduct(
                seller='다나와',
                category='RAM',
                pcode=pcode,
                product_name=product_name,
                brand=brand,
                product_url=url,
                image_url=image_url,
                capacity_gb=capacity_gb,
                memory_type=memory_type,
                speed_mts=speed_mts,
                module_count=module_count,
                raw_spec_text=raw_spec_text,
                offers=offers,
            )
        finally:
            driver.quit()
