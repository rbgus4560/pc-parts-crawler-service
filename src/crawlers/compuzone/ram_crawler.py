"""컴퓨존 RAM 상세 페이지에서 용량·DDR 규격·속도 정보를 추출한다."""

import re
from urllib.parse import parse_qs, urlparse

from src.crawlers.compuzone.base_crawler import CompuzoneBaseCrawler
from src.models.compuzone_product import RamCrawledProduct


class CompuzoneRamCrawler:
    """컴퓨존 데스크톱 RAM 상세 크롤러."""

    def __init__(self, min_delay=5.0, max_delay=10.0):
        self.base_crawler = CompuzoneBaseCrawler(
            min_delay=min_delay,
            max_delay=max_delay,
        )

    # ======================================================
    # 데스크톱 RAM 대상 여부 확인
    # ======================================================
    @staticmethod
    def _validate_desktop_ram(
        product_name: str,
        spec_text: str = None,
    ) -> None:
        check_text = " ".join(
            value
            for value in (
                product_name,
                spec_text,
            )
            if value
        ).upper()

        excluded_keywords = (
            "노트북용",
            "SO-DIMM",
            "SODIMM",
        )

        if any(
            keyword.upper() in check_text
            for keyword in excluded_keywords
        ):
            raise ValueError(
                "노트북용 RAM은 수집 대상이 아닙니다."
            )

    # ======================================================
    # RAM 상세 정보 파싱
    # ======================================================
    def crawl_product(self, url: str) -> RamCrawledProduct:
        # 1. 상품 페이지 로드 / 기본 정보
        soup = self.base_crawler.get_soup(url)

        if soup.title is not None:
            title = soup.title.get_text(strip=True)
        else:
            og_title = soup.find(
                "meta",
                property="og:title",
            )

            if (
                og_title is not None
                and og_title.get("content")
            ):
                title = og_title.get(
                    "content"
                ).strip()
            else:
                raise ValueError(
                    "상품명을 찾지 못했습니다. "
                    "정상적인 상품 페이지가 수신되지 않았을 수 있습니다."
                )

        product_name = title.replace(
            ": 컴퓨존",
            "",
        ).strip()

        query = parse_qs(
            urlparse(url).query
        )
        product_no = query.get(
            "ProductNo",
            [None],
        )[0]

        brand_match = re.match(
            r"\[([^\]]+)\]",
            product_name,
        )
        brand = (
            brand_match.group(1)
            if brand_match
            else None
        )

        page_text = soup.get_text(
            " ",
            strip=True,
        )

        # 2. 판매가 / 대표 이미지
        price_match = re.search(
            r"판매가\s+(?:[\d,]+\s+)?([\d,]+)\s*원",
            page_text,
        )

        if not price_match:
            raise ValueError(
                "판매가를 찾지 못했습니다."
            )

        price = int(
            price_match.group(1).replace(
                ",",
                "",
            )
        )

        image_url = None
        og_image = soup.find(
            "meta",
            property="og:image",
        )

        if og_image:
            image_url = og_image.get(
                "content"
            )

        # 3. 스펙 문자열 탐색
        spec_text = None
        spec_candidates = []

        for string in soup.stripped_strings:
            text = string.strip()

            if not text:
                continue

            has_memory_type = re.search(
                r"\bDDR\d+\b",
                text,
                re.IGNORECASE,
            )

            has_speed = (
                "MHz" in text
                or "MT/s" in text
                or "MT/S" in text
            )

            if (
                has_memory_type
                and "/" in text
                and has_speed
            ):
                spec_candidates.append(
                    text
                )

        if spec_candidates:
            capacity_candidates = [
                text
                for text
                in spec_candidates
                if re.search(
                    r"\d+\s*GB",
                    text,
                    re.IGNORECASE,
                )
            ]

            if capacity_candidates:
                spec_text = max(
                    capacity_candidates,
                    key=lambda text: (
                        text.count("/"),
                        len(text),
                    ),
                )
            else:
                spec_text = max(
                    spec_candidates,
                    key=lambda text: (
                        text.count("/"),
                        len(text),
                    ),
                )

        self._validate_desktop_ram(
            product_name,
            spec_text,
        )

        capacity_gb = None
        memory_type = None
        speed_mts = None
        module_count = None

        source_text = (
            spec_text
            if spec_text
            else product_name
        )

        # 4. 메모리 규격
        memory_match = re.search(
            r"\b(DDR\d+)\b",
            source_text,
            re.IGNORECASE,
        )

        if memory_match:
            memory_type = (
                memory_match.group(1).upper()
            )

        # 5. 총 용량
        bracket_capacity_match = re.search(
            r"\[(\d+)\s*GB(?:[^\]]*)\]",
            product_name,
            re.IGNORECASE,
        )

        if bracket_capacity_match:
            capacity_gb = int(
                bracket_capacity_match.group(
                    1
                )
            )

        if (
            capacity_gb is None
            and spec_text
        ):
            capacity_match = re.search(
                r"(?:^|/)\s*(\d+)\s*GB(?:\s*/|$)",
                spec_text,
                re.IGNORECASE,
            )

            if capacity_match:
                capacity_gb = int(
                    capacity_match.group(1)
                )

        # 6. 속도
        #
        # 컴퓨존 상품명 끝의 (5600), (6000), (6400) 값이
        # 실제 메모리 동작 속도를 가장 안정적으로 나타낸다.
        # 페이지 스펙의 600/800/400 같은 다른 숫자를 먼저 잡지 않도록
        # 상품명을 최우선으로 사용한다.
        product_speed_matches = re.findall(
            r"\((\d{4,5})\)",
            product_name,
        )

        if product_speed_matches:
            speed_mts = int(
                product_speed_matches[-1]
            )

        if (
            speed_mts is None
            and spec_text
        ):
            speed_match = re.search(
                r"\b(\d{4,5})\s*(?:MHz|MT/s|MT/S)\b",
                spec_text,
                re.IGNORECASE,
            )

            if speed_match:
                speed_mts = int(
                    speed_match.group(1)
                )

        # 7. 모듈 수
        # 16GB*2 / 16GB x 2 / 16GB×2 모두 인식한다.
        module_match = re.search(
            r"\d+\s*GB\s*[xX×*]\s*(\d+)",
            product_name,
            re.IGNORECASE,
        )

        if (
            not module_match
            and spec_text
        ):
            module_match = re.search(
                r"\d+\s*GB\s*[xX×*]\s*(\d+)",
                spec_text,
                re.IGNORECASE,
            )

        if module_match:
            module_count = int(
                module_match.group(1)
            )

        # 8. 크롤링 결과 객체 생성
        return RamCrawledProduct(
            seller="컴퓨존",
            retailer="컴퓨존",
            category="RAM",
            source_product_id=product_no,
            product_name=product_name,
            brand=brand,
            price=price,
            product_url=url,
            image_url=image_url,
            capacity_gb=capacity_gb,
            memory_type=memory_type,
            speed_mts=speed_mts,
            module_count=module_count,
            raw_spec_text=spec_text,
        )
