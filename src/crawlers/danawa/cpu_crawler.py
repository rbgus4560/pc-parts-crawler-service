"""다나와 CPU 상세 페이지에서 모델·세대·소켓·코어·클럭과 판매처를 추출한다."""

import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.crawlers.danawa.base_crawler import DanawaBaseCrawler
from src.models.danawa_product import DanawaCpuProduct

class DanawaCpuCrawler(DanawaBaseCrawler):
    """CPU 모델·스펙과 판매처 정보를 수집한다."""

    # ======================================================
    # CPU 모델 / 스펙 파싱
    # ======================================================
    @staticmethod
    def parse_amd_cpu(product_name: str):
        match = re.search(
            '라이젠\\s*([3579])(?:-\\s*([0-9]+세대))?\\s+([0-9]{4}[A-Z0-9]*)',
            product_name,
            re.IGNORECASE,
        )
        if not match:
            return {
                'model_name': None,
                'family': 'Ryzen',
                'generation': None,
                'tier': None,
                'suffix': None,
            }
        tier = match.group(1)
        generation = match.group(2)
        model_code = match.group(3).upper()
        suffix_match = re.search('\\d+([A-Z].*)$', model_code)
        suffix = suffix_match.group(1) if suffix_match else None
        model_name = f'Ryzen {tier} {model_code}'
        return {
            'model_name': model_name,
            'family': 'Ryzen',
            'generation': generation,
            'tier': tier,
            'suffix': suffix,
        }

    @staticmethod
    def parse_intel_cpu(product_name: str):
        match = re.search(
            '코어\\s*울트라\\s*([3579])(?:\\s*(시리즈\\d+))?\\s+([0-9]{3}[A-Z]*(?:\\s+Plus)?)',
            product_name,
            re.IGNORECASE,
        )
        if match:
            tier = match.group(1)
            generation = match.group(2)
            model_code = match.group(3).strip()
            suffix_match = re.search('\\d+(.+)$', model_code)
            suffix = None
            if suffix_match:
                suffix = suffix_match.group(1).strip()
                if not suffix:
                    suffix = None
            return {
                'model_name': f'Core Ultra {tier} {model_code}',
                'family': 'Core Ultra',
                'generation': generation,
                'tier': tier,
                'suffix': suffix,
            }
        match = re.search(
            '코어\\s*i([3579])(?:-\\s*([0-9]+세대))?\\s+([0-9]{4,5}[A-Z]*)',
            product_name,
            re.IGNORECASE,
        )
        if match:
            tier_num = match.group(1)
            tier = f'i{tier_num}'
            generation = match.group(2)
            model_code = match.group(3).upper()
            suffix_match = re.search('\\d+([A-Z]+)$', model_code)
            suffix = suffix_match.group(1) if suffix_match else None
            return {
                'model_name': f'Core {tier} {model_code}',
                'family': 'Core',
                'generation': generation,
                'tier': tier,
                'suffix': suffix,
            }
        return {
            'model_name': None,
            'family': 'Core',
            'generation': None,
            'tier': None,
            'suffix': None,
        }

    @classmethod
    def parse_cpu_model(cls, product_name: str, brand: str):
        if brand.upper() == 'AMD':
            return cls.parse_amd_cpu(product_name)
        if brand.upper() in ['INTEL', '인텔']:
            return cls.parse_intel_cpu(product_name)
        return {
            'model_name': None,
            'family': None,
            'generation': None,
            'tier': None,
            'suffix': None,
        }

    @staticmethod
    # CPU 스펙 파싱
    def parse_socket(spec_text: str, brand: str):
        match = re.search('소켓\\s*([A-Z]*\\d+)', spec_text, re.IGNORECASE)
        if not match:
            return None
        socket = match.group(1).upper()
        if socket.startswith('AM'):
            return socket
        if socket.startswith('LGA'):
            return socket
        if brand.upper() in ['INTEL', '인텔'] and socket.isdigit():
            return f'LGA{socket}'
        return socket

    @staticmethod
    def parse_cores(spec_text: str):
        match = re.search('(\\d+)\\s*코어', spec_text)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def parse_threads(spec_text: str):
        match = re.search('(\\d+)\\s*스레드', spec_text)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def parse_base_clock(spec_text: str):
        match = re.search('기본\\s*클럭\\s*:\\s*([0-9.]+)\\s*GHz', spec_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    @staticmethod
    def parse_boost_clock(spec_text: str):
        match = re.search('(?:최대|부스트)\\s*클럭\\s*:\\s*([0-9.]+)\\s*GHz', spec_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    # CPU 상세 정보 + Offer 파싱
    def crawl_product(self, url: str) -> DanawaCpuProduct:
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
                raise ValueError('다나와 CPU 상품명을 찾지 못했습니다.')
            if re.search('\\bAMD\\b', product_name, re.IGNORECASE):
                brand = 'AMD'
            elif '인텔' in product_name or re.search('\\bINTEL\\b', product_name, re.IGNORECASE):
                brand = 'Intel'
            else:
                brand = product_name.split()[0]
            # 3. 부품별 스펙 파싱
            cpu_model = self.parse_cpu_model(product_name, brand)
            spec_element = soup.select_one('div.spec_list')
            if spec_element is None:
                raise ValueError('다나와 CPU spec_list를 찾지 못했습니다.')
            raw_spec_text = self.clean_text(spec_element.get_text(' ', strip=True))
            socket = self.parse_socket(raw_spec_text, brand)
            cores = self.parse_cores(raw_spec_text)
            threads = self.parse_threads(raw_spec_text)
            base_clock_ghz = self.parse_base_clock(raw_spec_text)
            boost_clock_ghz = self.parse_boost_clock(raw_spec_text)
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image.get('content')
            # 4. 판매처별 Offer 수집
            offers = self.parse_offers(soup, pcode)
            if not offers:
                raise ValueError('다나와 CPU 판매처를 찾지 못했습니다.')
            # 5. 크롤링 결과 객체 생성
            return DanawaCpuProduct(
                seller='다나와',
                category='CPU',
                pcode=pcode,
                product_name=product_name,
                brand=brand,
                product_url=url,
                image_url=image_url,
                model_name=cpu_model['model_name'],
                family=cpu_model['family'],
                generation=cpu_model['generation'],
                tier=cpu_model['tier'],
                suffix=cpu_model['suffix'],
                socket=socket,
                cores=cores,
                threads=threads,
                base_clock_ghz=base_clock_ghz,
                boost_clock_ghz=boost_clock_ghz,
                raw_spec_text=raw_spec_text,
                offers=offers,
            )
        finally:
            driver.quit()
