
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

    [data-testid="stMetric"] {
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

st.sidebar.title("🏭 스마트공장")

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
# 4. CSV 데이터 불러오기
# --------------------------------------------------

file_name = "production_data.csv"

try:
    # 현재 폴더에 CSV 파일이 있으면 불러오기
    df = pd.read_csv(file_name)

except FileNotFoundError:
    # CSV 파일이 없으면 직접 업로드
    uploaded_file = st.sidebar.file_uploader(
        "생산 데이터 CSV 업로드",
        type=["csv"]
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        st.warning("생산 데이터 CSV 파일을 업로드해주세요.")
        st.stop()


# --------------------------------------------------
# 5. 데이터 전처리
# --------------------------------------------------

# 원본 데이터 보호를 위해 복사
df = df.copy()

# 필요한 컬럼 목록
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

# 필요한 컬럼이 있는지 확인
missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(f"필요한 컬럼이 없습니다: {missing_columns}")
    st.stop()

# 날짜 데이터 변환
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

# 날짜 변환에 실패한 행 제거
df = df.dropna(subset=["timestamp"])

# 생산량과 불량량 숫자로 변환
df["production_count"] = pd.to_numeric(
    df["production_count"],
    errors="coerce"
).fillna(0)

df["defect_count"] = pd.to_numeric(
    df["defect_count"],
    errors="coerce"
).fillna(0)

# 온도와 습도 숫자로 변환
df["temperature"] = pd.to_numeric(
    df["temperature"],
    errors="coerce"
)

df["humidity"] = pd.to_numeric(
    df["humidity"],
    errors="coerce"
)

# 날짜순 정렬
df = df.sort_values("timestamp")

# 데이터가 비어 있는지 확인
if df.empty:
    st.warning("분석할 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 6. 생산 현황 메뉴
# --------------------------------------------------

if menu == "생산 현황":

    st.title("📊 생산 현황")

    # 설비 목록
    machine_list = sorted(
        df["machine_id"].dropna().unique().tolist(),
        key=str
    )

    machine_options = ["전체"] + machine_list

    # 설비 선택
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
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )

    with col2:
        end_date = st.date_input(
            "종료 날짜",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )

    # 날짜 범위 확인
    if start_date > end_date:
        st.error("시작 날짜는 종료 날짜보다 늦을 수 없습니다.")
        st.stop()

    # 데이터 복사
    filtered_df = df.copy()

    # 설비 필터링
    if selected_machine != "전체":
        filtered_df = filtered_df[
            filtered_df["machine_id"] == selected_machine
        ]

    # 날짜 필터링
    filtered_df = filtered_df[
        (filtered_df["timestamp"] >= pd.Timestamp(start_date)) &
        (
            filtered_df["timestamp"] <
            pd.Timestamp(end_date) + pd.Timedelta(days=1)
        )
    ]

    # 조회 결과 확인
    if filtered_df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        st.stop()

    # 전체 생산량과 불량량 계산
    total_production = filtered_df["production_count"].sum()
    total_defect = filtered_df["defect_count"].sum()

    # 정상 제품 수 계산
    normal_count = total_production - total_defect

    # 불량률 계산
    if total_production > 0:
        defect_rate = total_defect / total_production * 100
        defect_rate_text = f"{defect_rate:.2f}%"
    else:
        defect_rate_text = "계산 불가"

    # 평균 온도 계산
    avg_temperature = filtered_df["temperature"].mean()

    # KPI 표시
    st.subheader("주요 생산 지표")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "총 생산량",
        f"{total_production:,.0f}개"
    )

    col2.metric(
        "정상 제품 수",
        f"{normal_count:,.0f}개"
    )

    col3.metric(
        "불량 제품 수",
        f"{total_defect:,.0f}개"
    )

    col4.metric(
        "불량률",
        defect_rate_text
    )

    st.metric(
        "평균 공정 온도",
        f"{avg_temperature:.1f}°C"
        if pd.notna(avg_temperature)
        else "데이터 없음"
    )

    # --------------------------------------------------
    # 생산 목표 달성률
    # --------------------------------------------------

    st.subheader("🎯 생산 목표 달성률")

    target_production = st.number_input(
        "목표 생산량 (개)",
        min_value=1,
        value=10000,
        step=100
    )

    achievement_rate = (
        total_production / target_production * 100
    )

    st.write(
        f"생산 목표 달성률: **{achievement_rate:.1f}%**"
    )

    # 진행률 막대그래프
    st.progress(
        min(achievement_rate, 100) / 100
    )

    if achievement_rate >= 100:
        st.success("생산 목표를 달성했습니다!")
    else:
        st.info("아직 생산 목표에 도달하지 못했습니다.")

    # --------------------------------------------------
    # 설비별 생산량 TOP 10
    # --------------------------------------------------

    st.subheader("설비별 생산량 TOP 10")

    production_by_machine = (
        filtered_df.groupby("machine_id")["production_count"]
        .sum()
        .reset_index()
    )

    production_by_machine = production_by_machine.sort_values(
        "production_count",
        ascending=False
    ).head(10)

    fig = px.bar(
        production_by_machine,
        x="machine_id",
        y="production_count",
        text="production_count",
        title="설비별 생산량 TOP 10",
        labels={
            "machine_id": "설비번호",
            "production_count": "생산량 (개)"
        }
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------
    # CSV 데이터 정보
    # --------------------------------------------------

    st.subheader("📁 생산 데이터 정보")

    col1, col2 = st.columns(2)

    col1.metric(
        "조회 데이터 행 수",
        f"{len(filtered_df):,}행"
    )

    col2.metric(
        "데이터 컬럼 수",
        f"{len(filtered_df.columns)}개"
    )

    st.write(
        f"조회 시작 시간: {filtered_df['timestamp'].min()}"
    )

    st.write(
        f"조회 종료 시간: {filtered_df['timestamp'].max()}"
    )

    # --------------------------------------------------
    # 생산 기록 조회
    # --------------------------------------------------

    st.subheader("📋 생산 기록 조회")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 7. 품질 관리 메뉴
# --------------------------------------------------

elif menu == "품질 관리":

    st.title("🔍 품질 관리")

    # --------------------------------------------------
    # 설비별 생산량과 불량량 집계
    # --------------------------------------------------

    quality_df = (
        df.groupby(
            "machine_id",
            dropna=False
        )[
            ["production_count", "defect_count"]
        ]
        .sum()
        .reset_index()
    )

    # --------------------------------------------------
    # 설비별 불량률 계산
    # --------------------------------------------------

    # 생산량이 0보다 큰 경우에만 불량률 계산
    quality_df["불량률(%)"] = quality_df.apply(
        lambda row: (
            row["defect_count"] /
            row["production_count"] * 100
            if row["production_count"] > 0
            else None
        ),
        axis=1
    )

    # --------------------------------------------------
    # 전체 품질 현황
    # --------------------------------------------------

    st.subheader("전체 품질 현황")

    total_production = quality_df["production_count"].sum()
    total_defect = quality_df["defect_count"].sum()

    if total_production > 0:
        total_defect_rate = (
            total_defect / total_production * 100
        )
        total_defect_rate_text = f"{total_defect_rate:.2f}%"
    else:
        total_defect_rate_text = "계산 불가"

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "전체 생산량",
        f"{total_production:,.0f}개"
    )

    col2.metric(
        "전체 불량 수량",
        f"{total_defect:,.0f}개"
    )

    col3.metric(
        "전체 불량률",
        total_defect_rate_text
    )

    # --------------------------------------------------
    # 설비별 불량률 TOP 10 그래프
    # --------------------------------------------------

    st.subheader("설비별 불량률 TOP 10")

    # 생산량이 0인 설비는 그래프에서 제외
    defect_rate_df = quality_df[
        quality_df["production_count"] > 0
    ].copy()

    # 불량률이 높은 순서로 정렬
    defect_rate_df = defect_rate_df.sort_values(
        "불량률(%)",
        ascending=False
    )

    # 상위 10개 설비만 선택
    top10_df = defect_rate_df.head(10).copy()

    if top10_df.empty:
        st.warning(
            "불량률을 계산할 수 있는 설비가 없습니다."
        )

    else:
        # 막대 위에 표시할 불량률 문자열
        top10_df["불량률 표시"] = (
            top10_df["불량률(%)"].map(
                lambda x: f"{x:.2f}%"
            )
        )

        # Plotly 막대그래프 생성
        fig = px.bar(
            top10_df,
            x="machine_id",
            y="불량률(%)",
            text="불량률 표시",
            title="설비별 불량률 TOP 10",
            labels={
                "machine_id": "설비번호",
                "불량률(%)": "불량률(%)"
            }
        )

        # 막대 위에 불량률 표시
        fig.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        # 그래프 디자인 설정
        fig.update_layout(
            xaxis_title="설비번호",
            yaxis_title="불량률(%)",
            yaxis_ticksuffix="%",
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        # 그래프 화면 출력
        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------
    # 설비별 품질 분석 데이터 표
    # --------------------------------------------------

    st.subheader("설비별 품질 분석")

    # 화면에 표시할 데이터 복사
    quality_table = quality_df[
        [
            "machine_id",
            "production_count",
            "defect_count",
            "불량률(%)"
        ]
    ].copy()

    # 컬럼명 변경
    quality_table = quality_table.rename(
        columns={
            "machine_id": "설비번호",
            "production_count": "총생산량",
            "defect_count": "불량 수량",
            "불량률(%)": "불량률"
        }
    )

    # 생산량과 불량 수량에 천 단위 쉼표 표시
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

    # 불량률 소수점 둘째 자리 표시
    quality_table["불량률"] = (
        quality_table["불량률"].map(
            lambda x: (
                f"{x:.2f}%"
                if pd.notna(x)
                else "계산 불가"
            )
        )
    )

    # 품질 분석 표 출력
    st.dataframe(
        quality_table,
        use_container_width=True,
        hide_index=True
    )

    # 분석된 설비 개수
    machine_count = len(quality_df)

    st.info(
        f"분석된 전체 설비 개수: {machine_count}대"
    )


# --------------------------------------------------
# 8. 설비 모니터링 메뉴
# --------------------------------------------------

elif menu == "설비 모니터링":

    st.title("⚙️ 설비 모니터링")

    # 평균 온도와 습도 계산
    avg_temperature = df["temperature"].mean()
    avg_humidity = df["humidity"].mean()

    col1, col2 = st.columns(2)

    col1.metric(
        "평균 설비 온도",
        f"{avg_temperature:.1f}°C"
        if pd.notna(avg_temperature)
        else "데이터 없음"
    )

    col2.metric(
        "평균 설비 습도",
        f"{avg_humidity:.1f}%"
        if pd.notna(avg_humidity)
        else "데이터 없음"
    )

    st.subheader("설비별 모니터링 데이터")

    monitoring_columns = [
        "timestamp",
        "machine_id",
        "temperature",
        "humidity",
        "operating_status"
    ]

    st.dataframe(
        df[monitoring_columns],
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 9. 데이터 관리 메뉴
# --------------------------------------------------

elif menu == "데이터 관리":

    st.title("📁 데이터 관리")

    st.subheader("전체 생산 데이터")

    # 전체 데이터 표시
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # CSV 다운로드
    csv_data = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="CSV 데이터 다운로드",
        data=csv_data,
        file_name="production_data.csv",
        mime="text/csv"
    )
