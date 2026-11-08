
import streamlit as st
import pandas as pd
import os

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
# 3. 사이드바 메뉴
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
# 4. CSV 파일 불러오기
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

    # timestamp를 날짜와 시간 형식으로 변환
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # 날짜 변환에 실패한 데이터 확인
    df = df.dropna(subset=["timestamp"])

    # 시간 순서대로 정렬
    df = df.sort_values("timestamp")


# ==========================================
# 6. 생산 현황 메뉴
# ==========================================

if menu == "생산 현황":

    st.title("📊 생산 현황")
    st.markdown("스마트공장 생산 데이터를 실시간으로 모니터링합니다.")

    if df is not None:

        # 생산 현황 카드
        col1, col2, col3, col4 = st.columns(4)

        total_production = df["production_count"].sum()
        total_defect = df["defect_count"].sum()

        defect_rate = (
            total_defect / total_production * 100
            if total_production > 0 else 0
        )

        machine_count = df["machine_id"].nunique()

        col1.metric(
            "총 생산량",
            f"{total_production:,.0f}개"
        )

        col2.metric(
            "총 불량 수량",
            f"{total_defect:,.0f}개"
        )

        col3.metric(
            "불량률",
            f"{defect_rate:.2f}%"
        )

        col4.metric(
            "가동 설비 수",
            f"{machine_count}대"
        )

        st.markdown("---")

        # 데이터 기본 정보
        st.subheader("📋 데이터 기본 정보")

        info1, info2, info3, info4 = st.columns(4)

        info1.metric(
            "전체 데이터 개수",
            f"{len(df):,}건"
        )

        info2.metric(
            "전체 컬럼 개수",
            f"{len(df.columns)}개"
        )

        info3.metric(
            "데이터 시작 시간",
            df["timestamp"].min().strftime("%Y-%m-%d %H:%M:%S")
        )

        info4.metric(
            "데이터 종료 시간",
            df["timestamp"].max().strftime("%Y-%m-%d %H:%M:%S")
        )

        st.markdown("---")

        # 처음 10개 데이터 표시
        st.subheader("📄 처음 10개 데이터")

        st.dataframe(
            df.head(10),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "CSV 파일이 없습니다. "
            "왼쪽 사이드바에서 production_data.csv 파일을 업로드해주세요."
        )


# ==========================================
# 7. 품질 관리 메뉴
# ==========================================

elif menu == "품질 관리":

    st.title("🔍 품질 관리")

    if df is not None:

        total_production = df["production_count"].sum()
        total_defect = df["defect_count"].sum()

        defect_rate = (
            total_defect / total_production * 100
            if total_production > 0 else 0
        )

        col1, col2 = st.columns(2)

        col1.metric("총 불량 수량", f"{total_defect:,.0f}개")
        col2.metric("불량률", f"{defect_rate:.2f}%")

        st.subheader("불량 데이터")

        st.dataframe(
            df[df["defect_count"] > 0],
            use_container_width=True
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

        col1.metric(
            "평균 온도",
            f"{df['temperature'].mean():.1f} ℃"
        )

        col2.metric(
            "평균 습도",
            f"{df['humidity'].mean():.1f} %"
        )

        st.subheader("설비 가동 상태")

        st.dataframe(
            df[["timestamp", "machine_id", "temperature",
                "humidity", "operating_status"]],
            use_container_width=True
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

        st.write(f"전체 데이터: {len(df):,}건")

        # 전체 CSV 데이터 표시
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # CSV 다운로드 기능
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
