# 리팩터링 정리 (v3)

## 목적

코드를 짧게 만드는 것만이 아니라, 나중에 다시 봤을 때 **어느 사이트 / 어느 부품 / 어느 역할인지 바로 찾을 수 있게** 정리했다.

## 가장 큰 변경점

### 1. 크롤러를 사이트별 폴더로 분리

```text
src/crawlers/
├─ compuzone/
│  ├─ base_crawler.py
│  ├─ list_crawler.py
│  ├─ gpu_crawler.py
│  ├─ cpu_crawler.py
│  ├─ ram_crawler.py
│  ├─ ssd_crawler.py
│  └─ motherboard_crawler.py
└─ danawa/
   ├─ base_crawler.py
   ├─ list_crawler.py
   ├─ gpu_crawler.py
   ├─ cpu_crawler.py
   ├─ ram_crawler.py
   ├─ ssd_crawler.py
   └─ motherboard_crawler.py
```

이제 `src/crawlers`에서 파일명이 섞이지 않고, **사이트 → 부품** 순서로 찾으면 된다.

### 2. 큰 주석은 다시 넣음

세세한 한 줄 설명을 남발하지 않고 다음 정도만 남겼다.

- 파일이 담당하는 역할
- GPU / CPU / RAM / SSD / MOTHERBOARD 구분
- 목록 수집 / 상세 파싱 / DB 저장 구분
- PRODUCT / SPEC / OFFER / PRICE_HISTORY 저장 흐름
- 가격 이력 / 호환성 / 크롤링 로그 조회 역할

### 3. Repository 역할 유지

```text
src/db/
├─ base_repository.py          # 공통 CATEGORY/BRAND/PRODUCT/OFFER/PRICE 저장
├─ spec_repository.py          # GPU/CPU/RAM/SSD/MOTHERBOARD 스펙 저장
├─ compuzone_repository.py     # 컴퓨존 저장 흐름
├─ danawa_repository.py        # 다나와 저장 흐름
├─ price_repository.py         # 가격 이력/통계 조회
├─ compatibility_repository.py # CPU/RAM ↔ 메인보드 호환성
└─ crawl_log_repository.py     # 크롤링 실행 로그
```

## 코드 스타일

짧은 표현은 한 줄로 유지한다.

```python
model_name=cpu_model["model_name"]
product_id=cur.fetchone()[0]
```

다만 SQL, 함수 인자가 길어지는 경우에는 의미 단위로 줄바꿈한다.

## 기능 변경 여부

이번 v3는 **구조와 가독성 중심 리팩터링**이다. 기존 크롤링/DB 저장 로직을 새 기능으로 바꾸지 않았다.

## v4 추가 정리

`GPU crawler`를 다른 부품의 공통 기반처럼 사용하던 구조를 분리했다.

- `compuzone/base_crawler.py`: requests 세션, 랜덤 대기, HTML/BeautifulSoup 처리
- `danawa/base_crawler.py`: 랜덤 대기, pcode, 판매처명, Offer 가격/링크 처리
- `gpu_crawler.py`: 이제 GPU 파싱만 담당

따라서 CPU 파일을 볼 때 GPU 파일을 공통 기반으로 이해해야 하는 혼란을 줄였다.

## 이름도 사이트 기준으로 정리

- `src/db/repository.py` → `src/db/compuzone_repository.py`
- `src/models/product.py` → `src/models/compuzone_product.py`

`repository.py`, `product.py`처럼 어디 사이트인지 애매한 이름을 줄였다.
