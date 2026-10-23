"""Flask 웹 화면에서 사용하는 상품 조회 Repository."""



from src.db.connection import get_connection





class WebRepository:

    """상품 목록, 상세 정보, 필터, 판매처 가격을 조회한다."""



    # ==========================================================

    # 카테고리

    # ==========================================================

    def get_categories(self):

        conn = get_connection()



        try:

            with conn.cursor() as cur:

                cur.execute(

                    """

                    SELECT

                        category_id,

                        category_code,

                        category_name

                    FROM category

                    ORDER BY category_id;

                    """

                )



                return [

                    {

                        "category_id": row[0],

                        "category_code": row[1],

                        "category_name": row[2],

                    }

                    for row in cur.fetchall()

                ]



        finally:

            conn.close()



    # ==========================================================

    # 목록 화면 필터 옵션

    # ==========================================================

    def get_filter_options(self, category_code=None):

        conn = get_connection()



        try:

            with conn.cursor() as cur:

                if category_code:

                    brands = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT b.brand_name

                        FROM product p

                        JOIN brand b

                            ON p.brand_id = b.brand_id

                        JOIN category c

                            ON p.category_id = c.category_id

                        WHERE c.category_code = %s

                        ORDER BY b.brand_name;

                        """,

                        (category_code,),

                    )

                else:

                    brands = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT b.brand_name

                        FROM product p

                        JOIN brand b

                            ON p.brand_id = b.brand_id

                        ORDER BY b.brand_name;

                        """,

                    )



                options = {

                    "brands": brands,

                    "sockets": [],

                    "memory_types": [],

                    "capacities": [],

                    "capacity_groups": [],

                    "vram_values": [],

                    "chipsets": [],

                    "interfaces": [],

                    "pcie_generations": [],

                    "form_factors": [],

                    "speeds": [],

                    "model_groups": [],

                }



                if category_code == "CPU":

                    options["sockets"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT socket

                        FROM cpu_spec

                        WHERE socket IS NOT NULL

                        ORDER BY socket;

                        """,

                    )

                    options["model_groups"] = self._fetch_model_groups(

                        cur,

                        category_code="CPU",

                    )



                elif category_code == "GPU":

                    options["memory_types"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT memory_type

                        FROM gpu_spec

                        WHERE memory_type IS NOT NULL

                        ORDER BY memory_type;

                        """,

                    )

                    options["vram_values"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT vram_gb

                        FROM gpu_spec

                        WHERE vram_gb IS NOT NULL

                        ORDER BY vram_gb;

                        """,

                    )

                    options["model_groups"] = self._fetch_model_groups(

                        cur,

                        category_code="GPU",

                    )



                elif category_code == "RAM":

                    options["memory_types"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT memory_type

                        FROM ram_spec

                        WHERE memory_type IS NOT NULL

                        ORDER BY memory_type;

                        """,

                    )

                    options["capacities"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT capacity_gb

                        FROM ram_spec

                        WHERE capacity_gb IS NOT NULL

                        ORDER BY capacity_gb;

                        """,

                    )

                    options["speeds"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT speed_mts

                        FROM ram_spec

                        WHERE speed_mts IS NOT NULL

                          AND speed_mts >= 2000

                        ORDER BY speed_mts;

                        """,

                    )



                elif category_code == "SSD":

                    options["capacities"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT capacity_gb

                        FROM ssd_spec

                        WHERE capacity_gb IS NOT NULL

                        ORDER BY capacity_gb;

                        """,

                    )

                    options["capacity_groups"] = self._build_ssd_capacity_groups(
                        options["capacities"]
                    )

                    options["interfaces"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT interface

                        FROM ssd_spec

                        WHERE interface IS NOT NULL

                        ORDER BY interface;

                        """,

                    )

                    options["pcie_generations"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT pcie_generation

                        FROM ssd_spec

                        WHERE pcie_generation IS NOT NULL

                        ORDER BY pcie_generation;

                        """,

                    )

                    options["form_factors"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT form_factor

                        FROM ssd_spec

                        WHERE form_factor IS NOT NULL

                        ORDER BY form_factor;

                        """,

                    )



                elif category_code == "MOTHERBOARD":

                    options["sockets"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT socket

                        FROM motherboard_spec

                        WHERE socket IS NOT NULL

                        ORDER BY socket;

                        """,

                    )

                    options["chipsets"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT chipset

                        FROM motherboard_spec

                        WHERE chipset IS NOT NULL

                        ORDER BY chipset;

                        """,

                    )

                    options["memory_types"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT memory_type

                        FROM motherboard_spec

                        WHERE memory_type IS NOT NULL

                        ORDER BY memory_type;

                        """,

                    )

                    options["form_factors"] = self._fetch_single_column(

                        cur,

                        """

                        SELECT DISTINCT form_factor

                        FROM motherboard_spec

                        WHERE form_factor IS NOT NULL

                        ORDER BY form_factor;

                        """,

                    )



                return options



        finally:

            conn.close()



    # ==========================================================

    # 상품 목록

    # ==========================================================

    def get_products(

        self,

        category_code=None,

        keyword=None,

        brand_name=None,

        socket=None,

        memory_type=None,

        capacity_gb=None,

        capacity_group=None,

        vram_gb=None,

        chipset=None,

        interface=None,

        pcie_generation=None,

        form_factor=None,

        speed_mts=None,

        model_family=None,

        model_name=None,

        limit=200,

        offset=0,

    ):

        conn = get_connection()



        try:

            with conn.cursor() as cur:

                conditions = []

                params = []



                if category_code:

                    conditions.append("c.category_code = %s")

                    params.append(category_code)



                if keyword:

                    conditions.append(

                        """

                        (

                            p.product_name ILIKE %s

                            OR p.model_name ILIKE %s

                            OR b.brand_name ILIKE %s

                        )

                        """

                    )

                    search_keyword = f"%{keyword}%"

                    params.extend(

                        [

                            search_keyword,

                            search_keyword,

                            search_keyword,

                        ]

                    )



                if brand_name:

                    conditions.append("b.brand_name = %s")

                    params.append(brand_name)



                if socket:

                    conditions.append(

                        """

                        (

                            cs.socket = %s

                            OR ms.socket = %s

                        )

                        """

                    )

                    params.extend([socket, socket])



                if memory_type:

                    conditions.append(

                        """

                        (

                            gs.memory_type = %s

                            OR rs.memory_type = %s

                            OR ms.memory_type = %s

                        )

                        """

                    )

                    params.extend(

                        [

                            memory_type,

                            memory_type,

                            memory_type,

                        ]

                    )



                if capacity_gb is not None:

                    conditions.append(

                        """

                        (

                            rs.capacity_gb = %s

                            OR ss.capacity_gb = %s

                        )

                        """

                    )

                    params.extend([capacity_gb, capacity_gb])



                if capacity_group:

                    capacity_values = self._ssd_capacity_values(
                        capacity_group
                    )

                    if capacity_values:
                        placeholders = ", ".join(
                            ["%s"] * len(capacity_values)
                        )
                        conditions.append(
                            f"ss.capacity_gb IN ({placeholders})"
                        )
                        params.extend(capacity_values)



                if vram_gb is not None:

                    conditions.append("gs.vram_gb = %s")

                    params.append(vram_gb)



                if chipset:

                    conditions.append("ms.chipset = %s")

                    params.append(chipset)



                if interface:

                    conditions.append("ss.interface = %s")

                    params.append(interface)



                if pcie_generation:

                    conditions.append("ss.pcie_generation = %s")

                    params.append(pcie_generation)



                if form_factor:

                    conditions.append(

                        """

                        (

                            ss.form_factor = %s

                            OR ms.form_factor = %s

                        )

                        """

                    )

                    params.extend([form_factor, form_factor])



                if speed_mts is not None:

                    conditions.append("rs.speed_mts = %s")

                    params.append(speed_mts)



                if model_family:

                    conditions.append(

                        """

                        (

                            cm.family = %s

                            OR gm.family = %s

                        )

                        """

                    )

                    params.extend([model_family, model_family])



                if model_name:

                    conditions.append(

                        """

                        (

                            TRIM(cm.model_name) = %s

                            OR TRIM(gm.model_name) = %s

                        )

                        """

                    )

                    params.extend([model_name, model_name])



                where_clause = ""



                if conditions:

                    where_clause = "WHERE " + " AND ".join(conditions)



                params.extend([limit, offset])



                cur.execute(

                    f"""

                    WITH latest_offer_price AS (

                        SELECT DISTINCT ON (po.offer_id)

                            po.offer_id,

                            po.product_id,

                            po.seller_id,

                            ph.price,

                            ph.collected_at

                        FROM product_offer po

                        JOIN price_history ph

                            ON po.offer_id = ph.offer_id

                        WHERE po.is_active = TRUE

                        ORDER BY

                            po.offer_id,

                            ph.collected_at DESC

                    )



                    SELECT

                        p.product_id,

                        c.category_code,

                        c.category_name,

                        b.brand_name,

                        p.product_name,

                        p.model_name,

                        p.image_url,

                        MIN(lop.price) AS current_min_price,

                        COUNT(DISTINCT lop.offer_id) AS active_offer_count,

                        COUNT(DISTINCT lop.seller_id) AS seller_count



                    FROM product p



                    JOIN category c

                        ON p.category_id = c.category_id



                    JOIN brand b

                        ON p.brand_id = b.brand_id



                    LEFT JOIN latest_offer_price lop

                        ON p.product_id = lop.product_id



                    LEFT JOIN cpu_spec cs

                        ON p.product_id = cs.product_id



                    LEFT JOIN gpu_spec gs

                        ON p.product_id = gs.product_id



                    LEFT JOIN cpu_model cm

                        ON cs.cpu_model_id = cm.cpu_model_id



                    LEFT JOIN gpu_model gm

                        ON gs.gpu_model_id = gm.gpu_model_id



                    LEFT JOIN ram_spec rs

                        ON p.product_id = rs.product_id



                    LEFT JOIN ssd_spec ss

                        ON p.product_id = ss.product_id



                    LEFT JOIN motherboard_spec ms

                        ON p.product_id = ms.product_id



                    {where_clause}



                    GROUP BY

                        p.product_id,

                        c.category_code,

                        c.category_name,

                        b.brand_name,

                        p.product_name,

                        p.model_name,

                        p.image_url



                    ORDER BY

                        current_min_price ASC NULLS LAST,

                        p.product_id ASC



                    LIMIT %s
                    OFFSET %s;

                    """,

                    tuple(params),

                )



                return [

                    {

                        "product_id": row[0],

                        "category_code": row[1],

                        "category_name": row[2],

                        "brand_name": row[3],

                        "product_name": row[4],

                        "model_name": row[5],

                        "image_url": row[6],

                        "current_min_price": self._to_int(row[7]),

                        "active_offer_count": int(row[8]),

                        "seller_count": int(row[9]),

                    }

                    for row in cur.fetchall()

                ]



        finally:

            conn.close()




    # ==========================================================
    # 상품 목록 전체 건수
    # - 페이지네이션 계산용
    # ==========================================================

    def get_product_count(
        self,
        category_code=None,
        keyword=None,
        brand_name=None,
        socket=None,
        memory_type=None,
        capacity_gb=None,
        capacity_group=None,
        vram_gb=None,
        chipset=None,
        interface=None,
        pcie_generation=None,
        form_factor=None,
        speed_mts=None,
        model_family=None,
        model_name=None,
    ):
        conn = get_connection()

        try:
            with conn.cursor() as cur:
                conditions = []
                params = []

                if category_code:
                    conditions.append(
                        "c.category_code = %s"
                    )
                    params.append(category_code)

                if keyword:
                    conditions.append(
                        """
                        (
                            p.product_name ILIKE %s
                            OR p.model_name ILIKE %s
                            OR b.brand_name ILIKE %s
                        )
                        """
                    )
                    search_keyword = f"%{keyword}%"
                    params.extend(
                        [
                            search_keyword,
                            search_keyword,
                            search_keyword,
                        ]
                    )

                if brand_name:
                    conditions.append(
                        "b.brand_name = %s"
                    )
                    params.append(brand_name)

                if socket:
                    conditions.append(
                        """
                        (
                            cs.socket = %s
                            OR ms.socket = %s
                        )
                        """
                    )
                    params.extend(
                        [socket, socket]
                    )

                if memory_type:
                    conditions.append(
                        """
                        (
                            gs.memory_type = %s
                            OR rs.memory_type = %s
                            OR ms.memory_type = %s
                        )
                        """
                    )
                    params.extend(
                        [
                            memory_type,
                            memory_type,
                            memory_type,
                        ]
                    )

                if capacity_gb is not None:
                    conditions.append(
                        """
                        (
                            rs.capacity_gb = %s
                            OR ss.capacity_gb = %s
                        )
                        """
                    )
                    params.extend(
                        [
                            capacity_gb,
                            capacity_gb,
                        ]
                    )

                if capacity_group:
                    capacity_values = self._ssd_capacity_values(
                        capacity_group
                    )

                    if capacity_values:
                        placeholders = ", ".join(
                            ["%s"] * len(capacity_values)
                        )
                        conditions.append(
                            f"ss.capacity_gb IN ({placeholders})"
                        )
                        params.extend(capacity_values)

                if vram_gb is not None:
                    conditions.append(
                        "gs.vram_gb = %s"
                    )
                    params.append(vram_gb)

                if chipset:
                    conditions.append(
                        "ms.chipset = %s"
                    )
                    params.append(chipset)

                if interface:
                    conditions.append(
                        "ss.interface = %s"
                    )
                    params.append(interface)

                if pcie_generation:
                    conditions.append(
                        "ss.pcie_generation = %s"
                    )
                    params.append(
                        pcie_generation
                    )

                if form_factor:
                    conditions.append(
                        """
                        (
                            ss.form_factor = %s
                            OR ms.form_factor = %s
                        )
                        """
                    )
                    params.extend(
                        [
                            form_factor,
                            form_factor,
                        ]
                    )

                if speed_mts is not None:
                    conditions.append(
                        "rs.speed_mts = %s"
                    )
                    params.append(speed_mts)

                if model_family:
                    conditions.append(
                        """
                        (
                            cm.family = %s
                            OR gm.family = %s
                        )
                        """
                    )
                    params.extend(
                        [
                            model_family,
                            model_family,
                        ]
                    )

                if model_name:
                    conditions.append(
                        """
                        (
                            TRIM(cm.model_name) = %s
                            OR TRIM(gm.model_name) = %s
                        )
                        """
                    )
                    params.extend(
                        [
                            model_name,
                            model_name,
                        ]
                    )

                where_clause = ""

                if conditions:
                    where_clause = (
                        "WHERE "
                        + " AND ".join(
                            conditions
                        )
                    )

                cur.execute(
                    f"""
                    SELECT
                        COUNT(
                            DISTINCT p.product_id
                        )
                    FROM product p
                    JOIN category c
                        ON p.category_id = c.category_id
                    JOIN brand b
                        ON p.brand_id = b.brand_id
                    LEFT JOIN cpu_spec cs
                        ON p.product_id = cs.product_id
                    LEFT JOIN gpu_spec gs
                        ON p.product_id = gs.product_id
                    LEFT JOIN cpu_model cm
                        ON cs.cpu_model_id = cm.cpu_model_id
                    LEFT JOIN gpu_model gm
                        ON gs.gpu_model_id = gm.gpu_model_id
                    LEFT JOIN ram_spec rs
                        ON p.product_id = rs.product_id
                    LEFT JOIN ssd_spec ss
                        ON p.product_id = ss.product_id
                    LEFT JOIN motherboard_spec ms
                        ON p.product_id = ms.product_id
                    {where_clause};
                    """,
                    tuple(params),
                )

                row = cur.fetchone()

                return (
                    int(row[0])
                    if row
                    else 0
                )

        finally:
            conn.close()


    # ==========================================================

    # 상품 기본 정보 + 카테고리별 스펙

    # ==========================================================

    def get_product_detail(self, product_id: int):

        conn = get_connection()



        try:

            with conn.cursor() as cur:

                cur.execute(

                    """

                    SELECT

                        p.product_id,

                        c.category_code,

                        c.category_name,

                        b.brand_name,

                        p.product_name,

                        p.model_name,

                        p.image_url,



                        cs.socket,

                        cs.cores,

                        cs.threads,

                        cs.base_clock_ghz,

                        cs.boost_clock_ghz,



                        gs.vram_gb,

                        gs.memory_type,



                        rs.capacity_gb,

                        rs.memory_type,

                        rs.speed_mts,

                        rs.module_count,



                        ss.capacity_gb,

                        ss.interface,

                        ss.pcie_generation,

                        ss.form_factor,

                        ss.read_speed_mbps,

                        ss.write_speed_mbps,



                        ms.socket,

                        ms.chipset,

                        ms.memory_type,

                        ms.form_factor



                    FROM product p



                    JOIN category c

                        ON p.category_id = c.category_id



                    JOIN brand b

                        ON p.brand_id = b.brand_id



                    LEFT JOIN cpu_spec cs

                        ON p.product_id = cs.product_id



                    LEFT JOIN gpu_spec gs

                        ON p.product_id = gs.product_id



                    LEFT JOIN ram_spec rs

                        ON p.product_id = rs.product_id



                    LEFT JOIN ssd_spec ss

                        ON p.product_id = ss.product_id



                    LEFT JOIN motherboard_spec ms

                        ON p.product_id = ms.product_id



                    WHERE p.product_id = %s;

                    """,

                    (product_id,),

                )



                row = cur.fetchone()



                if row is None:

                    return None



                product = {

                    "product_id": row[0],

                    "category_code": row[1],

                    "category_name": row[2],

                    "brand_name": row[3],

                    "product_name": row[4],

                    "model_name": row[5],

                    "image_url": row[6],

                    "spec": {},

                }



                category_code = row[1]



                if category_code == "CPU":

                    product["spec"] = {

                        "socket": row[7],

                        "cores": row[8],

                        "threads": row[9],

                        "base_clock_ghz": self._to_float(row[10]),

                        "boost_clock_ghz": self._to_float(row[11]),

                    }



                elif category_code == "GPU":

                    product["spec"] = {

                        "vram_gb": row[12],

                        "memory_type": row[13],

                    }



                elif category_code == "RAM":

                    product["spec"] = {

                        "capacity_gb": row[14],

                        "memory_type": row[15],

                        "speed_mts": row[16],

                        "module_count": row[17],

                    }



                elif category_code == "SSD":

                    product["spec"] = {

                        "capacity_gb": row[18],

                        "interface": row[19],

                        "pcie_generation": row[20],

                        "form_factor": row[21],

                        "read_speed_mbps": row[22],

                        "write_speed_mbps": row[23],

                    }



                elif category_code == "MOTHERBOARD":

                    product["spec"] = {

                        "socket": row[24],

                        "chipset": row[25],

                        "memory_type": row[26],

                        "form_factor": row[27],

                    }



                return product



        finally:

            conn.close()



    # ==========================================================

    # 현재 판매처별 가격

    # ==========================================================

    def get_product_offers(self, product_id: int):

        conn = get_connection()



        try:

            with conn.cursor() as cur:

                cur.execute(

                    """

                    WITH latest_offer_price AS (

                        SELECT DISTINCT ON (po.offer_id)

                            po.offer_id,

                            po.product_id,

                            po.seller_id,

                            po.retailer_id,

                            po.product_url,

                            ph.price,

                            ph.collected_at

                        FROM product_offer po



                        JOIN price_history ph

                            ON po.offer_id = ph.offer_id



                        WHERE po.product_id = %s

                          AND po.is_active = TRUE



                        ORDER BY

                            po.offer_id,

                            ph.collected_at DESC

                    )



                    SELECT

                        lop.offer_id,

                        s.seller_name,

                        r.retailer_name,

                        lop.price,

                        lop.product_url,

                        lop.collected_at



                    FROM latest_offer_price lop



                    JOIN seller s

                        ON lop.seller_id = s.seller_id



                    JOIN retailer r

                        ON lop.retailer_id = r.retailer_id



                    ORDER BY

                        lop.price ASC,

                        r.retailer_name ASC;

                    """,

                    (product_id,),

                )



                return [

                    {

                        "offer_id": row[0],

                        "seller_name": row[1],

                        "retailer_name": row[2],

                        "price": int(row[3]),

                        "product_url": row[4],

                        "collected_at": row[5],

                    }

                    for row in cur.fetchall()

                ]



        finally:

            conn.close()



    # ==========================================================

    # 내부 유틸리티

    # ==========================================================



    def _fetch_model_groups(self, cur, category_code):

        if category_code == "CPU":

            cur.execute(

                """

                SELECT DISTINCT

                    vb.brand_name,

                    cm.family,

                    TRIM(cm.model_name)

                FROM cpu_model cm

                JOIN brand vb

                    ON cm.vendor_brand_id = vb.brand_id

                JOIN cpu_spec cs

                    ON cs.cpu_model_id = cm.cpu_model_id

                JOIN product p

                    ON p.product_id = cs.product_id

                WHERE cm.model_name IS NOT NULL

                  AND TRIM(cm.model_name) <> ''

                ORDER BY

                    vb.brand_name,

                    cm.family,

                    TRIM(cm.model_name);

                """

            )

        elif category_code == "GPU":

            cur.execute(

                """

                SELECT DISTINCT

                    vb.brand_name,

                    gm.family,

                    TRIM(gm.model_name)

                FROM gpu_model gm

                JOIN brand vb

                    ON gm.vendor_brand_id = vb.brand_id

                JOIN gpu_spec gs

                    ON gs.gpu_model_id = gm.gpu_model_id

                JOIN product p

                    ON p.product_id = gs.product_id

                WHERE gm.model_name IS NOT NULL

                  AND TRIM(gm.model_name) <> ''

                ORDER BY

                    vb.brand_name,

                    gm.family,

                    TRIM(gm.model_name);

                """

            )

        else:

            return []



        groups = {}



        for vendor_name, family, model_name in cur.fetchall():

            family_name = (family or "기타").strip()

            vendor_name = self._normalize_vendor_name(

                vendor_name

            )

            model_name = (model_name or "").strip()

            key = (

                vendor_name.casefold(),

                family_name.casefold(),

            )



            if key not in groups:

                groups[key] = {

                    "vendor_name": vendor_name,

                    "family": family_name,

                    "label": f"{vendor_name} / {family_name}",

                    "models": [],

                }



            if (

                model_name

                and model_name

                not in groups[key]["models"]

            ):

                groups[key]["models"].append(

                    model_name

                )



        return list(groups.values())



    @staticmethod

    def _normalize_vendor_name(vendor_name):

        name = (vendor_name or "기타").strip()

        normalized = name.casefold()



        vendor_names = {

            "intel": "Intel",

            "amd": "AMD",

            "nvidia": "NVIDIA",

        }



        return vendor_names.get(

            normalized,

            name,

        )



    @staticmethod

    def _build_ssd_capacity_groups(capacities):
        """SSD 용량을 UI용 GB/TB 그룹으로 묶는다."""
        groups = {}

        for capacity in capacities:
            if capacity is None:
                continue

            capacity = int(capacity)

            if capacity < 1000:
                key = f"{capacity}GB"
            else:
                tb_value = round(capacity / 1000)

                if tb_value < 1:
                    tb_value = 1

                key = f"{tb_value}TB"

            if key not in groups:
                groups[key] = {
                    "value": key,
                    "label": key,
                    "capacities": [],
                }

            groups[key]["capacities"].append(capacity)

        return sorted(
            groups.values(),
            key=lambda item: min(item["capacities"]),
        )


    @staticmethod

    def _ssd_capacity_values(capacity_group):
        """1TB 같은 UI 값을 DB의 실제 GB 값으로 변환한다."""
        if not capacity_group:
            return []

        value = str(capacity_group).strip().upper()

        if value.endswith("GB"):
            try:
                return [int(value[:-2])]
            except ValueError:
                return []

        if value.endswith("TB"):
            try:
                tb_value = int(value[:-2])
            except ValueError:
                return []

            return [
                tb_value * 1000,
                tb_value * 1024,
            ]

        return []


    @staticmethod

    def _fetch_single_column(cur, query, params=()):

        cur.execute(query, params)

        return [row[0] for row in cur.fetchall()]



    @staticmethod

    def _to_int(value):

        return int(value) if value is not None else None



    @staticmethod

    def _to_float(value):

        return float(value) if value is not None else None
