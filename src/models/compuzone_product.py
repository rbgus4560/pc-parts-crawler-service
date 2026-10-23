"""컴퓨존 크롤링 결과 데이터 모델.

크롤러 → Repository 사이에서 GPU/CPU/RAM/SSD/MOTHERBOARD 데이터를 전달한다.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CrawledProduct:
    """컴퓨존 GPU 크롤링 결과."""

    seller: str
    retailer: str
    category: str
    source_product_id: str
    product_name: str
    brand: Optional[str]
    price: int
    product_url: str
    image_url: Optional[str]
    model_name: Optional[str]
    vram_gb: Optional[int]
    memory_type: Optional[str]
    raw_spec_text: Optional[str]


@dataclass
class CpuCrawledProduct:
    """컴퓨존 CPU 크롤링 결과."""

    seller: str
    retailer: str
    category: str
    source_product_id: str
    product_name: str
    brand: Optional[str]
    price: int
    product_url: str
    image_url: Optional[str]
    model_name: Optional[str]
    socket: Optional[str]
    cores: Optional[int]
    threads: Optional[int]
    base_clock_ghz: Optional[float]
    boost_clock_ghz: Optional[float]
    raw_spec_text: Optional[str]


@dataclass
class RamCrawledProduct:
    """컴퓨존 RAM 크롤링 결과."""

    seller: str
    retailer: str
    category: str
    source_product_id: str
    product_name: str
    brand: Optional[str]
    price: int
    product_url: str
    image_url: Optional[str]
    capacity_gb: Optional[int]
    memory_type: Optional[str]
    speed_mts: Optional[int]
    module_count: Optional[int]
    raw_spec_text: Optional[str]


@dataclass
class SsdCrawledProduct:
    """컴퓨존 SSD 크롤링 결과."""

    seller: str
    retailer: str
    category: str
    source_product_id: str
    product_name: str
    brand: Optional[str]
    price: int
    product_url: str
    image_url: Optional[str]
    capacity_gb: Optional[int]
    interface: Optional[str]
    pcie_generation: Optional[str]
    form_factor: Optional[str]
    read_speed_mbps: Optional[int]
    write_speed_mbps: Optional[int]
    raw_spec_text: Optional[str]


@dataclass
class MotherboardCrawledProduct:
    """컴퓨존 메인보드 크롤링 결과."""

    seller: str
    retailer: str
    category: str
    source_product_id: str
    product_name: str
    brand: Optional[str]
    price: int
    product_url: str
    image_url: Optional[str]
    socket: Optional[str]
    chipset: Optional[str]
    memory_type: Optional[str]
    form_factor: Optional[str]
    raw_spec_text: Optional[str]
