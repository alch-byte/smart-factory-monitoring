
%%writefile app.py

import streamlit as st
import pandas as pd
import plotly.express as px


# --------------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="스마트공장 생산 모니터링",
    page_icon="🏭",
    layout="wide"
)


# --------------------------------------------------
# 2. 화면 디자인 설정
# --------------------------------------------------

st.markdown("""
<style>
    .stApp {
        background-color: #F5F7FA;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E0E0E0;
    }

    h1 {
        color: #1E3A5F;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# 3. 사이드바 메뉴
# --------------------------------------------------

st.sidebar.title("🏭 스마트공장 시스템")

menu = st.sidebar.radio(
    "메뉴 선택",
    [
        "생산 현황",
        "품질 관리",
        "설비 모니터링",
        "데이터 관리"
    ]
)


# --------------------------------------------------
# 4. CSV 파일 불러오기
# --------------------------------------------------

file_name = "production_data.csv"

try:
    df = pd.read_csv(file_name)

except FileNotFoundError:

    uploaded_file = st.sidebar.file_uploader(
        "생산 데이터 CSV 업로드",
        type=["csv"]
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

    else:
        st.warning("production_data.csv 파일을 업로드해주세요.")
        st.stop()


# --------------------------------------------------
# 5. 데이터 전처리
# --------------------------------------------------

df = df.copy()

# 필요한 컬럼 확인
required_columns = [
    "timestamp",
    "machine_id",
    "product_id",
    "production_count",
    "defect_count",
    "temperature",
    "humidity",
    "operating_status"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(f"CSV 파일에 필요한 컬럼이 없습니다: {missing_columns}")
    st.stop()


# 날짜 데이터 변환
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

# 날짜가 잘못된 행 제거
df = df.dropna(subset=["timestamp"]).copy()

# 숫자형 데이터 변환
numeric_columns = [
    "production_count",
    "defect_count",
    "temperature",
    "humidity"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# 생산량과 불량 수량의 결측값은 0으로 처리
df["production_count"] = df["production_count"].fillna(0)
df["defect_count"] = df["defect_count"].fillna(0)

# 시간순 정렬
df = df.sort_values("timestamp").reset_index(drop=True)


if df.empty:
    st.warning("분석할 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 6. 품질 상태 색상 지정 함수
# --------------------------------------------------

def color_quality_status(value):

    if value == "정상":
        return "background-color: #D4EDDA; color: #155724"

    elif value == "경고":
        return "background-color: #F8D7DA; color: #721C24"

    else:
        return "background-color: #E2E3E5; color: #383D41"


# ==================================================
# 7. 생산 현황 메뉴
# ==================================================

if menu == "생산 현황":

    st.title("📊 생산 현황")

    # 설비 선택
    machine_list = sorted(
        df["machine_id"].dropna().unique().tolist(),
        key=str
    )

    machine_options = ["전체"] + machine_list

    selected_machine = st.selectbox(
        "설비 선택",
        machine_options
    )

    # 날짜 선택
    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "시작 날짜",
            value=min_date
        )

    with col2:
        end_date = st.date_input(
            "종료 날짜",
            value=max_date
        )

    if start_date > end_date:
        st.error("시작 날짜가 종료 날짜보다 늦을 수 없습니다.")
        st.stop()

    # 데이터 필터링
    filtered_df = df.copy()

    if selected_machine != "전체":
        filtered_df = filtered_df[
            filtered_df["machine_id"] == selected_machine
        ]

    filtered_df = filtered_df[
        (filtered_df["timestamp"] >= pd.Timestamp(start_date)) &
        (filtered_df["timestamp"] < (
            pd.Timestamp(end_date) + pd.Timedelta(days=1)
        ))
    ]

    if filtered_df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        st.stop()

    # 생산 현황 계산
    total_production = filtered_df["production_count"].sum()
    total_defect = filtered_df["defect_count"].sum()

    normal_production = total_production - total_defect

    if total_production > 0:
        defect_rate = total_defect / total_production * 100
        defect_rate_text = f"{defect_rate:.2f}%"
    else:
        defect_rate_text = "계산 불가"

    # KPI 표시
    st.subheader("생산 현황 요약")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "총 생산량",
        f"{total_production:,.0f}개"
    )

    col2.metric(
        "정상 제품 수",
        f"{normal_production:,.0f}개"
    )

    col3.metric(
        "불량 제품 수",
        f"{total_defect:,.0f}개"
    )

    col4.metric(
        "불량률",
        defect_rate_text
    )

    # 평균 공정 온도
    average_temperature = filtered_df["temperature"].mean()

    st.metric(
        "평균 공정 온도",
        f"{average_temperature:.1f} ℃"
        if pd.notna(average_temperature)
        else "데이터 없음"
    )

    st.divider()

    # 생산 목표 달성률
    st.subheader("생산 목표 달성률")

    target_production = st.number_input(
        "목표 생산량 (개)",
        min_value=1,
        value=10000,
        step=100
    )

    achievement_rate = (
        total_production / target_production * 100
    )

    st.metric(
        "목표 달성률",
        f"{achievement_rate:.1f}%"
    )

    st.progress(
        min(achievement_rate, 100) / 100
    )

    if achievement_rate >= 100:
        st.success("생산 목표를 달성했습니다.")
    else:
        st.info("아직 생산 목표에 도달하지 않았습니다.")

    st.divider()

    # 설비별 생산량 TOP 10
    st.subheader("설비별 생산량 TOP 10")

    production_by_machine = (
        filtered_df.groupby("machine_id")["production_count"]
        .sum()
        .reset_index()
        .sort_values("production_count", ascending=False)
        .head(10)
    )

    fig = px.bar(
        production_by_machine,
        x="machine_id",
        y="production_count",
        text="production_count",
        title="설비별 생산량 TOP 10",
        labels={
            "machine_id": "설비번호",
            "production_count": "생산량"
        }
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # 생산 데이터 정보
    st.subheader("생산 데이터 정보")

    col1, col2, col3 = st.columns(3)

    col1.metric("데이터 행 수", f"{len(filtered_df):,}개")
    col2.metric("데이터 컬럼 수", f"{len(filtered_df.columns)}개")
    col3.metric(
        "조회 기간",
        f"{start_date} ~ {end_date}"
    )

    st.subheader("생산 기록 조회")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


# ==================================================
# 8. 품질 관리 메뉴
# ==================================================

elif menu == "품질 관리":

    st.title("🔍 품질 관리")

    # 설비별 생산량과 불량 수량 집계
    quality_df = (
        df.groupby("machine_id", dropna=False)[
            ["production_count", "defect_count"]
        ]
        .sum()
        .reset_index()
    )

    # 설비별 불량률 계산
    quality_df["불량률(%)"] = quality_df.apply(
        lambda row: (
            row["defect_count"] / row["production_count"] * 100
            if row["production_count"] > 0
            else None
        ),
        axis=1
    )

    # 전체 품질 현황
    total_production = quality_df["production_count"].sum()
    total_defect = quality_df["defect_count"].sum()

    if total_production > 0:
        total_defect_rate = (
            total_defect / total_production * 100
        )
        total_defect_rate_text = f"{total_defect_rate:.2f}%"
    else:
        total_defect_rate_text = "계산 불가"

    st.subheader("전체 품질 현황")

    col1, col2, col3 = st.columns(3)

    col1.metric("전체 생산량", f"{total_production:,.0f}개")
    col2.metric("전체 불량 수량", f"{total_defect:,.0f}개")
    col3.metric("전체 불량률", total_defect_rate_text)

    st.divider()

    # 품질 경고 기준 설정
    st.subheader("품질 경고 기준")

    allowed_defect_rate = st.slider(
        "허용 불량률 (%)",
        min_value=0.0,
        max_value=10.0,
        value=5.0,
        step=0.1
    )

    # 설비별 품질 상태 판정
    def get_quality_status(row):

        if row["production_count"] <= 0:
            return "계산 불가"

        elif row["불량률(%)"] <= allowed_defect_rate:
            return "정상"

        else:
            return "경고"

    quality_df["품질 상태"] = quality_df.apply(
        get_quality_status,
        axis=1
    )

    # 경고 설비 계산
    warning_df = quality_df[
        quality_df["품질 상태"] == "경고"
    ]

    warning_count = len(warning_df)

    st.metric("경고 설비 수", f"{warning_count}대")

    if warning_count > 0:

        warning_machines = ", ".join(
            warning_df["machine_id"].astype(str).tolist()
        )

        st.error(
            f"품질 경고: {warning_count}개 설비의 불량률이 "
            f"허용 기준 {allowed_defect_rate:.1f}%를 초과했습니다. "
            f"대상 설비: {warning_machines}"
        )

    else:
        st.success("품질 경고 설비가 없습니다. 모든 판정 가능 설비가 정상입니다.")

    st.divider()

    # 설비별 불량률 TOP 10 그래프
    st.subheader("설비별 불량률 TOP 10")

    defect_chart_df = quality_df[
        quality_df["production_count"] > 0
    ].copy()

    defect_chart_df = (
        defect_chart_df
        .sort_values("불량률(%)", ascending=False)
        .head(10)
    )

    if not defect_chart_df.empty:

        fig = px.bar(
            defect_chart_df,
            x="machine_id",
            y="불량률(%)",
            text=defect_chart_df["불량률(%)"].apply(
                lambda x: f"{x:.2f}%"
            ),
            title="설비별 불량률 TOP 10",
            labels={
                "machine_id": "설비번호",
                "불량률(%)": "불량률"
            }
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis_ticksuffix="%"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        st.info("불량률을 계산할 수 있는 설비가 없습니다.")

    st.divider()

    # 날짜별 불량률 변화 그래프
    st.subheader("날짜별 불량률 변화")

    date_df = df.copy()

    # timestamp에서 날짜 추출
    date_df["date"] = date_df["timestamp"].dt.date

    # 날짜별 생산량과 불량 수량 합계
    daily_quality_df = (
        date_df.groupby("date")[
            ["production_count", "defect_count"]
        ]
        .sum()
        .reset_index()
        .sort_values("date")
    )

    # 날짜별 불량률 계산
    daily_quality_df["불량률(%)"] = daily_quality_df.apply(
        lambda row: (
            row["defect_count"] / row["production_count"] * 100
            if row["production_count"] > 0
            else None
        ),
        axis=1
    )

    daily_chart_df = daily_quality_df.dropna(
        subset=["불량률(%)"]
    )

    if not daily_chart_df.empty:

        fig = px.line(
            daily_chart_df,
            x="date",
            y="불량률(%)",
            markers=True,
            title="날짜별 불량률 변화",
            labels={
                "date": "날짜",
                "불량률(%)": "불량률(%)"
            }
        )

        fig.update_traces(
            hovertemplate=(
                "날짜: %{x}<br>"
                "불량률: %{y:.2f}%"
                "<extra></extra>"
            )
        )

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis_ticksuffix="%",
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        st.info("날짜별 불량률을 계산할 수 있는 데이터가 없습니다.")

    # 날짜별 집계표
    with st.expander("날짜별 품질 집계표 확인"):

        daily_table = daily_quality_df.rename(
            columns={
                "date": "날짜",
                "production_count": "총생산량",
                "defect_count": "불량 수량"
            }
        ).copy()

        daily_table["불량률(%)"] = (
            daily_table["불량률(%)"].apply(
                lambda x: f"{x:.2f}%" if pd.notna(x) else "계산 불가"
            )
        )

        st.dataframe(
            daily_table,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # 최소 생산량 기준 설정
    st.subheader("설비별 품질 순위 기준")

    min_production = st.number_input(
        "최소 생산량 기준 (개)",
        min_value=0,
        value=1000,
        step=100
    )

    # 최소 생산량 이상인 설비만 순위에 포함
    quality_rank_df = quality_df[
        quality_df["production_count"] >= min_production
    ].copy()

    quality_rank_df = quality_rank_df[
        quality_rank_df["production_count"] > 0
    ]

    # 불량률이 낮은 순서대로 정렬
    quality_rank_df = quality_rank_df.sort_values(
        "불량률(%)",
        ascending=True,
        kind="mergesort"
    ).reset_index(drop=True)

    # 순위 번호 추가
    quality_rank_df.insert(
        0,
        "순위",
        range(1, len(quality_rank_df) + 1)
    )

    st.metric(
        "최소 생산량 기준을 만족하는 설비 수",
        f"{len(quality_rank_df):,}대"
    )

    # 순위표 표시용 데이터 생성
    quality_rank_table = quality_rank_df[
        [
            "순위",
            "machine_id",
            "production_count",
            "defect_count",
            "불량률(%)",
            "품질 상태"
        ]
    ].copy()

    quality_rank_table = quality_rank_table.rename(
        columns={
            "machine_id": "설비번호",
            "production_count": "총생산량",
            "defect_count": "불량 수량"
        }
    )

    quality_rank_table["총생산량"] = (
        quality_rank_table["총생산량"].map(
            lambda x: f"{x:,.0f}"
        )
    )

    quality_rank_table["불량 수량"] = (
        quality_rank_table["불량 수량"].map(
            lambda x: f"{x:,.0f}"
        )
    )

    quality_rank_table["불량률(%)"] = (
        quality_rank_table["불량률(%)"].map(
            lambda x: f"{x:.2f}%"
        )
    )

    st.subheader("전체 설비 품질 순위표")

    if not quality_rank_table.empty:

        st.dataframe(
            quality_rank_table.style.map(
                color_quality_status,
                subset=["품질 상태"]
            ),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("품질 순위 TOP 10")

        top10_rank_table = quality_rank_table.head(10)

        st.dataframe(
            top10_rank_table.style.map(
                color_quality_status,
                subset=["품질 상태"]
            ),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "최소 생산량 기준을 만족하는 설비가 없습니다. "
            "기준을 낮춰 확인해보세요."
        )

    # 최소 생산량 기준 미달 설비
    below_min_df = quality_df[
        (quality_df["production_count"] > 0) &
        (quality_df["production_count"] < min_production)
    ].copy()

    if not below_min_df.empty:

        with st.expander("최소 생산량 기준 미달 설비 확인"):

            below_min_table = below_min_df[
                [
                    "machine_id",
                    "production_count",
                    "defect_count",
                    "불량률(%)",
                    "품질 상태"
                ]
            ].copy()

            below_min_table = below_min_table.rename(
                columns={
                    "machine_id": "설비번호",
                    "production_count": "총생산량",
                    "defect_count": "불량 수량"
                }
            )

            below_min_table["총생산량"] = (
                below_min_table["총생산량"].map(
                    lambda x: f"{x:,.0f}"
                )
            )

            below_min_table["불량 수량"] = (
                below_min_table["불량 수량"].map(
                    lambda x: f"{x:,.0f}"
                )
            )

            below_min_table["불량률(%)"] = (
                below_min_table["불량률(%)"].map(
                    lambda x: f"{x:.2f}%"
                )
            )

            st.dataframe(
                below_min_table,
                use_container_width=True,
                hide_index=True
            )

    # 생산량이 0인 설비 별도 표시
    zero_production_df = quality_df[
        quality_df["production_count"] <= 0
    ].copy()

    if not zero_production_df.empty:

        st.subheader("생산량 0인 설비")

        zero_production_table = zero_production_df[
            [
                "machine_id",
                "production_count",
                "defect_count"
            ]
        ].copy()

        zero_production_table = zero_production_table.rename(
            columns={
                "machine_id": "설비번호",
                "production_count": "총생산량",
                "defect_count": "불량 수량"
            }
        )

        zero_production_table["불량률(%)"] = "계산 불가"
        zero_production_table["품질 상태"] = "계산 불가"

        zero_production_table["총생산량"] = (
            zero_production_table["총생산량"].map(
                lambda x: f"{x:,.0f}"
            )
        )

        zero_production_table["불량 수량"] = (
            zero_production_table["불량 수량"].map(
                lambda x: f"{x:,.0f}"
            )
        )

        st.dataframe(
            zero_production_table.style.map(
                color_quality_status,
                subset=["품질 상태"]
            ),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # 기존 설비별 품질 분석표
    st.subheader("설비별 품질 분석")

    quality_table = quality_df[
        [
            "machine_id",
            "production_count",
            "defect_count",
            "불량률(%)",
            "품질 상태"
        ]
    ].copy()

    quality_table = quality_table.rename(
        columns={
            "machine_id": "설비번호",
            "production_count": "총생산량",
            "defect_count": "불량 수량"
        }
    )

    quality_table["총생산량"] = (
        quality_table["총생산량"].map(
            lambda x: f"{x:,.0f}"
        )
    )

    quality_table["불량 수량"] = (
        quality_table["불량 수량"].map(
            lambda x: f"{x:,.0f}"
        )
    )

    quality_table["불량률(%)"] = (
        quality_table["불량률(%)"].map(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "계산 불가"
        )
    )

    st.metric(
        "전체 설비 개수",
        f"{len(quality_table):,}대"
    )

    st.dataframe(
        quality_table.style.map(
            color_quality_status,
            subset=["품질 상태"]
        ),
        use_container_width=True,
        hide_index=True
    )


# ==================================================
# 9. 설비 모니터링 메뉴
# ==================================================

elif menu == "설비 모니터링":

    st.title("🏭 설비 모니터링")

    st.write(
        "설비를 선택하면 최근 센서 정보와 "
        "온도·습도 변화 그래프를 확인할 수 있습니다."
    )

    # 설비번호 목록 가져오기
    machine_list = sorted(
        df["machine_id"].dropna().unique().tolist(),
        key=str
    )

    if not machine_list:
        st.warning("선택할 수 있는 설비 정보가 없습니다.")
        st.stop()

    # 사용자가 설비 선택
    selected_machine = st.selectbox(
        "설비번호 선택",
        machine_list
    )

    # 선택한 설비의 데이터만 가져오기
    selected_machine_df = df[
        df["machine_id"] == selected_machine
    ].copy()

    # timestamp 기준으로 시간순 정렬
    selected_machine_df = selected_machine_df.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    if selected_machine_df.empty:
        st.warning("선택한 설비의 데이터가 없습니다.")
        st.stop()

    # 가장 최근 기록 가져오기
    latest_record = selected_machine_df.iloc[-1]

    st.divider()

    # --------------------------------------------------
    # 최근 설비 상태 표시
    # --------------------------------------------------

    st.subheader("최근 설비 상태")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "설비번호",
            str(selected_machine)
        )

    with col2:
        st.metric(
            "최근 기록 시간",
            latest_record["timestamp"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    # 최근 온도와 습도 표시
    col1, col2 = st.columns(2)

    with col1:
        temperature = latest_record["temperature"]

        st.metric(
            "최근 공정 온도",
            f"{temperature:.1f} ℃"
            if pd.notna(temperature)
            else "데이터 없음"
        )

    with col2:
        humidity = latest_record["humidity"]

        st.metric(
            "최근 습도",
            f"{humidity:.1f} %"
            if pd.notna(humidity)
            else "데이터 없음"
        )

    st.divider()

    # --------------------------------------------------
    # 온도 이상 경고 기능
    # --------------------------------------------------

    st.subheader("🌡️ 온도 이상 경고 설정")

    # 온도 경고 기준 설정
    temperature_limit = st.slider(
        "온도 경고 기준 (℃)",
        min_value=30,
        max_value=50,
        value=40,
        step=1
    )

    st.write(
        f"현재 온도 경고 기준: **{temperature_limit} ℃**"
    )

    # 최근 온도와 경고 기준 비교
    if pd.isna(temperature):

        st.warning(
            "최근 온도 데이터가 없어 온도 경고 상태를 판정할 수 없습니다."
        )

    elif temperature > temperature_limit:

        st.error(
            f"경고: {selected_machine} 설비의 온도가 기준을 초과했습니다."
        )

    else:

        st.success(
            f"{selected_machine} 설비의 온도가 정상 범위입니다."
        )

    # 가동 상태는 온도 경고와 별도로 표시
    st.subheader("⚙️ 설비 가동 상태")

    operating_status = latest_record["operating_status"]

    if pd.isna(operating_status):
        st.info("가동 상태 데이터가 없습니다.")
    else:
        st.write(f"현재 가동 상태: **{operating_status}**")

    st.divider()

    # --------------------------------------------------
    # 시간별 온도 변화 그래프
    # --------------------------------------------------

    st.subheader("시간별 온도 변화")

    # 온도 데이터가 있는 행만 그래프에 사용
    temperature_df = selected_machine_df.dropna(
        subset=["temperature"]
    ).copy()

    if not temperature_df.empty:

        fig_temperature = px.line(
            temperature_df,
            x="timestamp",
            y="temperature",
            markers=True,
            title="시간별 온도 변화",
            labels={
                "timestamp": "기록 시간",
                "temperature": "공정 온도(℃)"
            }
        )

        # 마우스를 올리면 시간과 온도 표시
        fig_temperature.update_traces(
            hovertemplate=(
                "기록 시간: %{x}<br>"
                "공정 온도: %{y:.1f} ℃"
                "<extra></extra>"
            )
        )

        # 현재 설정한 온도 경고 기준을 빨간색 점선으로 표시
        fig_temperature.add_hline(
            y=temperature_limit,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text=f"경고 기준 {temperature_limit} ℃",
            annotation_position="top left"
        )

        fig_temperature.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            hovermode="x unified",
            xaxis_title="기록 시간",
            yaxis_title="공정 온도(℃)"
        )

        st.plotly_chart(
            fig_temperature,
            use_container_width=True
        )

    else:
        st.info("표시할 온도 데이터가 없습니다.")

    st.divider()

    # --------------------------------------------------
    # 시간별 습도 변화 그래프
    # --------------------------------------------------

    st.subheader("시간별 습도 변화")

    # 습도 데이터가 있는 행만 그래프에 사용
    humidity_df = selected_machine_df.dropna(
        subset=["humidity"]
    ).copy()

    if not humidity_df.empty:

        fig_humidity = px.line(
            humidity_df,
            x="timestamp",
            y="humidity",
            markers=True,
            title="시간별 습도 변화",
            labels={
                "timestamp": "기록 시간",
                "humidity": "습도(%)"
            }
        )

        # 마우스를 올리면 시간과 습도 표시
        fig_humidity.update_traces(
            hovertemplate=(
                "기록 시간: %{x}<br>"
                "습도: %{y:.1f}%"
                "<extra></extra>"
            )
        )

        fig_humidity.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            hovermode="x unified",
            xaxis_title="기록 시간",
            yaxis_title="습도(%)"
        )

        st.plotly_chart(
            fig_humidity,
            use_container_width=True
        )

    else:
        st.info("표시할 습도 데이터가 없습니다.")


# ==================================================
# 10. 데이터 관리 메뉴
# ==================================================

elif menu == "데이터 관리":

    st.title("🗂️ 데이터 관리")

    st.subheader("전체 생산 데이터")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # CSV 다운로드
    csv_data = df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        label="CSV 데이터 다운로드",
        data=csv_data,
        file_name="production_data_download.csv",
        mime="text/csv"
    )
