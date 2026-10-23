"""다나와 SSD 상세 페이지에서 용량·인터페이스·PCIe·폼팩터·속도와 판매처를 추출한다."""

import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.crawlers.danawa.base_crawler import DanawaBaseCrawler
from src.models.danawa_product import DanawaSsdProduct

class DanawaSsdCrawler(DanawaBaseCrawler):
    """SSD 스펙 파싱과 판매처 정보를 수집한다."""

    # ======================================================
    # SSD 스펙 파싱
    # ======================================================
    @staticmethod
    def parse_capacity(product_name: str):
        match = re.search('\\(\\s*([0-9.]+)\\s*TB\\s*\\)', product_name, re.IGNORECASE)
        if match:
            capacity_tb = float(match.group(1))
            return int(capacity_tb * 1000)
        match = re.search('\\(\\s*(\\d+)\\s*GB\\s*\\)', product_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search('\\b([0-9.]+)\\s*TB\\b', product_name, re.IGNORECASE)
        if match:
            capacity_tb = float(match.group(1))
            return int(capacity_tb * 1000)
        match = re.search('\\b(\\d+)\\s*GB\\b', product_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def parse_interface(product_name: str, spec_text: str):
        combined_text = product_name + ' ' + spec_text
        if re.search('\\bNVMe\\b', combined_text, re.IGNORECASE):
            return 'NVMe'
        if re.search('\\bSATA\\b', combined_text, re.IGNORECASE):
            return 'SATA'
        return None

    @staticmethod
    def parse_pcie_generation(spec_text: str):
        match = re.search('\\bPCIe\\s*([1-9])(?:\\.0)?', spec_text, re.IGNORECASE)
        if match:
            return f'PCIe{match.group(1)}.0'
        return None

    @staticmethod
    def parse_form_factor(product_name: str, spec_text: str):
        combined_text = spec_text + ' ' + product_name
        match = re.search('M\\.2\\s*\\(\\s*(\\d{4})\\s*\\)', combined_text, re.IGNORECASE)
        if match:
            return f'M.2 {match.group(1)}'
        if re.search('\\bM\\.2\\b', combined_text, re.IGNORECASE):
            return 'M.2'
        if re.search('2\\.5\\s*(?:형|인치)', combined_text, re.IGNORECASE):
            return '2.5형'
        return None

    @staticmethod
    def parse_read_speed(spec_text: str):
        match = re.search('순차\\s*읽기\\s*:\\s*([\\d,]+)\\s*MB/s', spec_text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(',', ''))
        return None

    @staticmethod
    def parse_write_speed(spec_text: str):
        match = re.search('순차\\s*쓰기\\s*:\\s*([\\d,]+)\\s*MB/s', spec_text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(',', ''))
        return None

    # SSD 상세 정보 + Offer 파싱
    def crawl_product(self, url: str) -> DanawaSsdProduct:
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
                raise ValueError('다나와 SSD 상품명을 찾지 못했습니다.')
            words = product_name.split()
            brand = words[0] if words else None
            spec_element = soup.select_one('div.spec_list')
            if spec_element is None:
                raise ValueError('다나와 SSD spec_list를 찾지 못했습니다.')
            raw_spec_text = self.clean_text(spec_element.get_text(' ', strip=True))
            # 3. 부품별 스펙 파싱
            capacity_gb = self.parse_capacity(product_name)
            interface = self.parse_interface(product_name, raw_spec_text)
            pcie_generation = self.parse_pcie_generation(raw_spec_text)
            form_factor = self.parse_form_factor(product_name, raw_spec_text)
            read_speed_mbps = self.parse_read_speed(raw_spec_text)
            write_speed_mbps = self.parse_write_speed(raw_spec_text)
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image.get('content')
            # 4. 판매처별 Offer 수집
            offers = self.parse_offers(soup, pcode)
            if not offers:
                raise ValueError('다나와 SSD 판매처를 찾지 못했습니다.')
            # 5. 크롤링 결과 객체 생성
            return DanawaSsdProduct(
                seller='다나와',
                category='SSD',
                pcode=pcode,
                product_name=product_name,
                brand=brand,
                product_url=url,
                image_url=image_url,
                capacity_gb=capacity_gb,
                interface=interface,
                pcie_generation=pcie_generation,
                form_factor=form_factor,
                read_speed_mbps=read_speed_mbps,
                write_speed_mbps=write_speed_mbps,
                raw_spec_text=raw_spec_text,
                offers=offers,
            )
        finally:
            driver.quit()
