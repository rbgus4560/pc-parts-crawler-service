"""다나와 크롤링 결과와 판매처 Offer를 전달하는 데이터 모델."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DanawaOffer:
    """다나와 가격비교 판매처 한 건."""

    retailer: str
    source_offer_id: str
    price: int
    product_url: str


@dataclass
class DanawaGpuProduct:
    seller: str
    category: str
    pcode: str
    product_name: str
    brand: Optional[str]
    product_url: str
    image_url: Optional[str]
    model_name: Optional[str]
    vram_gb: Optional[int]
    memory_type: Optional[str]
    raw_spec_text: Optional[str]
    offers: List[DanawaOffer]


@dataclass
class DanawaCpuProduct:
    seller: str
    category: str
    pcode: str
    product_name: str
    brand: Optional[str]
    product_url: str
    image_url: Optional[str]
    model_name: Optional[str]
    family: Optional[str]
    generation: Optional[str]
    tier: Optional[str]
    suffix: Optional[str]
    socket: Optional[str]
    cores: Optional[int]
    threads: Optional[int]
    base_clock_ghz: Optional[float]
    boost_clock_ghz: Optional[float]
    raw_spec_text: Optional[str]
    offers: List[DanawaOffer]


@dataclass
class DanawaRamProduct:
    seller: str
    category: str
    pcode: str
    product_name: str
    brand: Optional[str]
    product_url: str
    image_url: Optional[str]
    capacity_gb: Optional[int]
    memory_type: Optional[str]
    speed_mts: Optional[int]
    module_count: Optional[int]
    raw_spec_text: Optional[str]
    offers: List[DanawaOffer]


@dataclass
class DanawaSsdProduct:
    seller: str
    category: str
    pcode: str
    product_name: str
    brand: Optional[str]
    product_url: str
    image_url: Optional[str]
    capacity_gb: Optional[int]
    interface: Optional[str]
    pcie_generation: Optional[str]
    form_factor: Optional[str]
    read_speed_mbps: Optional[int]
    write_speed_mbps: Optional[int]
    raw_spec_text: Optional[str]
    offers: List[DanawaOffer]


@dataclass
class DanawaMotherboardProduct:
    seller: str
    category: str
    pcode: str
    product_name: str
    brand: Optional[str]
    product_url: str
    image_url: Optional[str]
    socket: Optional[str]
    chipset: Optional[str]
    memory_type: Optional[str]
    form_factor: Optional[str]
    raw_spec_text: Optional[str]
    offers: List[DanawaOffer]
