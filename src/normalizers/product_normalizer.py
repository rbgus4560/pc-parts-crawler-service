"""상품명/모델명 비교에 사용하는 문자열 정규화 함수."""

import re


def normalize_product_name(name: str) -> str:
    """기존 상품 비교용 문자열을 만든다."""
    name = name.upper()
    name = re.sub(r"\[[^\]]+\]", "", name)
    return re.sub(r"[^A-Z0-9가-힣]", "", name)


def normalize_ram_product_name(
    name: str,
    capacity_gb: int,
    memory_type: str,
    speed_mts: int = None,
    module_count: int = None,
) -> str:
    """RAM 용량/규격이 다른 상품이 하나로 합쳐지지 않도록 식별키를 만든다."""
    base = normalize_product_name(name)
    memory = re.sub(r"[^A-Z0-9]", "", (memory_type or "").upper())
    speed = speed_mts if speed_mts is not None else 0
    modules = module_count if module_count is not None else 0

    return (
        f"{base}"
        f"|CAP{capacity_gb}"
        f"|TYPE{memory}"
        f"|SPEED{speed}"
        f"|MODULE{modules}"
    )


def normalize_ssd_product_name(
    name: str,
    capacity_gb: int,
    interface: str = None,
    pcie_generation: str = None,
    form_factor: str = None,
) -> str:
    """SSD 용량/규격이 다른 상품이 하나로 합쳐지지 않도록 식별키를 만든다."""
    base = normalize_product_name(name)
    interface_key = re.sub(r"[^A-Z0-9]", "", (interface or "").upper())
    pcie_key = re.sub(r"[^A-Z0-9]", "", (pcie_generation or "").upper())
    form_key = re.sub(r"[^A-Z0-9]", "", (form_factor or "").upper())

    return (
        f"{base}"
        f"|CAP{capacity_gb}"
        f"|IF{interface_key}"
        f"|PCIE{pcie_key}"
        f"|FORM{form_key}"
    )


def get_gpu_vendor(model_name: str) -> str:
    """GPU 모델명으로 칩셋 제조사를 판별한다."""
    model = model_name.upper().replace(" ", "")

    if model.startswith("RX"):
        return "AMD"
    if model.startswith(("RTX", "GTX")):
        return "NVIDIA"
    if model.startswith("ARC"):
        return "Intel"

    raise ValueError(f"알 수 없는 GPU 모델입니다: {model_name}")


def get_gpu_family(model_name: str) -> str:
    model = model_name.upper().replace(" ", "")

    if model.startswith("RX"):
        return "Radeon RX"
    if model.startswith("RTX"):
        return "GeForce RTX"
    if model.startswith("GTX"):
        return "GeForce GTX"
    if model.startswith("ARC"):
        return "Arc"

    return "UNKNOWN"
