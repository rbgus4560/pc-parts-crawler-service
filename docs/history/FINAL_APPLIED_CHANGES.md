# 최종 적용본

적용 내용
- 컴퓨존 페이지네이션: 페이지당 20개 기준
- 다나와: 통합검색 대신 부품 전용 카테고리 사용
- 다나와 목록: cate+pcode 방식 + CPU/GPU 상품카드 fallback
- RAM: 용량/메모리 타입/속도/모듈 수를 상품 식별에 반영
- SSD: 용량/인터페이스/PCIe 세대/폼팩터를 상품 식별에 반영
- 컴퓨존 판매 종료/가격 없음 상품: 실패가 아니라 건너뜀 처리
- 요청 간 랜덤 대기: 35~40초
- Flask 웹 UI 포함
- DB 스키마 변경 없음

본수집 권장 명령
& <사용자 홈>\anaconda3\envs\web_crol\python.exe -m src.main --seller ALL --category ALL --limit 20 2>&1 | Tee-Object -FilePath .\full_crawl_log.txt

웹 실행
& <사용자 홈>\anaconda3\envs\web_crol\python.exe -m web.app
