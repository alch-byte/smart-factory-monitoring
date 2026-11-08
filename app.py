
# ==========================================
# 1. 필요한 라이브러리 불러오기
# ==========================================
import streamlit as st
import pandas as pd
import plotly.express as px
import os


# ==========================================
# 2. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="스마트공장 생산 모니터링",
    page_icon="🏭",
    layout="wide"
)


# ==========================================
# 3. 화면 디자인 설정
# ==========================================
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


# ==========================================
# 4. 프로그램 제목
# ==========================================
st.title("🏭 스마트공장 생산 모니터링")
st.markdown("---")


# ==========================================
# 5. 사이드바 메뉴 구성
# ==========================================
menu = st.sidebar.radio(
    "메뉴 선택",
    [
        "생산 현황",
        "품질 관리",
        "설비 모니터링",
        "데이터 관리"
    ]
)


# ==========================================
# 6. CSV 데이터 불러오기
# ==========================================
file_name = "production_data.csv"

# 현재 작업 폴더에 CSV 파일이 있는지 확인
if os.path.exists(file_name):

    df = pd.read_csv(file_name)

else:
    # 파일이 없으면 사용자가 CSV 파일을 업로드
    uploaded_file = st.sidebar.file_uploader(
        "생산 데이터 CSV 파일 업로드",
        type=["csv"]
    )

    if uploaded_file is None:
        st.info("production_data.csv 파일을 업로드해주세요.")
        st.stop()

    df = pd.read_csv(uploaded_file)


# ==========================================
# 7. 데이터 전처리
# ==========================================

# 원본 데이터를 보호하기 위해 복사
df = df.copy()

# 분석에 필요한 컬럼 목록
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

# CSV에 필요한 컬럼이 있는지 확인
missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        f"CSV 파일에 필요한 컬럼이 없습니다: {missing_columns}"
    )
    st.stop()

# 날짜 데이터를 날짜 형식으로 변환
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

# 날짜 변환에 실패한 행 제거
df = df.dropna(subset=["timestamp"])

# 생산량과 불량량을 숫자 형식으로 변환
df["production_count"] = pd.to_numeric(
    df["production_count"],
    errors="coerce"
).fillna(0)

df["defect_count"] = pd.to_numeric(
    df["defect_count"],
    errors="coerce"
).fillna(0)

# 온도와 습도를 숫자 형식으로 변환
df["temperature"] = pd.to_numeric(
    df["temperature"],
    errors="coerce"
)

df["humidity"] = pd.to_numeric(
    df["humidity"],
    errors="coerce"
)

# 날짜순으로 정렬
df = df.sort_values("timestamp")


# ==========================================
# 8. 생산 현황 메뉴
# ==========================================
if menu == "생산 현황":

    st.header("📊 생산 현황")

    # --------------------------------------
    # 8-1. 설비 및 날짜 필터
    # --------------------------------------

    if df.empty:
        st.warning("조회할 생산 데이터가 없습니다.")
        st.stop()

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    # CSV에 있는 설비 목록 가져오기
    machine_list = sorted(
        df["machine_id"].dropna().unique().tolist(),
        key=str
    )

    # 전체 설비 옵션 추가
    machine_options = ["전체"] + machine_list

    selected_machine = filter_col1.selectbox(
        "설비번호 선택",
        machine_options
    )

    # 데이터의 시작 날짜와 종료 날짜
    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()

    start_date = filter_col2.date_input(
        "시작일",
        value=min_date
    )

    end_date = filter_col3.date_input(
        "종료일",
        value=max_date
    )

    # 시작일이 종료일보다 늦은 경우 확인
    if start_date > end_date:
        st.error("시작일은 종료일보다 늦을 수 없습니다.")
        st.stop()

    # --------------------------------------
    # 8-2. 설비 및 날짜 필터 적용
    # --------------------------------------

    # 원본 데이터 복사
    filtered_df = df.copy()

    # 선택한 설비만 필터링
    if selected_machine != "전체":

        filtered_df = filtered_df[
            filtered_df["machine_id"] == selected_machine
        ]

    # 선택한 날짜 범위 필터링
    # 종료일의 마지막 시간까지 포함하기 위해 하루를 더함
    filtered_df = filtered_df[
        (filtered_df["timestamp"] >= pd.Timestamp(start_date)) &
        (filtered_df["timestamp"] < (
            pd.Timestamp(end_date) + pd.Timedelta(days=1)
        ))
    ]

    # 필터 결과가 없는 경우
    if filtered_df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        st.stop()

    # --------------------------------------
    # 8-3. 주요 생산 지표 계산
    # --------------------------------------

    # 총생산량
    total_production = filtered_df["production_count"].sum()

    # 불량 제품 수량
    total_defect = filtered_df["defect_count"].sum()

    # 정상 제품 수량
    normal_production = total_production - total_defect

    # 전체 불량률
    if total_production > 0:
        defect_rate = total_defect / total_production * 100
    else:
        defect_rate = 0

    # 평균 공정 온도
    avg_temperature = filtered_df["temperature"].mean()

    # --------------------------------------
    # 8-4. 주요 생산 지표 화면 표시
    # --------------------------------------

    st.subheader("📌 주요 생산 지표")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "총생산량",
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
        "전체 불량률",
        f"{defect_rate:.2f}%"
    )

    # 평균 공정 온도 표시
    temp_col1, temp_col2, temp_col3 = st.columns(3)

    if pd.notna(avg_temperature):
        temp_col2.metric(
            "평균 공정 온도",
            f"{avg_temperature:.2f} ℃"
        )
    else:
        temp_col2.metric(
            "평균 공정 온도",
            "-"
        )

    # --------------------------------------
    # 8-5. 생산 목표 달성률
    # --------------------------------------

    st.markdown("---")
    st.subheader("🎯 생산 목표 달성 현황")

    goal_col1, goal_col2 = st.columns(2)

    # 사용자가 목표 생산량을 직접 입력
    target_production = goal_col1.number_input(
        "목표 생산량 (개)",
        min_value=1,
        value=10000,
        step=100
    )

    # 현재 선택한 설비와 날짜에 해당하는 실제 생산량
    goal_col2.metric(
        "실제 생산량",
        f"{total_production:,.0f}개"
    )

    # 목표 달성률 계산
    achievement_rate = (
        total_production / target_production
    ) * 100

    # 목표 달성률 숫자 표시
    st.metric(
        "목표 달성률",
        f"{achievement_rate:.1f}%"
    )

    # 진행률 막대는 최대 100%까지만 표시
    progress_rate = min(achievement_rate, 100)

    st.progress(progress_rate / 100)

    # 목표 달성 여부 안내
    if achievement_rate >= 100:

        if achievement_rate > 100:
            st.success(
                f"목표 생산량을 {achievement_rate - 100:.1f}% 초과했습니다."
            )
        else:
            st.success("목표 생산량을 달성했습니다!")

    else:
        st.info(
            f"목표 달성까지 {100 - achievement_rate:.1f}% 남았습니다."
        )

    # --------------------------------------
    # 8-6. 설비별 생산량 TOP 10 그래프
    # --------------------------------------

    st.markdown("---")
    st.subheader("🏭 설비별 생산량 TOP 10")

    # 설비별 생산량 합계 계산
    machine_production = (
        filtered_df
        .groupby("machine_id")["production_count"]
        .sum()
        .reset_index()
    )

    # 생산량이 많은 순서로 정렬하고 상위 10개 선택
    machine_top10 = (
        machine_production
        .sort_values(
            "production_count",
            ascending=False
        )
        .head(10)
    )

    # 설비별 생산량 막대그래프 생성
    fig = px.bar(
        machine_top10,
        x="machine_id",
        y="production_count",
        text="production_count",
        labels={
            "machine_id": "설비번호",
            "production_count": "생산량"
        },
        title="설비별 생산량 TOP 10"
    )

    # 그래프에 생산량 숫자 표시
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

    # --------------------------------------
    # 8-7. CSV 데이터 정보 표시
    # --------------------------------------

    st.markdown("---")
    st.subheader("📋 CSV 데이터 정보")

    info_col1, info_col2, info_col3, info_col4 = st.columns(4)

    info_col1.metric(
        "데이터 행 수",
        f"{len(filtered_df):,}개"
    )

    info_col2.metric(
        "컬럼 수",
        f"{len(filtered_df.columns)}개"
    )

    info_col3.metric(
        "시작 시간",
        str(filtered_df["timestamp"].min())
    )

    info_col4.metric(
        "종료 시간",
        str(filtered_df["timestamp"].max())
    )

    # --------------------------------------
    # 8-8. 생산 기록 조회
    # --------------------------------------

    st.markdown("---")
    st.subheader("🔎 생산 기록 조회")

    # 현재 선택한 설비와 날짜에 해당하는 생산 기록 표시
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 9. 품질 관리 메뉴
# ==========================================
elif menu == "품질 관리":

    # 첫째, 품질 관리 제목 표시
    st.header("🔍 품질 관리")

    # --------------------------------------
    # 9-1. 설비별 생산량과 불량 수량 집계
    # --------------------------------------

    # machine_id를 기준으로 데이터를 그룹화
    # 각 설비의 생산량과 불량 수량을 합산
    # dropna=False는 설비번호가 비어 있는 데이터도 집계하기 위한 설정
    quality_df = (
        df.groupby("machine_id", dropna=False)[
            ["production_count", "defect_count"]
        ]
        .sum()
        .reset_index()
    )

    # --------------------------------------
    # 9-2. 설비별 불량률 계산
    # --------------------------------------

    # 생산량이 0보다 큰 경우에만 불량률 계산
    # 생산량이 0인 경우에는 '계산 불가'로 표시
    quality_df["불량률"] = quality_df.apply(
        lambda row: (
            f"{row['defect_count'] / row['production_count'] * 100:.2f}%"
            if row["production_count"] > 0
            else "계산 불가"
        ),
        axis=1
    )

    # --------------------------------------
    # 9-3. 전체 생산량과 불량 수량 계산
    # --------------------------------------

    total_production = quality_df["production_count"].sum()
    total_defect = quality_df["defect_count"].sum()

    # 전체 생산량이 0보다 큰 경우 전체 불량률 계산
    # 설비별 불량률을 평균 내지 않음
    if total_production > 0:

        total_defect_rate = (
            total_defect / total_production
        ) * 100

        total_defect_rate_text = f"{total_defect_rate:.2f}%"

    else:

        total_defect_rate_text = "계산 불가"

    # --------------------------------------
    # 9-4. 전체 품질 현황 표시
    # --------------------------------------

    st.subheader("📌 전체 품질 현황")

    quality_col1, quality_col2, quality_col3 = st.columns(3)

    quality_col1.metric(
        "전체 생산량",
        f"{total_production:,.0f}개"
    )

    quality_col2.metric(
        "전체 불량 수량",
        f"{total_defect:,.0f}개"
    )

    quality_col3.metric(
        "전체 불량률",
        total_defect_rate_text
    )

    # --------------------------------------
    # 9-5. 설비별 품질 분석 표
    # --------------------------------------

    st.markdown("---")
    st.subheader("🏭 설비별 품질 분석")

    # 표에 표시할 컬럼 이름 변경
    quality_table = quality_df.rename(
        columns={
            "machine_id": "설비번호",
            "production_count": "총생산량",
            "defect_count": "불량 수량"
        }
    )

    # 생산량과 불량 수량을 정수 형태로 표시
    quality_table["총생산량"] = quality_table["총생산량"].map(
        lambda x: f"{x:,.0f}"
    )

    quality_table["불량 수량"] = quality_table["불량 수량"].map(
        lambda x: f"{x:,.0f}"
    )

    # 설비별 품질 현황 표 출력
    st.dataframe(
        quality_table[
            ["설비번호", "총생산량", "불량 수량", "불량률"]
        ],
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------
    # 9-6. 전체 설비 개수 표시
    # --------------------------------------

    # 그룹화된 설비 데이터의 행 개수 계산
    machine_count = len(quality_df)

    st.markdown("---")

    st.metric(
        "분석된 전체 설비 개수",
        f"{machine_count:,}대"
    )


# ==========================================
# 10. 설비 모니터링 메뉴
# ==========================================
elif menu == "설비 모니터링":

    st.header("⚙️ 설비 모니터링")

    # 평균 온도와 평균 습도 계산
    avg_temperature = df["temperature"].mean()
    avg_humidity = df["humidity"].mean()

    col1, col2 = st.columns(2)

    # 평균 온도 표시
    if pd.notna(avg_temperature):
        col1.metric(
            "평균 설비 온도",
            f"{avg_temperature:.2f} ℃"
        )
    else:
        col1.metric(
            "평균 설비 온도",
            "-"
        )

    # 평균 습도 표시
    if pd.notna(avg_humidity):
        col2.metric(
            "평균 설비 습도",
            f"{avg_humidity:.2f}%"
        )
    else:
        col2.metric(
            "평균 설비 습도",
            "-"
        )

    # 설비 운영 상태 데이터 표시
    st.subheader("설비 운영 상태")

    st.dataframe(
        df[
            [
                "timestamp",
                "machine_id",
                "temperature",
                "humidity",
                "operating_status"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 11. 데이터 관리 메뉴
# ==========================================
elif menu == "데이터 관리":

    st.header("💾 데이터 관리")

    # 전체 생산 데이터 표시
    st.subheader("전체 생산 데이터")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # CSV 다운로드용 데이터 생성
    csv_data = df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    # CSV 다운로드 버튼
    st.download_button(
        label="CSV 데이터 다운로드",
        data=csv_data,
        file_name="production_data_download.csv",
        mime="text/csv"
    )
