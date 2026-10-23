"""컴퓨존 메인보드 상세 페이지에서 소켓·칩셋·메모리·폼팩터를 추출한다."""

import re
from urllib.parse import urlparse, parse_qs
from src.crawlers.compuzone.base_crawler import CompuzoneBaseCrawler
from src.models.compuzone_product import MotherboardCrawledProduct


# 메인보드 칩셋 추출용 공통 패턴
GENERIC_CHIPSET_PATTERN = (
    r'\b('
    r'A\d{3}[A-Z]?|B\d{3}[A-Z]?|H\d{3}[A-Z]?|Q\d{3}[A-Z]?|'
    r'W\d{3}[A-Z]?|X\d{3}[A-Z]?|Z\d{3}[A-Z]?'
    r')\b'
)

class CompuzoneMotherboardCrawler:
    """컴퓨존 MOTHERBOARD 상세 크롤러."""

    def __init__(self, min_delay=5.0, max_delay=10.0):
        self.base_crawler = CompuzoneBaseCrawler(min_delay=min_delay, max_delay=max_delay)

    # MOTHERBOARD 상세 정보 파싱
    def crawl_product(self, url: str) -> MotherboardCrawledProduct:
        # 1. 상품 페이지 로드 / 기본 정보
        soup = self.base_crawler.get_soup(url)
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
        page_text = soup.get_text(' ', strip=True)
        # 2. 판매가 / 대표 이미지
        price_match = re.search('판매가\\s+(?:[\\d,]+\\s+)?([\\d,]+)\\s*원', page_text)
        if not price_match:
            raise ValueError('판매가를 찾지 못했습니다. 판매 종료 또는 가격 정보가 없는 상품일 수 있습니다.')
        price = int(price_match.group(1).replace(',', ''))
        image_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content')
        spec_candidates = []
        for string in soup.stripped_strings:
            text = string.strip()
            if not text:
                continue
            if '소켓' in text and re.search('\\bDDR[45]\\b', text, re.IGNORECASE) and ('/' in text):
                spec_candidates.append(text)
        raw_spec_text = None
        if spec_candidates:
            raw_spec_text = max(spec_candidates, key=lambda text: (text.count('/'), len(text)))
        source_text = raw_spec_text if raw_spec_text else product_name
        socket = None
        chipset = None
        memory_type = None
        form_factor = None
        amd_socket_match = re.search('(AM[345])', source_text, re.IGNORECASE)
        if amd_socket_match:
            socket = amd_socket_match.group(1).upper()
        if socket is None:
            intel_socket_match = re.search('LGA\\s*(\\d{4})', source_text, re.IGNORECASE)
            if intel_socket_match:
                socket = 'LGA' + intel_socket_match.group(1)
        if socket is None:
            intel_socket_match = re.search(
                '(?:인텔\\s*)?소켓\\s*(1150|1151|1200|1700|1851|2066)',
                source_text,
                re.IGNORECASE,
            )
            if intel_socket_match:
                socket = 'LGA' + intel_socket_match.group(1)
        chipset_match = re.search('\\bAMD\\s+([ABX]\\d{3}[A-Z]?)\\b', source_text, re.IGNORECASE)
        if chipset_match:
            chipset = chipset_match.group(1).upper()
        if chipset is None:
            chipset_match = re.search(
                '\\b(?:INTEL|인텔)\\s+([BHQWZ]\\d{3}[A-Z]?)\\b',
                source_text,
                re.IGNORECASE,
            )
            if chipset_match:
                chipset = chipset_match.group(1).upper()
        if chipset is None:
            chipset_match = re.search(
                GENERIC_CHIPSET_PATTERN,
                source_text,
                re.IGNORECASE,
            )
            if chipset_match:
                chipset = chipset_match.group(1).upper()
        memory_match = re.search('\\b(DDR4|DDR5)\\b', source_text, re.IGNORECASE)
        if memory_match:
            memory_type = memory_match.group(1).upper()
        if re.search('\\bMini[\\s-]*ITX\\b', source_text, re.IGNORECASE):
            form_factor = 'Mini-ITX'
        elif re.search('\\bE[\\s-]*ATX\\b', source_text, re.IGNORECASE):
            form_factor = 'E-ATX'
        elif re.search('\\b(?:M[\\s-]*ATX|MATX|Micro[\\s-]*ATX)\\b', source_text, re.IGNORECASE):
            form_factor = 'M-ATX'
        elif re.search('\\bATX\\b', source_text, re.IGNORECASE):
            form_factor = 'ATX'
        elif re.search('\\bITX\\b', source_text, re.IGNORECASE):
            form_factor = 'Mini-ITX'
        if chipset is None:
            title_chipset_match = re.search(
                GENERIC_CHIPSET_PATTERN,
                product_name,
                re.IGNORECASE,
            )
            if title_chipset_match:
                chipset = title_chipset_match.group(1).upper()
        if form_factor is None:
            if re.search('\\bM[\\s-]*ATX\\b', product_name, re.IGNORECASE):
                form_factor = 'M-ATX'
            elif re.search('\\bATX\\b', product_name, re.IGNORECASE):
                form_factor = 'ATX'
            elif re.search('\\bMini[\\s-]*ITX\\b', product_name, re.IGNORECASE):
                form_factor = 'Mini-ITX'
        # 4. 크롤링 결과 객체 생성
        return MotherboardCrawledProduct(
            seller='컴퓨존',
            retailer='컴퓨존',
            category='MOTHERBOARD',
            source_product_id=product_no,
            product_name=product_name,
            brand=brand,
            price=price,
            product_url=url,
            image_url=image_url,
            socket=socket,
            chipset=chipset,
            memory_type=memory_type,
            form_factor=form_factor,
            raw_spec_text=raw_spec_text,
        )
