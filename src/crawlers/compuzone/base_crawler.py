"""컴퓨존 크롤러 공통 HTTP 요청 기능.

GPU/CPU/RAM/SSD/MOTHERBOARD 크롤러가 동일한 요청/대기 로직을 재사용한다.
"""

import random
import time

import requests
from bs4 import BeautifulSoup

class CompuzoneBaseCrawler:
    """컴퓨존 요청 세션과 HTML 파싱의 공통 기반 클래스."""

    BASE_URL = "https://www.compuzone.co.kr"

    def __init__(self, min_delay=1.5, max_delay=3.0):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/154.0.0.0 Safari/537.36"
                )
            }
        )
        self.min_delay = min_delay
        self.max_delay = max_delay

    # ------------------------------------------------------
    # 사이트 요청 간 랜덤 대기
    # ------------------------------------------------------
    def _delay(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        print(f"대기: {delay:.2f}초")
        time.sleep(delay)

    # ------------------------------------------------------
    # HTTP 요청 / BeautifulSoup 변환
    # ------------------------------------------------------
    def fetch_html(self, url: str) -> str:
        self._delay()
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def get_soup(self, url: str) -> BeautifulSoup:
        return BeautifulSoup(self.fetch_html(url), "lxml")
