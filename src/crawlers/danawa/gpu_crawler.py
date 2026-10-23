"""다나와 GPU 상세 페이지 파싱."""

import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.crawlers.danawa.base_crawler import DanawaBaseCrawler
from src.models.danawa_product import DanawaGpuProduct

class DanawaGpuCrawler(DanawaBaseCrawler):
    """다나와 GPU 스펙과 판매처별 가격을 수집한다."""

    # ======================================================
    # GPU 모델 / VRAM / 메모리 규격 파싱
    # ======================================================
    @staticmethod
    def parse_gpu_model(product_name: str):
        match = re.search(
            '\\b(RTX|GTX)\\s*(\\d{3,4})(?:\\s*(Ti|SUPER))?\\b',
            product_name,
            re.IGNORECASE,
        )
        if match:
            family = match.group(1).upper()
            number = match.group(2)
            suffix = match.group(3)
            if suffix:
                if suffix.upper() == 'TI':
                    suffix = 'Ti'
                else:
                    suffix = suffix.upper()
                return f'{family} {number} {suffix}'
            return f'{family} {number}'
        match = re.search('\\bRX\\s*(\\d{4})(?:\\s*(XT|XTX))?\\b', product_name, re.IGNORECASE)
        if match:
            number = match.group(1)
            suffix = match.group(2)
            if suffix:
                return f'RX {number} {suffix.upper()}'
            return f'RX {number}'
        match = re.search('\\bARC\\s*([AB]\\d{3})\\b', product_name, re.IGNORECASE)
        if match:
            return f'ARC {match.group(1).upper()}'
        return None

    @staticmethod
    def parse_vram(product_name: str):
        match = re.search('\\b(?:D[67]|GDDR[67])\\s*(\\d+)\\s*GB\\b', product_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def parse_memory_type(product_name: str):
        match = re.search('\\bGDDR([67])\\b', product_name, re.IGNORECASE)
        if match:
            return f'GDDR{match.group(1)}'
        match = re.search('\\bD([67])\\s*\\d+\\s*GB\\b', product_name, re.IGNORECASE)
        if match:
            return f'GDDR{match.group(1)}'
        return None


    # GPU 상세 정보 + Offer 파싱
    def crawl_product(self, url: str) -> DanawaGpuProduct:
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
            if not product_name and soup.title:
                product_name = self.clean_text(soup.title.get_text(' ', strip=True))
                product_name = product_name.replace(': 다나와 가격비교', '').strip()
            if not product_name:
                raise ValueError('다나와 상품명을 찾지 못했습니다.')
            product_words = product_name.split()
            brand = product_words[0] if product_words else None
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image.get('content')
            # 3. 부품별 스펙 파싱
            model_name = self.parse_gpu_model(product_name)
            vram_gb = self.parse_vram(product_name)
            memory_type = self.parse_memory_type(product_name)
            raw_spec_items = []
            for string in soup.stripped_strings:
                text = self.clean_text(string)
                if not text:
                    continue
                if model_name and text.upper() == model_name.upper():
                    raw_spec_items.append(text)
                    continue
                if re.fullmatch('GDDR[567]', text, re.IGNORECASE):
                    raw_spec_items.append(text)
                    continue
                if re.fullmatch('PCIe[\\d.]+x\\d+', text, re.IGNORECASE):
                    raw_spec_items.append(text)
            raw_spec_items = list(dict.fromkeys(raw_spec_items))
            raw_spec_text = ' / '.join(raw_spec_items[:10]) if raw_spec_items else None
            # 4. 판매처별 Offer 수집
            offers = self.parse_offers(soup, pcode)
            if not offers:
                raise ValueError('다나와 판매처 정보를 찾지 못했습니다.')
            # 5. 크롤링 결과 객체 생성
            return DanawaGpuProduct(
                seller='다나와',
                category='GPU',
                pcode=pcode,
                product_name=product_name,
                brand=brand,
                product_url=url,
                image_url=image_url,
                model_name=model_name,
                vram_gb=vram_gb,
                memory_type=memory_type,
                raw_spec_text=raw_spec_text,
                offers=offers,
            )
        finally:
            driver.quit()
