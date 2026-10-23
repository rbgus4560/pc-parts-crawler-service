"""컴퓨존 GPU 상세 페이지 파싱."""

import re
from urllib.parse import parse_qs, urlparse

from src.crawlers.compuzone.base_crawler import CompuzoneBaseCrawler
from src.models.compuzone_product import CrawledProduct

class CompuzoneGpuCrawler(CompuzoneBaseCrawler):
    """컴퓨존 GPU 상품명, 가격, 모델, VRAM, 메모리 규격을 수집한다."""

    # ======================================================
    # GPU 상세 정보 파싱
    # ======================================================
    def crawl_product(self, url: str) -> CrawledProduct:
        # 1. 상품 페이지 로드 / 기본 정보
        soup = self.get_soup(url)
        if soup.title is not None:
            title = soup.title.get_text(strip=True)
        else:
            og_title = soup.find('meta', property='og:title')
            if og_title is not None and og_title.get('content'):
                title = og_title.get('content').strip()
            else:
                raise ValueError('상품명을 찾지 못했습니다. 정상적인 상품 페이지가 수신되지 않았을 수 있습니다.')
        product_name = title.replace(': 컴퓨존', '').strip()
        query = parse_qs(urlparse(url).query)
        product_no = query.get('ProductNo', [None])[0]
        brand_match = re.match('\\[([^\\]]+)\\]', product_name)
        brand = brand_match.group(1) if brand_match else None
        text = soup.get_text(' ', strip=True)
        # 2. 판매가 / 대표 이미지
        price_match = re.search('판매가\\s+(?:[\\d,]+\\s+)?([\\d,]+)\\s*원', text)
        if not price_match:
            raise ValueError('판매가를 찾지 못했습니다.')
        price = int(price_match.group(1).replace(',', ''))
        image_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content')
        # 3. 부품별 스펙 문자열 탐색
        spec_text = None
        for string in soup.stripped_strings:
            if 'PCI Express' in string and '/' in string and ('GDDR' in string):
                spec_text = string
                break
        gpu_model = None
        vram_gb = None
        memory_type = None
        if spec_text:
            specs = [item.strip() for item in spec_text.split('/')]
            if specs:
                gpu_model = specs[0]
            for item in specs:
                match = re.fullmatch('(\\d+)\\s*GB', item, re.IGNORECASE)
                if match:
                    vram_gb = int(match.group(1))
                    break
            for item in specs:
                if re.fullmatch('GDDR\\d+', item, re.IGNORECASE):
                    memory_type = item.upper()
                    break
        nvidia_match = re.search(
            '\\b(RTX|GTX)\\s*(\\d{3,4})(?:\\s*(Ti(?:\\s+SUPER)?|SUPER))?\\b',
            product_name,
            re.IGNORECASE,
        )
        amd_match = re.search(
            '\\bRX\\s*(\\d{4})(?:\\s*(XTX|XT|GRE))?\\b',
            product_name,
            re.IGNORECASE,
        )
        if nvidia_match:
            series = nvidia_match.group(1).upper()
            number = nvidia_match.group(2)
            suffix = nvidia_match.group(3)
            gpu_model = f'{series} {number}'
            if suffix:
                suffix = suffix.upper()
                if suffix == 'TI':
                    suffix = 'Ti'
                elif suffix == 'TI SUPER':
                    suffix = 'Ti SUPER'
                gpu_model += f' {suffix}'
        elif amd_match:
            number = amd_match.group(1)
            suffix = amd_match.group(2)
            gpu_model = f'RX {number}'
            if suffix:
                gpu_model += f' {suffix.upper()}'
        if vram_gb is None:
            vram_match = re.search('\\bD\\d+\\s+(\\d+)\\s*GB\\b', product_name, re.IGNORECASE)
            if not vram_match:
                vram_match = re.search('\\b(\\d+)\\s*GB\\b', product_name, re.IGNORECASE)
            if vram_match:
                vram_gb = int(vram_match.group(1))
        if memory_type is None:
            memory_match = re.search('\\bD(\\d+)\\b', product_name, re.IGNORECASE)
            if memory_match:
                memory_type = f'GDDR{memory_match.group(1)}'
        # 4. 크롤링 결과 객체 생성
        return CrawledProduct(
            seller='컴퓨존',
            retailer='컴퓨존',
            category='GPU',
            source_product_id=product_no,
            product_name=product_name,
            brand=brand,
            price=price,
            product_url=url,
            image_url=image_url,
            model_name=gpu_model,
            vram_gb=vram_gb,
            memory_type=memory_type,
            raw_spec_text=spec_text,
        )
