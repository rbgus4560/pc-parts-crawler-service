from math import ceil

from flask import Flask, abort, render_template, request, url_for

from src.db.compatibility_repository import CompatibilityRepository
from src.db.price_repository import PriceRepository
from src.db.web_repository import WebRepository


app = Flask(__name__)

web_repository = WebRepository()
price_repository = PriceRepository()
compatibility_repository = CompatibilityRepository()


@app.template_filter("price")
def format_price(value):
    """정수 가격을 123,000원 형태로 표시한다."""
    if value is None:
        return "-"
    return f"{int(value):,}원"


@app.template_filter("datetime_kr")
def format_datetime(value):
    """수집 시각을 화면용 문자열로 변환한다."""
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def get_query_filters():
    """상품 목록 화면의 공통 검색 조건을 읽는다."""
    return {
        "keyword": request.args.get("q", "").strip(),
        "category_code": request.args.get("category", "").strip().upper(),
        "brand_name": request.args.get("brand", "").strip(),
        "socket": request.args.get("socket", "").strip(),
        "memory_type": request.args.get("memory_type", "").strip(),
        "capacity_gb": request.args.get("capacity_gb", type=int),
        "vram_gb": request.args.get("vram_gb", type=int),
        "chipset": request.args.get("chipset", "").strip(),
        "interface": request.args.get("interface", "").strip(),
        "pcie_generation": request.args.get("pcie_generation", "").strip(),
        "form_factor": request.args.get("form_factor", "").strip(),
        "speed_mts": request.args.get("speed_mts", type=int),
        "model_family": request.args.get("family", "").strip(),
        "model_name": request.args.get("model", "").strip(),
    }


# ==========================================================
# 홈
# - 검색
# - 카테고리 바로가기
# ==========================================================
@app.get("/")
def home():
    categories = web_repository.get_categories()

    return render_template(
        "home.html",
        categories=categories,
    )


# ==========================================================
# 상품 목록
# - 검색
# - 카테고리 / 제조사 / 스펙 필터
# - 현재 최저가 기준 상품 카드
# ==========================================================
@app.get("/products")
def product_list():
    filters = get_query_filters()

    if filters["category_code"] in ("", "ALL"):
        filters["category_code"] = None

    categories = web_repository.get_categories()
    filter_options = web_repository.get_filter_options(
        filters["category_code"]
    )

    filter_options_by_category = {}

    if filters["category_code"] is None:
        filter_options_by_category = {
            category["category_code"]: web_repository.get_filter_options(
                category["category_code"]
            )
            for category in categories
        }

    page = max(
        request.args.get(
            "page",
            default=1,
            type=int,
        ),
        1,
    )

    per_page = request.args.get(
        "per_page",
        default=20,
        type=int,
    )

    if per_page not in (20, 40, 60):
        per_page = 20

    product_query = {
        "category_code": filters["category_code"],
        "keyword": filters["keyword"] or None,
        "brand_name": filters["brand_name"] or None,
        "socket": filters["socket"] or None,
        "memory_type": filters["memory_type"] or None,
        "capacity_gb": filters["capacity_gb"],
        "vram_gb": filters["vram_gb"],
        "chipset": filters["chipset"] or None,
        "interface": filters["interface"] or None,
        "pcie_generation": filters["pcie_generation"] or None,
        "form_factor": filters["form_factor"] or None,
        "speed_mts": filters["speed_mts"],
        "model_family": filters["model_family"] or None,
        "model_name": filters["model_name"] or None,
    }

    total_count = web_repository.get_product_count(
        **product_query
    )

    total_pages = max(
        1,
        ceil(total_count / per_page),
    )

    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    products = web_repository.get_products(
        **product_query,
        limit=per_page,
        offset=offset,
    )

    base_args = request.args.to_dict(
        flat=True
    )
    base_args.pop("page", None)
    base_args.pop("per_page", None)

    page_group_size = 5
    group_start = (
        ((page - 1) // page_group_size)
        * page_group_size
        + 1
    )
    group_end = min(
        group_start + page_group_size - 1,
        total_pages,
    )

    page_links = [
        {
            "number": page_number,
            "url": url_for(
                "product_list",
                **base_args,
                page=page_number,
                per_page=per_page,
            ),
        }
        for page_number in range(
            group_start,
            group_end + 1,
        )
    ]

    previous_group_page = (
        max(
            1,
            group_start - page_group_size,
        )
        if group_start > 1
        else None
    )

    next_group_page = (
        group_end + 1
        if group_end < total_pages
        else None
    )

    per_page_urls = {
        size: url_for(
            "product_list",
            **base_args,
            page=1,
            per_page=size,
        )
        for size in (20, 40, 60)
    }

    pagination = {
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "group_start": group_start,
        "group_end": group_end,
        "page_links": page_links,
        "first_url": (
            url_for(
                "product_list",
                **base_args,
                page=1,
                per_page=per_page,
            )
            if page > 1
            else None
        ),
        "last_url": (
            url_for(
                "product_list",
                **base_args,
                page=total_pages,
                per_page=per_page,
            )
            if page < total_pages
            else None
        ),
        "previous_url": (
            url_for(
                "product_list",
                **base_args,
                page=page - 1,
                per_page=per_page,
            )
            if page > 1
            else None
        ),
        "next_url": (
            url_for(
                "product_list",
                **base_args,
                page=page + 1,
                per_page=per_page,
            )
            if page < total_pages
            else None
        ),
        "previous_group_url": (
            url_for(
                "product_list",
                **base_args,
                page=previous_group_page,
                per_page=per_page,
            )
            if previous_group_page is not None
            else None
        ),
        "next_group_url": (
            url_for(
                "product_list",
                **base_args,
                page=next_group_page,
                per_page=per_page,
            )
            if next_group_page is not None
            else None
        ),
        "per_page_urls": per_page_urls,
    }

    return render_template(
        "products.html",
        categories=categories,
        products=products,
        filters=filters,
        filter_options=filter_options,
        filter_options_by_category=filter_options_by_category,
        pagination=pagination,
    )


# ==========================================================
# 상품 상세
# - 가격 이력 그래프
# - 스펙
# - 판매처별 가격
# - CPU / RAM 호환 메인보드
# ==========================================================
@app.get("/product/<int:product_id>")
def product_detail(product_id):
    product = web_repository.get_product_detail(product_id)

    if product is None:
        abort(404)

    categories = web_repository.get_categories()
    filter_options = web_repository.get_filter_options(
        product["category_code"]
    )
    offers = web_repository.get_product_offers(product_id)
    price_statistics = price_repository.get_price_statistics(
        product_id,
        recent_days=7,
    )
    daily_prices = price_repository.get_daily_min_prices(product_id)

    compatibility = None

    if product["category_code"] == "CPU":
        result = compatibility_repository.get_compatible_motherboards_for_cpu(
            product_id
        )

        if result is not None:
            compatibility = {
                "title": "CPU 소켓 기준 호환 메인보드",
                "criteria": f'소켓 {result["cpu"]["socket"]} 일치',
                "motherboards": result["motherboards"],
            }

    elif product["category_code"] == "RAM":
        result = compatibility_repository.get_compatible_motherboards_for_ram(
            product_id
        )

        if result is not None:
            compatibility = {
                "title": "RAM 규격 기준 호환 메인보드",
                "criteria": f'메모리 타입 {result["ram"]["memory_type"]} 일치',
                "motherboards": result["motherboards"],
            }

    elif product["category_code"] == "MOTHERBOARD":
        result = (
            compatibility_repository
            .get_compatible_components_for_motherboard(
                product_id
            )
        )

        if result is not None:
            compatibility = {
                "title": "메인보드 기준 호환 부품",
                "criteria": (
                    f'소켓 {result["motherboard"]["socket"]}'
                    f' · 메모리 {result["motherboard"]["memory_type"]}'
                ),
                "cpus": result["cpus"],
                "rams": result["rams"],
            }

    return render_template(
        "product_detail.html",
        categories=categories,
        product=product,
        offers=offers,
        price_statistics=price_statistics,
        daily_prices=daily_prices,
        compatibility=compatibility,
        filter_options=filter_options,
    )


@app.errorhandler(404)
def not_found(_error):
    return (
        render_template(
            "404.html",
        ),
        404,
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
