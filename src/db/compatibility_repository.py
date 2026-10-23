"""PC 부품의 기본 호환성을 조회하는 Repository."""

from src.db.connection import get_connection


class CompatibilityRepository:
    """현재 프로젝트 범위의 기본 호환성을 조회한다.

    기준:
    - CPU ↔ 메인보드: socket 일치
    - RAM ↔ 메인보드: memory_type 일치
    - 메인보드 → CPU: socket 일치
    - 메인보드 → RAM: memory_type 일치
    """

    # ======================================================
    # CPU → MOTHERBOARD
    # socket 일치
    # ======================================================
    def get_compatible_motherboards_for_cpu(
        self,
        cpu_product_id: int,
    ):
        conn = get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        p.product_id,
                        p.product_name,
                        b.brand_name,
                        cs.socket
                    FROM product p
                    JOIN brand b
                        ON p.brand_id = b.brand_id
                    JOIN cpu_spec cs
                        ON p.product_id = cs.product_id
                    WHERE p.product_id = %s;
                    """,
                    (cpu_product_id,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                cpu = {
                    "product_id": row[0],
                    "product_name": row[1],
                    "brand_name": row[2],
                    "socket": row[3],
                }

                return {
                    "cpu": cpu,
                    "motherboards": self._find_motherboards(
                        cur,
                        "socket",
                        cpu["socket"],
                    ),
                }

        finally:
            conn.close()

    # ======================================================
    # RAM → MOTHERBOARD
    # memory_type 일치
    # ======================================================
    def get_compatible_motherboards_for_ram(
        self,
        ram_product_id: int,
    ):
        conn = get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        p.product_id,
                        p.product_name,
                        b.brand_name,
                        rs.capacity_gb,
                        rs.memory_type,
                        rs.speed_mts,
                        rs.module_count
                    FROM product p
                    JOIN brand b
                        ON p.brand_id = b.brand_id
                    JOIN ram_spec rs
                        ON p.product_id = rs.product_id
                    WHERE p.product_id = %s;
                    """,
                    (ram_product_id,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                ram = {
                    "product_id": row[0],
                    "product_name": row[1],
                    "brand_name": row[2],
                    "capacity_gb": row[3],
                    "memory_type": row[4],
                    "speed_mts": row[5],
                    "module_count": row[6],
                }

                return {
                    "ram": ram,
                    "motherboards": self._find_motherboards(
                        cur,
                        "memory_type",
                        ram["memory_type"],
                    ),
                }

        finally:
            conn.close()

    # ======================================================
    # MOTHERBOARD → CPU + RAM
    # socket / memory_type 기준 역방향 조회
    # ======================================================
    def get_compatible_components_for_motherboard(
        self,
        motherboard_product_id: int,
    ):
        conn = get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        p.product_id,
                        p.product_name,
                        b.brand_name,
                        ms.socket,
                        ms.chipset,
                        ms.memory_type,
                        ms.form_factor
                    FROM product p
                    JOIN brand b
                        ON p.brand_id = b.brand_id
                    JOIN motherboard_spec ms
                        ON p.product_id = ms.product_id
                    WHERE p.product_id = %s;
                    """,
                    (motherboard_product_id,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                motherboard = {
                    "product_id": row[0],
                    "product_name": row[1],
                    "brand_name": row[2],
                    "socket": row[3],
                    "chipset": row[4],
                    "memory_type": row[5],
                    "form_factor": row[6],
                }

                cpus = self._find_cpus(
                    cur,
                    motherboard["socket"],
                )

                rams = self._find_rams(
                    cur,
                    motherboard["memory_type"],
                )

                return {
                    "motherboard": motherboard,
                    "cpus": cpus,
                    "rams": rams,
                }

        finally:
            conn.close()

    # ======================================================
    # 내부 조회: 호환 메인보드
    # ======================================================
    @staticmethod
    def _find_motherboards(
        cur,
        field: str,
        value: str,
    ):
        if field not in {
            "socket",
            "memory_type",
        }:
            raise ValueError(
                f"지원하지 않는 호환성 필드입니다: {field}"
            )

        cur.execute(
            f"""
            SELECT
                p.product_id,
                p.product_name,
                b.brand_name,
                ms.socket,
                ms.chipset,
                ms.memory_type,
                ms.form_factor
            FROM motherboard_spec ms
            JOIN product p
                ON ms.product_id = p.product_id
            JOIN brand b
                ON p.brand_id = b.brand_id
            WHERE UPPER(TRIM(ms.{field}))
                = UPPER(TRIM(%s))
            ORDER BY
                b.brand_name,
                p.product_name;
            """,
            (value,),
        )

        return [
            {
                "product_id": row[0],
                "product_name": row[1],
                "brand_name": row[2],
                "socket": row[3],
                "chipset": row[4],
                "memory_type": row[5],
                "form_factor": row[6],
            }
            for row in cur.fetchall()
        ]

    # ======================================================
    # 내부 조회: 메인보드와 같은 socket의 CPU
    # ======================================================
    @staticmethod
    def _find_cpus(
        cur,
        socket: str,
    ):
        cur.execute(
            """
            SELECT
                p.product_id,
                p.product_name,
                b.brand_name,
                cs.socket,
                cs.cores,
                cs.threads,
                cs.base_clock_ghz,
                cs.boost_clock_ghz
            FROM cpu_spec cs
            JOIN product p
                ON cs.product_id = p.product_id
            JOIN brand b
                ON p.brand_id = b.brand_id
            WHERE UPPER(TRIM(cs.socket))
                = UPPER(TRIM(%s))
            ORDER BY
                b.brand_name,
                p.product_name;
            """,
            (socket,),
        )

        return [
            {
                "product_id": row[0],
                "product_name": row[1],
                "brand_name": row[2],
                "socket": row[3],
                "cores": row[4],
                "threads": row[5],
                "base_clock_ghz": (
                    float(row[6])
                    if row[6] is not None
                    else None
                ),
                "boost_clock_ghz": (
                    float(row[7])
                    if row[7] is not None
                    else None
                ),
            }
            for row in cur.fetchall()
        ]

    # ======================================================
    # 내부 조회: 메인보드와 같은 memory_type의 RAM
    # ======================================================
    @staticmethod
    def _find_rams(
        cur,
        memory_type: str,
    ):
        cur.execute(
            """
            SELECT
                p.product_id,
                p.product_name,
                b.brand_name,
                rs.capacity_gb,
                rs.memory_type,
                rs.speed_mts,
                rs.module_count
            FROM ram_spec rs
            JOIN product p
                ON rs.product_id = p.product_id
            JOIN brand b
                ON p.brand_id = b.brand_id
            WHERE UPPER(TRIM(rs.memory_type))
                = UPPER(TRIM(%s))
            ORDER BY
                rs.capacity_gb,
                rs.speed_mts,
                b.brand_name,
                p.product_name;
            """,
            (memory_type,),
        )

        return [
            {
                "product_id": row[0],
                "product_name": row[1],
                "brand_name": row[2],
                "capacity_gb": row[3],
                "memory_type": row[4],
                "speed_mts": row[5],
                "module_count": row[6],
            }
            for row in cur.fetchall()
        ]
