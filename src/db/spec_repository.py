"""GPU/CPU/RAM/SSD/MOTHERBOARD 모델·스펙 테이블 저장 기능."""

class SpecRepositoryMixin:
    """부품별 모델/스펙 테이블 공통 저장 기능."""

    @staticmethod
    # ======================================================
    # GPU MODEL / SPEC
    # ======================================================
    def upsert_gpu_model(cur, vendor_brand_id: int, family: str, model_name: str) -> int:
        cur.execute(
            """
            INSERT INTO gpu_model (vendor_brand_id, family, model_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (vendor_brand_id, model_name)
            DO UPDATE SET family = EXCLUDED.family
            RETURNING gpu_model_id;
            """,
            (vendor_brand_id, family, model_name),
        )
        return cur.fetchone()[0]

    @staticmethod
    def upsert_gpu_spec(
        cur,
        product_id: int,
        gpu_model_id: int,
        vram_gb,
        memory_type,
    ) -> None:
        cur.execute(
            """
            INSERT INTO gpu_spec (product_id, gpu_model_id, vram_gb, memory_type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_id)
            DO UPDATE SET
                gpu_model_id = EXCLUDED.gpu_model_id,
                vram_gb = EXCLUDED.vram_gb,
                memory_type = EXCLUDED.memory_type;
            """,
            (product_id, gpu_model_id, vram_gb, memory_type),
        )

    @staticmethod
    # ======================================================
    # CPU MODEL / SPEC
    # ======================================================
    def upsert_cpu_model(
        cur,
        vendor_brand_id: int,
        family: str,
        model_name: str,
        generation=None,
        tier=None,
        suffix=None,
    ) -> int:
        cur.execute(
            """
            INSERT INTO cpu_model (
                vendor_brand_id,
                family,
                generation,
                tier,
                model_name,
                suffix
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (vendor_brand_id, model_name)
            DO UPDATE SET
                family = EXCLUDED.family,
                generation = COALESCE(EXCLUDED.generation, cpu_model.generation),
                tier = COALESCE(EXCLUDED.tier, cpu_model.tier),
                suffix = COALESCE(EXCLUDED.suffix, cpu_model.suffix)
            RETURNING cpu_model_id;
            """,
            (vendor_brand_id, family, generation, tier, model_name, suffix),
        )
        return cur.fetchone()[0]

    @staticmethod
    def upsert_cpu_spec(
        cur,
        product_id: int,
        cpu_model_id: int,
        socket,
        cores,
        threads,
        base_clock_ghz,
        boost_clock_ghz,
    ) -> None:
        cur.execute(
            """
            INSERT INTO cpu_spec (
                product_id,
                cpu_model_id,
                socket,
                cores,
                threads,
                base_clock_ghz,
                boost_clock_ghz
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id)
            DO UPDATE SET
                cpu_model_id = EXCLUDED.cpu_model_id,
                socket = EXCLUDED.socket,
                cores = EXCLUDED.cores,
                threads = EXCLUDED.threads,
                base_clock_ghz = EXCLUDED.base_clock_ghz,
                boost_clock_ghz = EXCLUDED.boost_clock_ghz;
            """,
            (
                product_id,
                cpu_model_id,
                socket,
                cores,
                threads,
                base_clock_ghz,
                boost_clock_ghz,
            ),
        )

    @staticmethod
    # ======================================================
    # RAM SPEC
    # ======================================================
    def upsert_ram_spec(
        cur,
        product_id: int,
        capacity_gb,
        memory_type,
        speed_mts,
        module_count,
    ) -> None:
        cur.execute(
            """
            INSERT INTO ram_spec (
                product_id,
                capacity_gb,
                memory_type,
                speed_mts,
                module_count
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (product_id)
            DO UPDATE SET
                capacity_gb = EXCLUDED.capacity_gb,
                memory_type = EXCLUDED.memory_type,
                speed_mts = EXCLUDED.speed_mts,
                module_count = EXCLUDED.module_count;
            """,
            (product_id, capacity_gb, memory_type, speed_mts, module_count),
        )

    @staticmethod
    # ======================================================
    # SSD SPEC
    # ======================================================
    def upsert_ssd_spec(
        cur,
        product_id: int,
        capacity_gb,
        interface,
        pcie_generation,
        form_factor,
        read_speed_mbps,
        write_speed_mbps,
    ) -> None:
        cur.execute(
            """
            INSERT INTO ssd_spec (
                product_id,
                capacity_gb,
                interface,
                pcie_generation,
                form_factor,
                read_speed_mbps,
                write_speed_mbps
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id)
            DO UPDATE SET
                capacity_gb = EXCLUDED.capacity_gb,
                interface = EXCLUDED.interface,
                pcie_generation = EXCLUDED.pcie_generation,
                form_factor = EXCLUDED.form_factor,
                read_speed_mbps = EXCLUDED.read_speed_mbps,
                write_speed_mbps = EXCLUDED.write_speed_mbps;
            """,
            (
                product_id,
                capacity_gb,
                interface,
                pcie_generation,
                form_factor,
                read_speed_mbps,
                write_speed_mbps,
            ),
        )

    @staticmethod
    # ======================================================
    # MOTHERBOARD SPEC
    # ======================================================
    def upsert_motherboard_spec(
        cur,
        product_id: int,
        socket,
        chipset,
        memory_type,
        form_factor,
    ) -> None:
        cur.execute(
            """
            INSERT INTO motherboard_spec (
                product_id,
                socket,
                chipset,
                memory_type,
                form_factor
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (product_id)
            DO UPDATE SET
                socket = EXCLUDED.socket,
                chipset = EXCLUDED.chipset,
                memory_type = EXCLUDED.memory_type,
                form_factor = EXCLUDED.form_factor;
            """,
            (product_id, socket, chipset, memory_type, form_factor),
        )
