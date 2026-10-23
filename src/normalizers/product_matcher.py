"""서로 다른 쇼핑몰의 동일 상품을 같은 PRODUCT로 연결하기 위한 Matcher."""

import re
from typing import Optional

from src.normalizers.product_normalizer import normalize_product_name


def normalize_brand_name(brand_name: str) -> str:
    return normalize_product_name(brand_name) if brand_name else ""


def remove_leading_brand(text: str, brand_name: str) -> str:
    """상품명 앞의 `[브랜드]` 또는 일반 브랜드 표기를 제거한다."""
    if not text:
        return ""

    result = text.strip()
    if not brand_name:
        return result

    escaped_brand = re.escape(brand_name)
    result = re.sub(
        rf"^\[\s*{escaped_brand}\s*\]\s*", "", result, flags=re.IGNORECASE
    )
    result = re.sub(
        rf"^{escaped_brand}\s+", "", result, count=1, flags=re.IGNORECASE
    )
    return result.strip()


def clean_motherboard_name(text: str, brand_name: str) -> str:
    """메인보드명에서 쇼핑몰별 부가 문구를 제거한다."""
    result = remove_leading_brand(text, brand_name)
    result = re.sub(r"\([^)]*\)", " ", result)
    result = re.sub(r"\[[^\]]*\]", " ", result)

    for noise in ("정품 박스", "정품박스", "정품 BOX", "정품BOX"):
        result = re.sub(re.escape(noise), " ", result, flags=re.IGNORECASE)

    return normalize_product_name(" ".join(result.split()))


def make_product_match_key(
    category_code: str,
    brand_name: str,
    product_name: str,
    model_name: Optional[str] = None,
) -> Optional[str]:
    """검증된 카테고리에 대해서만 동일상품 매칭 키를 만든다."""
    category_code = category_code.strip().upper()

    if category_code != "MOTHERBOARD":
        return None

    brand_key = normalize_brand_name(brand_name)
    source_text = model_name or product_name
    model_key = clean_motherboard_name(source_text, brand_name)

    if not brand_key or not model_key:
        return None

    return f"{brand_key}|{model_key}"


def find_matching_product_id(
    cur,
    category_id: int,
    brand_id: int,
    category_code: str,
    brand_name: str,
    product_name: str,
    model_name: Optional[str] = None,
) -> Optional[int]:
    """같은 카테고리/브랜드 안에서 동일한 기준 상품을 찾는다."""
    target_key = make_product_match_key(
        category_code=category_code,
        brand_name=brand_name,
        product_name=product_name,
        model_name=model_name,
    )
    if target_key is None:
        return None

    cur.execute(
        """
        SELECT product_id, product_name, model_name
        FROM product
        WHERE category_id = %s
          AND brand_id = %s
        ORDER BY product_id;
        """,
        (category_id, brand_id),
    )

    for product_id, existing_name, existing_model_name in cur.fetchall():
        existing_key = make_product_match_key(
            category_code=category_code,
            brand_name=brand_name,
            product_name=existing_name,
            model_name=existing_model_name,
        )
        if existing_key == target_key:
            return product_id

    return None
