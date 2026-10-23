"""다나와 크롤링 결과를 PostgreSQL에 저장하는 Repository."""

from src.db.base_repository import BaseRepository
from src.db.connection import get_connection
from src.db.spec_repository import SpecRepositoryMixin
from src.normalizers.product_matcher import find_matching_product_id
from src.normalizers.product_normalizer import (
    get_gpu_family,
    get_gpu_vendor,
    normalize_product_name,
    normalize_ram_product_name,
    normalize_ssd_product_name,
)


class DanawaRepository(BaseRepository, SpecRepositoryMixin):
    """다나와 상품과 판매처별 Offer를 저장한다."""

    SITE_URL = "https://www.danawa.com"
    CRAWL_TYPE = "DYNAMIC"

    # ======================================================
    # 다나와 공통 저장 로직
    # ======================================================
    def _prepare_common(self, cur, product):
        category_id = self.get_or_create_category(cur, product.category)
        brand_id = self.get_or_create_brand(cur, product.brand)
        seller_id = self.get_or_create_seller(
            cur, product.seller, self.SITE_URL, self.CRAWL_TYPE
        )
        return category_id, brand_id, seller_id

    def _model_name(self, product) -> str:
        return self.strip_leading_brand(product.product_name, product.brand)

    def _normalized_name(self, product) -> str:
        return normalize_product_name(self._model_name(product))

    def _save_product(
        self,
        cur,
        product,
        category_id: int,
        brand_id: int,
        model_name: str,
        normalized_name: str = None,
    ):
        if normalized_name is None:
            normalized_name = self._normalized_name(product)

        return self.upsert_product(
            cur,
            category_id=category_id,
            brand_id=brand_id,
            product_name=product.product_name,
            model_name=model_name,
            normalized_name=normalized_name,
            image_url=product.image_url,
        )

    def _save_current_offers(self, cur, product, product_id: int, seller_id: int) -> int:
        self.deactivate_existing_offers(cur, product_id, seller_id)
        saved_count = 0

        for offer in product.offers:
            if (
                not offer.retailer
                or not offer.source_offer_id
                or not offer.product_url
                or offer.price <= 0
            ):
                continue

            retailer_id = self.get_or_create_retailer(cur, offer.retailer)
            offer_id = self.save_offer(
                cur,
                product_id=product_id,
                seller_id=seller_id,
                retailer_id=retailer_id,
                source_product_id=offer.source_offer_id,
                raw_product_name=product.product_name,
                product_url=offer.product_url,
            )
            self.save_price(cur, offer_id, offer.price)
            saved_count += 1

        return saved_count

    # ======================================================
    # GPU 저장
    # ======================================================
    def save_gpu_product(self, product):
        if not product.brand:
            raise ValueError("GPU brand가 없습니다.")
        if not product.model_name:
            raise ValueError("GPU model_name이 없습니다.")
        if not product.offers:
            raise ValueError("다나와 판매처 정보가 없습니다.")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                category_id, brand_id, seller_id = self._prepare_common(cur, product)
                product_id = self._save_product(
                    cur, product, category_id, brand_id, product.model_name
                )

                gpu_vendor_id = self.get_or_create_brand(
                    cur, get_gpu_vendor(product.model_name)
                )
                gpu_model_id = self.upsert_gpu_model(
                    cur,
                    vendor_brand_id=gpu_vendor_id,
                    family=get_gpu_family(product.model_name),
                    model_name=product.model_name,
                )
                self.upsert_gpu_spec(
                    cur,
                    product_id=product_id,
                    gpu_model_id=gpu_model_id,
                    vram_gb=product.vram_gb,
                    memory_type=product.memory_type,
                )
                saved_count = self._save_current_offers(
                    cur, product, product_id, seller_id
                )

            conn.commit()
            return product_id, saved_count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ======================================================
    # CPU 저장
    # ======================================================
    def save_cpu_product(self, product):
        if not product.brand:
            raise ValueError("CPU brand가 없습니다.")
        if not product.model_name:
            raise ValueError("CPU model_name이 없습니다.")
        if not product.family:
            raise ValueError("CPU family가 없습니다.")
        if not product.socket:
            raise ValueError("CPU socket이 없습니다.")
        if not product.offers:
            raise ValueError("다나와 판매처 정보가 없습니다.")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                category_id, brand_id, seller_id = self._prepare_common(cur, product)
                product_id = self._save_product(
                    cur, product, category_id, brand_id, product.model_name
                )
                cpu_model_id = self.upsert_cpu_model(
                    cur,
                    vendor_brand_id=brand_id,
                    family=product.family,
                    generation=product.generation,
                    tier=product.tier,
                    model_name=product.model_name,
                    suffix=product.suffix,
                )
                self.upsert_cpu_spec(
                    cur,
                    product_id=product_id,
                    cpu_model_id=cpu_model_id,
                    socket=product.socket,
                    cores=product.cores,
                    threads=product.threads,
                    base_clock_ghz=product.base_clock_ghz,
                    boost_clock_ghz=product.boost_clock_ghz,
                )
                saved_count = self._save_current_offers(
                    cur, product, product_id, seller_id
                )

            conn.commit()
            return product_id, saved_count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ======================================================
    # RAM 저장
    # ======================================================
    def save_ram_product(self, product):
        if not product.brand:
            raise ValueError("RAM brand가 없습니다.")
        if product.capacity_gb is None:
            raise ValueError("RAM capacity_gb가 없습니다.")
        if not product.memory_type:
            raise ValueError("RAM memory_type이 없습니다.")
        if not product.offers:
            raise ValueError("다나와 판매처 정보가 없습니다.")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                category_id, brand_id, seller_id = self._prepare_common(cur, product)
                model_name = self._model_name(product)
                normalized_name = normalize_ram_product_name(
                    model_name,
                    product.capacity_gb,
                    product.memory_type,
                    product.speed_mts,
                    product.module_count,
                )
                product_id = self._save_product(
                    cur,
                    product,
                    category_id,
                    brand_id,
                    model_name,
                    normalized_name=normalized_name,
                )
                self.upsert_ram_spec(
                    cur,
                    product_id=product_id,
                    capacity_gb=product.capacity_gb,
                    memory_type=product.memory_type,
                    speed_mts=product.speed_mts,
                    module_count=product.module_count,
                )
                saved_count = self._save_current_offers(
                    cur, product, product_id, seller_id
                )

            conn.commit()
            return product_id, saved_count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ======================================================
    # SSD 저장
    # ======================================================
    def save_ssd_product(self, product):
        if not product.brand:
            raise ValueError("SSD brand가 없습니다.")
        if product.capacity_gb is None:
            raise ValueError("SSD capacity_gb가 없습니다.")
        if not product.offers:
            raise ValueError("다나와 판매처 정보가 없습니다.")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                category_id, brand_id, seller_id = self._prepare_common(cur, product)
                model_name = self._model_name(product)
                normalized_name = normalize_ssd_product_name(
                    model_name,
                    product.capacity_gb,
                    product.interface,
                    product.pcie_generation,
                    product.form_factor,
                )
                product_id = self._save_product(
                    cur,
                    product,
                    category_id,
                    brand_id,
                    model_name,
                    normalized_name=normalized_name,
                )
                self.upsert_ssd_spec(
                    cur,
                    product_id=product_id,
                    capacity_gb=product.capacity_gb,
                    interface=product.interface,
                    pcie_generation=product.pcie_generation,
                    form_factor=product.form_factor,
                    read_speed_mbps=product.read_speed_mbps,
                    write_speed_mbps=product.write_speed_mbps,
                )
                saved_count = self._save_current_offers(
                    cur, product, product_id, seller_id
                )

            conn.commit()
            return product_id, saved_count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ======================================================
    # MOTHERBOARD 저장
    # ======================================================
    def save_motherboard_product(self, product):
        if not product.brand:
            raise ValueError("MOTHERBOARD brand가 없습니다.")
        if not product.socket:
            raise ValueError("MOTHERBOARD socket이 없습니다.")
        if not product.chipset:
            raise ValueError("MOTHERBOARD chipset이 없습니다.")
        if not product.memory_type:
            raise ValueError("MOTHERBOARD memory_type이 없습니다.")
        if not product.offers:
            raise ValueError("다나와 판매처 정보가 없습니다.")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                category_id, brand_id, seller_id = self._prepare_common(cur, product)
                model_name = self._model_name(product)
                matched_product_id = find_matching_product_id(
                    cur=cur,
                    category_id=category_id,
                    brand_id=brand_id,
                    category_code=product.category,
                    brand_name=product.brand,
                    product_name=product.product_name,
                    model_name=model_name,
                )

                if matched_product_id is not None:
                    product_id = matched_product_id
                    self.fill_product_image(cur, product_id, product.image_url)
                else:
                    product_id = self._save_product(
                        cur, product, category_id, brand_id, model_name
                    )

                self.upsert_motherboard_spec(
                    cur,
                    product_id=product_id,
                    socket=product.socket,
                    chipset=product.chipset,
                    memory_type=product.memory_type,
                    form_factor=product.form_factor,
                )
                saved_count = self._save_current_offers(
                    cur, product, product_id, seller_id
                )

            conn.commit()
            return product_id, saved_count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
