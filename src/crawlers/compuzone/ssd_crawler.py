"""컴퓨존 SSD 상세 페이지에서 용량·인터페이스·규격·속도를 추출한다."""

import re
from urllib.parse import urlparse, parse_qs
from src.crawlers.compuzone.base_crawler import CompuzoneBaseCrawler
from src.models.compuzone_product import SsdCrawledProduct

class CompuzoneSsdCrawler:
    """컴퓨존 SSD 상세 크롤러."""

    def __init__(self, min_delay=5.0, max_delay=10.0):
        self.base_crawler = CompuzoneBaseCrawler(min_delay=min_delay, max_delay=max_delay)

    # SSD 상세 정보 파싱
    def crawl_product(self, url: str) -> SsdCrawledProduct:
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
        # 3. 부품별 스펙 문자열 탐색
        spec_text = None
        spec_candidates = []
        for string in soup.stripped_strings:
            text = string.strip()
            if not text:
                continue
            has_interface = 'PCIe' in text or 'NVMe' in text or 'SATA' in text
            has_ssd_detail = (
                '읽기' in text or '쓰기' in text or 'SSD' in text or 'M.2' in text
            )
            if '/' in text and has_interface and has_ssd_detail:
                spec_candidates.append(text)
        if spec_candidates:
            spec_text = max(spec_candidates, key=lambda text: (text.count('/'), len(text)))
        capacity_gb = None
        interface = None
        pcie_generation = None
        form_factor = None
        read_speed_mbps = None
        write_speed_mbps = None
        capacity_match = re.search(
            '\\[(\\d+(?:\\.\\d+)?)\\s*(GB|TB)\\]',
            product_name,
            re.IGNORECASE,
        )
        if not capacity_match:
            capacity_match = re.search(
                '\\b(\\d+(?:\\.\\d+)?)\\s*(GB|TB)\\b',
                product_name,
                re.IGNORECASE,
            )
        if capacity_match:
            capacity_value = float(capacity_match.group(1))
            capacity_unit = capacity_match.group(2).upper()
            if capacity_unit == 'TB':
                capacity_gb = int(capacity_value * 1024)
            else:
                capacity_gb = int(capacity_value)
        if capacity_gb is None and spec_text:
            capacity_match = re.search(
                '(?:^|/)\\s*(\\d+(?:\\.\\d+)?)\\s*(GB|TB)\\s*(?:/|$)',
                spec_text,
                re.IGNORECASE,
            )
            if capacity_match:
                capacity_value = float(capacity_match.group(1))
                capacity_unit = capacity_match.group(2).upper()
                if capacity_unit == 'TB':
                    capacity_gb = int(capacity_value * 1024)
                else:
                    capacity_gb = int(capacity_value)
        if re.search('\\bNVMe\\b', product_name, re.IGNORECASE):
            interface = 'NVMe'
        elif re.search('\\bSATA\\b', product_name, re.IGNORECASE):
            interface = 'SATA'
        elif spec_text:
            if re.search('\\bNVMe\\b', spec_text, re.IGNORECASE):
                interface = 'NVMe'
            elif re.search('\\bSATA\\b', spec_text, re.IGNORECASE):
                interface = 'SATA'
        if interface is None and spec_text and re.search('PCIe', spec_text, re.IGNORECASE):
            interface = 'NVMe'
        source_text = spec_text if spec_text else product_name
        pcie_match = re.search('PCIe\\s*(?:Gen\\s*)?([345])(?:\\.0)?', source_text, re.IGNORECASE)
        if pcie_match:
            pcie_generation = f'PCIe Gen{pcie_match.group(1)}'
        m2_match = re.search('\\bM\\.?2\\b', product_name, re.IGNORECASE)
        size_match = re.search('\\b(2230|2242|2260|2280|22110)\\b', product_name)
        if m2_match:
            if size_match:
                form_factor = f'M.2 {size_match.group(1)}'
            else:
                form_factor = 'M.2'
        if form_factor == 'M.2' and spec_text:
            spec_size_match = re.search(
                'M\\.?2\\s*\\(?(2230|2242|2260|2280|22110)\\)?',
                spec_text,
                re.IGNORECASE,
            )
            if spec_size_match:
                form_factor = f'M.2 {spec_size_match.group(1)}'
        if form_factor is None:
            if re.search('2\\.5\\s*(?:형|인치|inch)?', product_name, re.IGNORECASE):
                form_factor = '2.5 inch'
            elif spec_text and re.search('2\\.5\\s*(?:형|인치|inch)?', spec_text, re.IGNORECASE):
                form_factor = '2.5 inch'
        if spec_text:
            read_match = re.search(
                '(?:순차)?읽기\\s*:?\\s*([\\d,]+)\\s*(?:MB/s|MB/S|M)\\b',
                spec_text,
                re.IGNORECASE,
            )
            if read_match:
                read_speed_mbps = int(read_match.group(1).replace(',', ''))
        if spec_text:
            write_match = re.search(
                '(?:순차)?쓰기\\s*:?\\s*([\\d,]+)\\s*(?:MB/s|MB/S|M)\\b',
                spec_text,
                re.IGNORECASE,
            )
            if write_match:
                write_speed_mbps = int(write_match.group(1).replace(',', ''))
        # 4. 크롤링 결과 객체 생성
        return SsdCrawledProduct(
            seller='컴퓨존',
            retailer='컴퓨존',
            category='SSD',
            source_product_id=product_no,
            product_name=product_name,
            brand=brand,
            price=price,
            product_url=url,
            image_url=image_url,
            capacity_gb=capacity_gb,
            interface=interface,
            pcie_generation=pcie_generation,
            form_factor=form_factor,
            read_speed_mbps=read_speed_mbps,
            write_speed_mbps=write_speed_mbps,
            raw_spec_text=spec_text,
        )
