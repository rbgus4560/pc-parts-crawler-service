"""크롤링 대상 사이트와 카테고리별 실행 설정.

main.py는 이 파일의 설정만 읽어서 어떤 크롤러와 Repository를 사용할지 결정한다.

컴퓨존과 다나와 모두 검색어가 아니라 부품 카테고리 목록 URL을 기준으로
상품 상세 URL을 수집한다.
"""

from src.crawlers.compuzone.cpu_crawler import CompuzoneCpuCrawler
from src.crawlers.compuzone.gpu_crawler import CompuzoneGpuCrawler
from src.crawlers.compuzone.list_crawler import CompuzoneListCrawler
from src.crawlers.compuzone.motherboard_crawler import CompuzoneMotherboardCrawler
from src.crawlers.compuzone.ram_crawler import CompuzoneRamCrawler
from src.crawlers.compuzone.ssd_crawler import CompuzoneSsdCrawler
from src.crawlers.danawa.cpu_crawler import DanawaCpuCrawler
from src.crawlers.danawa.gpu_crawler import DanawaGpuCrawler
from src.crawlers.danawa.list_crawler import DanawaListCrawler
from src.crawlers.danawa.motherboard_crawler import DanawaMotherboardCrawler
from src.crawlers.danawa.ram_crawler import DanawaRamCrawler
from src.crawlers.danawa.ssd_crawler import DanawaSsdCrawler
from src.db.compuzone_repository import ProductRepository
from src.db.danawa_repository import DanawaRepository


# ==========================================================
# 공통 카테고리
# ==========================================================
CATEGORY_CODES = ["GPU", "CPU", "RAM", "SSD", "MOTHERBOARD"]


# ==========================================================
# 사이트별 크롤링 설정
# ==========================================================
SITE_CONFIG = {
    # ------------------------------------------------------
    # 컴퓨존
    # ------------------------------------------------------
    "COMPUZONE": {
        "seller_name": "컴퓨존",
        "site_url": "https://www.compuzone.co.kr",
        "crawl_type": "STATIC",
        "list_crawler_class": CompuzoneListCrawler,
        "repository_class": ProductRepository,
        "categories": {
            "GPU": {
                "list_url": (
                    "https://www.compuzone.co.kr/product/product_list.htm"
                    "?BigDivNo=4&MediumDivNo=1016"
                ),
                "crawler_class": CompuzoneGpuCrawler,
                "save_method": "save_gpu_product",
            },
            "CPU": {
                "list_url": (
                    "https://www.compuzone.co.kr/product/product_list.htm"
                    "?BigDivNo=4&MediumDivNo=1012"
                ),
                "crawler_class": CompuzoneCpuCrawler,
                "save_method": "save_cpu_product",
            },
            "RAM": {
                "list_url": (
                    "https://www.compuzone.co.kr/product/product_list.htm"
                    "?BigDivNo=4&MediumDivNo=1014"
                ),
                "crawler_class": CompuzoneRamCrawler,
                "save_method": "save_ram_product",
            },
            "SSD": {
                "list_url": (
                    "https://www.compuzone.co.kr/product/product_list.htm"
                    "?BigDivNo=4&MediumDivNo=1276"
                ),
                "crawler_class": CompuzoneSsdCrawler,
                "save_method": "save_ssd_product",
            },
            "MOTHERBOARD": {
                "list_url": (
                    "https://www.compuzone.co.kr/product/product_list.htm"
                    "?BigDivNo=4&MediumDivNo=1013"
                ),
                "crawler_class": CompuzoneMotherboardCrawler,
                "save_method": "save_motherboard_product",
            },
        },
    },

    # ------------------------------------------------------
    # 다나와
    #
    # 통합검색을 사용하지 않고 PC 부품 전용 카테고리 페이지를 사용한다.
    # 검색어 관련상품/액세서리/노트북 혼입을 방지하기 위한 구조다.
    # ------------------------------------------------------
    "DANAWA": {
        "seller_name": "다나와",
        "site_url": "https://www.danawa.com",
        "crawl_type": "DYNAMIC",
        "list_crawler_class": DanawaListCrawler,
        "repository_class": DanawaRepository,
        "categories": {
            "GPU": {
                "list_url": "https://prod.danawa.com/list/?cate=112753",
                "crawler_class": DanawaGpuCrawler,
                "save_method": "save_gpu_product",
            },
            "CPU": {
                "list_url": "https://prod.danawa.com/list/?cate=112747",
                "crawler_class": DanawaCpuCrawler,
                "save_method": "save_cpu_product",
            },
            "RAM": {
                "list_url": "https://prod.danawa.com/list/?cate=112752",
                "crawler_class": DanawaRamCrawler,
                "save_method": "save_ram_product",
            },
            "SSD": {
                "list_url": "https://prod.danawa.com/list/?cate=112760",
                "crawler_class": DanawaSsdCrawler,
                "save_method": "save_ssd_product",
            },
            "MOTHERBOARD": {
                "list_url": "https://prod.danawa.com/list/?cate=112751",
                "crawler_class": DanawaMotherboardCrawler,
                "save_method": "save_motherboard_product",
            },
        },
    },
}
