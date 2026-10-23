(() => {
    // ======================================================
    // 판매처 가격 비교: 기본 5개만 표시
    // ======================================================
    const offerMoreButton = document.getElementById(
        "offer-more-button",
    );

    if (offerMoreButton) {
        const extraRows = [
            ...document.querySelectorAll(
                ".offer-extra-row",
            ),
        ];

        offerMoreButton.addEventListener(
            "click",
            () => {
                const isExpanded =
                    offerMoreButton.getAttribute(
                        "aria-expanded",
                    ) === "true";

                extraRows.forEach((row) => {
                    row.hidden = isExpanded;
                });

                offerMoreButton.setAttribute(
                    "aria-expanded",
                    String(!isExpanded),
                );

                offerMoreButton.textContent =
                    isExpanded
                        ? "더보기"
                        : "접기";
            },
        );
    }

    // ======================================================
    // 최근 1주일 가격 변동 그래프
    // ======================================================
    const canvas = document.getElementById(
        "price-chart",
    );
    const dataElement = document.getElementById(
        "price-data",
    );

    if (!canvas || !dataElement) {
        return;
    }

    const allPoints = JSON.parse(
        dataElement.textContent || "[]",
    );

    // 오늘 포함 최근 7일만 표시한다.
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const sevenDayStart = new Date(today);
    sevenDayStart.setDate(
        sevenDayStart.getDate() - 6,
    );

    const points = allPoints.filter(
        (point) => {
            const pointDate = new Date(
                `${point.price_date}T00:00:00`,
            );

            return (
                pointDate >= sevenDayStart
                && pointDate <= today
            );
        },
    );

    if (points.length === 0) {
        canvas.parentElement.innerHTML =
            '<div class="empty-panel">'
            + '최근 1주일 가격 이력 데이터가 없습니다.'
            + '</div>';
        return;
    }

    const context = canvas.getContext("2d");
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(
        canvas.parentElement.clientWidth,
        360,
    );
    const height = 300;

    canvas.width = width * ratio;
    canvas.height = height * ratio;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    context.scale(ratio, ratio);

    const padding = {
        top: 24,
        right: 28,
        bottom: 48,
        left: 82,
    };

    // 날짜가 차트 양 끝에 붙지 않도록
    // 실제 데이터 영역을 좌우에서 한 번 더 안쪽으로 넣는다.
    const horizontalInset = Math.min(
        36,
        Math.max(20, width * 0.035),
    );

    const plotLeft =
        padding.left + horizontalInset;
    const plotRight =
        width - padding.right - horizontalInset;

    const chartWidth =
        plotRight - plotLeft;
    const chartHeight =
        height - padding.top - padding.bottom;

    const prices = points.map(
        (point) => Number(point.min_price),
    );

    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);

    let range = maxPrice - minPrice;

    if (range === 0) {
        range = Math.max(
            minPrice * 0.1,
            1000,
        );
    }

    const lowerBound = Math.max(
        0,
        minPrice - range * 0.15,
    );
    const upperBound =
        maxPrice + range * 0.15;

    const xForIndex = (index) => {
        if (points.length === 1) {
            return (
                plotLeft
                + chartWidth / 2
            );
        }

        return (
            plotLeft
            + (
                index
                / (points.length - 1)
            ) * chartWidth
        );
    };

    const yForPrice = (price) => (
        padding.top
        + (
            1
            - (
                price - lowerBound
            ) / (
                upperBound - lowerBound
            )
        ) * chartHeight
    );

    context.font = "12px sans-serif";

    // Y축 가이드
    for (
        let index = 0;
        index <= 4;
        index += 1
    ) {
        const ratioY = index / 4;
        const y =
            padding.top
            + ratioY * chartHeight;
        const price =
            upperBound
            - ratioY
            * (
                upperBound
                - lowerBound
            );

        context.beginPath();
        context.moveTo(
            plotLeft,
            y,
        );
        context.lineTo(
            plotRight,
            y,
        );
        context.strokeStyle = "#d7d7d7";
        context.lineWidth = 1;
        context.stroke();

        context.fillStyle = "#666666";
        context.textAlign = "right";
        context.textBaseline = "middle";
        context.fillText(
            `${Math.round(price).toLocaleString(
                "ko-KR",
            )}원`,
            padding.left - 12,
            y,
        );
    }

    // 가격선
    context.beginPath();

    points.forEach(
        (point, index) => {
            const x = xForIndex(index);
            const y = yForPrice(
                Number(point.min_price),
            );

            if (index === 0) {
                context.moveTo(x, y);
            } else {
                context.lineTo(x, y);
            }
        },
    );

    context.strokeStyle = "#202020";
    context.lineWidth = 2;
    context.stroke();

    // 데이터 포인트 + 날짜
    points.forEach(
        (point, index) => {
            const x = xForIndex(index);
            const y = yForPrice(
                Number(point.min_price),
            );

            context.beginPath();
            context.arc(
                x,
                y,
                4,
                0,
                Math.PI * 2,
            );
            context.fillStyle = "#202020";
            context.fill();

            context.fillStyle = "#666666";
            context.textAlign = "center";
            context.textBaseline = "top";
            context.fillText(
                point.price_date,
                x,
                height
                    - padding.bottom
                    + 16,
            );
        },
    );
})();
