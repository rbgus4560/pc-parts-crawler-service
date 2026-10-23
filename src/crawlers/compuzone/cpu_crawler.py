"""컴퓨존 CPU 상세 페이지에서 모델·소켓·코어·클럭 정보를 추출한다."""

import re
from urllib.parse import urlparse, parse_qs
from src.crawlers.compuzone.base_crawler import CompuzoneBaseCrawler
from src.models.compuzone_product import CpuCrawledProduct

class CompuzoneCpuCrawler:
    """컴퓨존 CPU 상세 크롤러."""

    def __init__(self, min_delay=5.0, max_delay=10.0):
        self.base_crawler = CompuzoneBaseCrawler(min_delay=min_delay, max_delay=max_delay)

    # CPU 상세 정보 파싱
    def crawl_product(self, url: str) -> CpuCrawledProduct:
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
            raise ValueError('판매가를 찾지 못했습니다.')
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
            has_socket = re.search('(AM\\d+|LGA\\s*\\d+|소켓\\s*\\d+)', text, re.IGNORECASE)
            if '/' in text and 'GHz' in text and ('코어' in text or has_socket):
                spec_candidates.append(text)
        socket_candidates = []
        for candidate in spec_candidates:
            if re.search('(AM\\d+|LGA\\s*\\d+|소켓\\s*\\d+)', candidate, re.IGNORECASE):
                socket_candidates.append(candidate)
        if socket_candidates:
            spec_text = max(socket_candidates, key=lambda text: (text.count('/'), len(text)))
        elif spec_candidates:
            spec_text = max(spec_candidates, key=lambda text: (text.count('/'), len(text)))
        # 4. CPU 모델명 / 코어 / 스레드 / 소켓 / 클럭 해석
        model_name = None
        socket = None
        cores = None
        threads = None
        base_clock_ghz = None
        boost_clock_ghz = None
        if brand:
            brand_upper = brand.upper()
            if brand_upper == 'AMD':
                amd_model_match = re.search(
                    '\\b(\\d{4,5}(?:X3D\\d*|XT|X|GE|G|F)?)\\b',
                    product_name,
                    re.IGNORECASE,
                )
                if amd_model_match:
                    model_name = amd_model_match.group(1).upper()
            elif brand_upper == 'INTEL':
                intel_ultra_match = re.search(
                    '(?:코어\\s*)?Ultra\\s*([3579])(?:\\s*프로세서)?\\s*(\\d{3,4}[A-Z]{0,2})',
                    product_name,
                    re.IGNORECASE,
                )
                if intel_ultra_match:
                    ultra_grade = intel_ultra_match.group(1)
                    ultra_model = intel_ultra_match.group(2).upper()
                    model_name = f'Core Ultra {ultra_grade} {ultra_model}'
                else:
                    intel_core_match = re.search(
                        '\\b(i[3579])[-\\s]?(\\d{4,5}[A-Z]{0,2})\\b',
                        product_name,
                        re.IGNORECASE,
                    )
                    if intel_core_match:
                        intel_grade = intel_core_match.group(1).lower()
                        intel_model = intel_core_match.group(2).upper()
                        model_name = f'{intel_grade}-{intel_model}'
        if spec_text:
            hybrid_core_match = re.search(
                'P\\s*(\\d+)\\s*\\+\\s*E\\s*(\\d+)\\s*코어',
                spec_text,
                re.IGNORECASE,
            )
            if hybrid_core_match:
                p_cores = int(hybrid_core_match.group(1))
                e_cores = int(hybrid_core_match.group(2))
                cores = p_cores + e_cores
            else:
                core_match = re.search('(\\d+)\\s*코어', spec_text)
                if not core_match:
                    core_match = re.search('\\((\\d+)\\)\\s*코어', spec_text)
                if core_match:
                    cores = int(core_match.group(1))
            hybrid_thread_match = re.search('(\\d+)\\s*\\+\\s*(\\d+)\\s*(?:스레드|쓰레드)', spec_text)
            if hybrid_thread_match:
                first_threads = int(hybrid_thread_match.group(1))
                second_threads = int(hybrid_thread_match.group(2))
                threads = first_threads + second_threads
            else:
                thread_match = re.search('(\\d+)\\s*(?:스레드|쓰레드)', spec_text)
                if thread_match:
                    threads = int(thread_match.group(1))
            socket_match = re.search('(AM\\d+|LGA\\s*\\d+|소켓\\s*\\d+)', spec_text, re.IGNORECASE)
            if socket_match:
                socket_value = socket_match.group(1).upper().replace(' ', '')
                if socket_value.startswith('소켓'):
                    socket_number = re.search('\\d+', socket_value)
                    if socket_number:
                        socket = 'LGA' + socket_number.group(0)
                else:
                    socket = socket_value
            base_match = re.search(
                '기본\\s*클럭\\s*:\\s*(\\d+(?:\\.\\d+)?)\\s*GHz',
                spec_text,
                re.IGNORECASE,
            )
            if base_match:
                base_clock_ghz = float(base_match.group(1))
            boost_match = re.search(
                '(?:최대|부스트)\\s*클럭\\s*:\\s*(\\d+(?:\\.\\d+)?)\\s*GHz',
                spec_text,
                re.IGNORECASE,
            )
            if boost_match:
                boost_clock_ghz = float(boost_match.group(1))
            clock_range_match = re.search(
                '(\\d+(?:\\.\\d+)?)\\s*~\\s*(\\d+(?:\\.\\d+)?)\\s*GHz',
                spec_text,
                re.IGNORECASE,
            )
            if clock_range_match:
                if base_clock_ghz is None:
                    base_clock_ghz = float(clock_range_match.group(1))
                if boost_clock_ghz is None:
                    boost_clock_ghz = float(clock_range_match.group(2))
            if base_clock_ghz is None:
                clock_match = re.search('(\\d+(?:\\.\\d+)?)\\s*GHz', spec_text, re.IGNORECASE)
                if clock_match:
                    base_clock_ghz = float(clock_match.group(1))
        if cores is None:
            name_core_match = re.search('(\\d+)\\s*코어', product_name)
            if name_core_match:
                cores = int(name_core_match.group(1))
        if threads is None:
            name_thread_match = re.search('(\\d+)\\s*(?:스레드|쓰레드)', product_name)
            if name_thread_match:
                threads = int(name_thread_match.group(1))
        if base_clock_ghz is None:
            name_clock_match = re.search('(\\d+(?:\\.\\d+)?)\\s*GHz', product_name, re.IGNORECASE)
            if name_clock_match:
                base_clock_ghz = float(name_clock_match.group(1))
        # 5. 크롤링 결과 객체 생성
        return CpuCrawledProduct(
            seller='컴퓨존',
            retailer='컴퓨존',
            category='CPU',
            source_product_id=product_no,
            product_name=product_name,
            brand=brand,
            price=price,
            product_url=url,
            image_url=image_url,
            model_name=model_name,
            socket=socket,
            cores=cores,
            threads=threads,
            base_clock_ghz=base_clock_ghz,
            boost_clock_ghz=boost_clock_ghz,
            raw_spec_text=spec_text,
        )
