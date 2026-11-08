
import streamlit as st

# 브라우저 탭 제목과 화면 너비 설정
st.set_page_config(
    page_title="스마트공장 생산 모니터링 시스템",
    layout="wide"
)

# 프로그램 제목 표시
st.title("스마트공장 생산 모니터링 시스템")

# 프로그램 설명 표시
st.write("""
이 프로그램은 공장의 생산량과 불량률을
확인하기 위한 모니터링 프로그램입니다.
""")

# 생산 현황 영역 제목
st.header("생산 현황")

# 생산 현황 데이터 (예시 숫자를 직접 입력)
total_production = 1000  # 총생산량
normal_products = 950    # 정상 제품
defect_products = 50     # 불량 제품
defect_rate = 5.0        # 불량률(%)
average_temperature = 38 # 평균 공정 온도(℃)

# 첫 번째 줄: 생산량 관련 지표
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="총생산량",
        value=f"{total_production:,}개"
    )

with col2:
    st.metric(
        label="정상 제품",
        value=f"{normal_products:,}개"
    )

with col3:
    st.metric(
        label="불량 제품",
        value=f"{defect_products:,}개"
    )

# 두 번째 줄: 불량률과 공정 온도
col4, col5 = st.columns(2)

with col4:
    st.metric(
        label="불량률",
        value=f"{defect_rate:.1f}%"
    )

with col5:
    st.metric(
        label="평균 공정 온도",
        value=f"{average_temperature}℃"
    )

# 현재 개발 단계 표시
st.subheader("현재 개발 단계")
st.write("생산 현황 표시 기능 추가")
