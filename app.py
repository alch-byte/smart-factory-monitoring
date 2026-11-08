
import streamlit as st
import pandas as pd
import os
import plotly.express as px


# ==========================================
# 1. 기본 페이지 설정
# ==========================================

st.set_page_config(
    page_title="스마트공장 생산 모니터링",
    page_icon="🏭",
    layout="wide"
)


# ==========================================
# 2. 화면 디자인 설정
# ==========================================

st.markdown("""
<style>
    .main {
        background-color: #F5F7FA;
    }

    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
    }

    h1 {
        color: #1E3A5F;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. 사이드바 메뉴 설정
# ==========================================

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


# ==========================================
# 4. CSV 파일 연결
# ==========================================

st.sidebar.markdown("---")
st.sidebar.subheader("📁 데이터 연결")

file_name = "production_data.csv"

df = None

# 현재 폴더에 CSV 파일이 있는지 확인
if os.path.exists(file_name):

    # CSV 파일 읽기
    df = pd.read_csv(file_name)

    st.sidebar.success("CSV 파일 연결 완료")

else:

    # CSV 파일이 없으면 업로드 기능 제공
    uploaded_file = st.sidebar.file_uploader(
        "CSV 파일 업로드",
        type=["csv"]
    )

    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)

        st.sidebar.success("파일 업로드 완료")


# ==========================================
# 5. 데이터 전처리
# ==========================================

if df is not None:

    # 원본 데이터 보호를 위해 복사본 생성
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

        st.error(
            f"CSV 파일에 필요한 컬럼이 없습니다: {missing_columns}"
        )

        df = None

    else:

        # 날짜 및 시간 형식으로 변환
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        # 날짜 변환에 실패한 데이터 제거
        df = df.dropna(subset=["timestamp"]).copy()

        # 생산량과 불량 수량을 숫자 형식으로 변환
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

        # 시간 순서대로 정렬
        df = df.sort_values("timestamp")


# ==========================================
# 6. 생산 현황 메뉴
# ==========================================

if menu == "생산 현황":

    st.title("📊 생산 현황")

    st.markdown(
        "스마트공장 생산 데이터를 모니터링합니다."
    )

    if df is not None and len(df) > 0:

        # ----------------------------------
        # 6-1. 데이터 필터 설정
        # ----------------------------------

        st.subheader("🔎 생산 데이터 검색")

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        # 설비 목록 자동 생성
        machine_list = sorted(
            df["machine_id"].dropna().unique().tolist(),
            key=str
        )

        # 전체 설비를 기본값으로 설정
        machine_options = ["전체"] + machine_list

        # 설비번호 선택
        selected_machine = filter_col1.selectbox(
            "설비번호 선택",
            machine_options
        )

        # 데이터의 최소 및 최대 날짜 확인
        min_date = df["timestamp"].min().date()
        max_date = df["timestamp"].max().date()

        # 시작 날짜 선택
        start_date = filter_col2.date_input(
            "시작 날짜",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )

        # 종료 날짜 선택
        end_date = filter_col3.date_input(
            "종료 날짜",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )

        st.markdown("---")

        # ----------------------------------
        # 6-2. 날짜 오류 확인
        # ----------------------------------

        if start_date > end_date:

            st.error(
                "시작 날짜가 종료 날짜보다 늦습니다. "
                "날짜를 다시 선택해주세요."
            )

        else:

            # ----------------------------------
            # 6-3. 데이터 필터링
            # ----------------------------------

            # 원본 데이터와 분리된 필터용 데이터 생성
            filtered_df = df.copy()

            # 설비번호 필터링
            if selected_machine != "전체":

                filtered_df = filtered_df[
                    filtered_df["machine_id"] == selected_machine
                ]

            # 날짜 필터링
            start_datetime = pd.Timestamp(start_date)

            # 종료 날짜의 다음 날 0시
            end_datetime = (
                pd.Timestamp(end_date) + pd.Timedelta(days=1)
            )

            filtered_df = filtered_df[
                (filtered_df["timestamp"] >= start_datetime) &
                (filtered_df["timestamp"] < end_datetime)
            ].copy()

            # 조회 조건 표시
            st.info(
                f"선택 설비: {selected_machine} | "
                f"조회 기간: {start_date} ~ {end_date} | "
                f"조회 데이터: {len(filtered_df):,}건"
            )

            # ----------------------------------
            # 6-4. 조회 데이터가 없는 경우
            # ----------------------------------

            if len(filtered_df) == 0:

                st.warning(
                    "선택한 조건에 해당하는 데이터가 없습니다. "
                    "설비 또는 날짜를 변경해주세요."
                )

            else:

                # ----------------------------------
                # 6-5. 생산 데이터 계산
                # ----------------------------------

                # 전체 생산량
                total_production = filtered_df[
                    "production_count"
                ].sum()

                # 불량 제품 수
                total_defect = filtered_df[
                    "defect_count"
                ].sum()

                # 정상 제품 수
                total_normal = (
                    total_production - total_defect
                )

                # 불량률 계산
                if total_production > 0:

                    defect_rate = (
                        total_defect / total_production
                    ) * 100

                else:

                    defect_rate = 0

                # 평균 공정 온도
                avg_temperature = filtered_df[
                    "temperature"
                ].mean()

                # ----------------------------------
                # 6-6. 생산 현황 KPI 카드
                # ----------------------------------

                st.subheader("📌 생산 현황 주요 지표")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "총생산량",
                    f"{total_production:,.0f}개"
                )

                col2.metric(
                    "정상 제품",
                    f"{total_normal:,.0f}개"
                )

                col3.metric(
                    "불량 제품",
                    f"{total_defect:,.0f}개"
                )

                col4.metric(
                    "불량률",
                    f"{defect_rate:.2f}%"
                )

                # ----------------------------------
                # 6-7. 생산 목표 달성률
                # ----------------------------------

                st.markdown("---")

                st.subheader("🎯 생산 목표 달성 현황")

                # 목표 생산량 입력
                goal_col1, goal_col2 = st.columns(2)

                target_production = goal_col1.number_input(
                    "목표 생산량 (개)",
                    min_value=1,
                    value=10000,
                    step=100
                )

                # 목표 달성률 계산
                achievement_rate = (
                    total_production / target_production
                ) * 100

                # 목표 생산량과 실제 생산량 표시
                goal_col2.metric(
                    "실제 생산량",
                    f"{total_production:,.0f}개"
                )

                # 목표 달성률 숫자 표시
                st.metric(
                    "목표 달성률",
                    f"{achievement_rate:.1f}%"
                )

                # 진행률 막대는 최대 100%까지만 표시
                progress_rate = min(
                    achievement_rate,
                    100
                )

                st.progress(
                    progress_rate / 100
                )

                # 달성 상태 안내
                if achievement_rate >= 100:

                    st.success(
                        f"목표 달성! 목표 생산량을 "
                        f"{achievement_rate - 100:.1f}% 초과했습니다."
                        if achievement_rate > 100
                        else "목표 생산량을 달성했습니다!"
                    )

                else:

                    st.info(
                        f"목표 달성까지 "
                        f"{100 - achievement_rate:.1f}% 남았습니다."
                    )

                # ----------------------------------
                # 6-8. 평균 공정 온도
                # ----------------------------------

                st.markdown("---")

                st.subheader("🌡️ 공정 환경 지표")

                temp_col1, temp_col2, temp_col3 = st.columns(3)

                temp_col2.metric(
                    "평균 공정 온도",
                    f"{avg_temperature:.2f} ℃"
                    if pd.notna(avg_temperature) else "-"
                )

                # ----------------------------------
                # 6-9. 설비별 생산량 그래프
                # ----------------------------------

                st.markdown("---")

                st.subheader("📈 설비별 생산량")

                # 설비별 생산량 합계 계산
                machine_production = (
                    filtered_df.groupby("machine_id")[
                        "production_count"
                    ]
                    .sum()
                    .reset_index()
                )

                # Plotly 막대그래프 생성
                fig = px.bar(
                    machine_production,
                    x="machine_id",
                    y="production_count",
                    title="설비별 생산량 비교",
                    labels={
                        "machine_id": "설비번호",
                        "production_count": "생산량"
                    },
                    text="production_count"
                )

                # 그래프 디자인 설정
                fig.update_traces(
                    texttemplate="%{text:,.0f}",
                    textposition="outside"
                )

                fig.update_layout(
                    xaxis_title="설비번호",
                    yaxis_title="생산량",
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )

                # 그래프 표시
                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                # ----------------------------------
                # 6-10. 데이터 기본 정보
                # ----------------------------------

                st.markdown("---")

                st.subheader("📋 데이터 기본 정보")

                info1, info2, info3, info4 = st.columns(4)

                info1.metric(
                    "전체 데이터 개수",
                    f"{len(filtered_df):,}건"
                )

                info2.metric(
                    "전체 컬럼 개수",
                    f"{len(filtered_df.columns)}개"
                )

                info3.metric(
                    "데이터 시작 시간",
                    filtered_df["timestamp"].min().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

                info4.metric(
                    "데이터 종료 시간",
                    filtered_df["timestamp"].max().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

                # ----------------------------------
                # 6-11. 처음 10개 데이터
                # ----------------------------------

                st.markdown("---")

                st.subheader("📄 처음 10개 데이터")

                st.dataframe(
                    filtered_df.head(10),
                    use_container_width=True,
                    hide_index=True
                )


    else:

        st.warning(
            "CSV 파일이 없거나 유효한 날짜 데이터가 없습니다. "
            "왼쪽 사이드바에서 production_data.csv 파일을 확인해주세요."
        )


# ==========================================
# 7. 품질 관리 메뉴
# ==========================================

elif menu == "품질 관리":

    st.title("🔍 품질 관리")

    if df is not None:

        total_production = df["production_count"].sum()
        total_defect = df["defect_count"].sum()

        if total_production > 0:

            defect_rate = (
                total_defect / total_production
            ) * 100

        else:

            defect_rate = 0

        col1, col2 = st.columns(2)

        col1.metric(
            "총 불량 수량",
            f"{total_defect:,.0f}개"
        )

        col2.metric(
            "불량률",
            f"{defect_rate:.2f}%"
        )

        st.markdown("---")

        st.subheader("불량 데이터")

        st.dataframe(
            df[df["defect_count"] > 0],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning("먼저 CSV 파일을 연결해주세요.")


# ==========================================
# 8. 설비 모니터링 메뉴
# ==========================================

elif menu == "설비 모니터링":

    st.title("⚙️ 설비 모니터링")

    if df is not None:

        col1, col2 = st.columns(2)

        avg_temperature = df["temperature"].mean()
        avg_humidity = df["humidity"].mean()

        col1.metric(
            "평균 온도",
            f"{avg_temperature:.2f} ℃"
            if pd.notna(avg_temperature) else "-"
        )

        col2.metric(
            "평균 습도",
            f"{avg_humidity:.2f} %"
            if pd.notna(avg_humidity) else "-"
        )

        st.markdown("---")

        st.subheader("설비 가동 상태")

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

    else:

        st.warning("먼저 CSV 파일을 연결해주세요.")


# ==========================================
# 9. 데이터 관리 메뉴
# ==========================================

elif menu == "데이터 관리":

    st.title("📁 데이터 관리")

    if df is not None:

        st.subheader("전체 데이터")

        st.write(
            f"전체 데이터: {len(df):,}건"
        )

        # 전체 데이터 표시
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        # CSV 다운로드
        csv_data = df.to_csv(
            index=False,
            encoding="utf-8-sig"
        )

        st.download_button(
            label="📥 CSV 데이터 다운로드",
            data=csv_data,
            file_name="production_data_download.csv",
            mime="text/csv"
        )

    else:

        st.warning("먼저 CSV 파일을 연결해주세요.")
