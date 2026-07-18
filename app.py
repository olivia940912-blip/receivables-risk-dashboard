"""해외채권 리스크 진단 대시보드 — Streamlit 앱.
charts/ 폴더의 차트 스크립트(각 build_fig() 함수)를 그대로 불러와 조립한다.
모든 지표는 매번 data/ 폴더의 원본 CSV에서 다시 계산한다 (하드코딩 없음).
"""
import importlib.util
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
CHARTS_DIR = BASE_DIR / "charts"
sys.path.insert(0, str(CHARTS_DIR))

import data_prep as dp


def load_module(filename):
    spec = importlib.util.spec_from_file_location(filename, CHARTS_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


st.set_page_config(page_title="해외채권 리스크 진단 대시보드", layout="wide")
st.title("채권은 왜 안 걷히는가 — 해외채권 리스크 진단 대시보드")

m = dp.customer_metrics()
overall_ratio = dp.overall_over90_ratio(m)
no_cover_count = int((m["부보기관"] == "미부보").sum())
double_exposure_count = len(dp.double_exposure_bonds())

c1, c2, c3, c4 = st.columns(4)
c1.metric("전체 채권잔액", f"{m['총잔액_KRW'].sum() / 1e8:,.0f}억원")
c2.metric("91일 이상 연체비중", f"{overall_ratio * 100:.1f}%")
c3.metric("무보증 고객 수", f"{no_cover_count}명")
c4.metric("이중 익스포저 채권 수", f"{double_exposure_count}건")

st.divider()
st.subheader("① 부보여부로 본 연체 위험 — matplotlib vs Plotly 비교")
col_mpl, col_plotly = st.columns(2)
with col_mpl:
    st.caption("matplotlib (정적 이미지)")
    mpl_mod = load_module("01_matplotlib_부보연체비교.py")
    st.pyplot(mpl_mod.build_fig())
with col_plotly:
    st.caption("Plotly (인터랙티브 — 마우스를 올려보세요)")
    plotly1_mod = load_module("01_plotly_부보연체비교.py")
    st.plotly_chart(plotly1_mod.build_fig(), width="stretch")
st.caption("미부보 고객의 91일 이상 연체비중이 전체 평균보다 높다면, 리스크 이전 수단 부재가 연체 장기화와 함께 움직인다는 신호다.")

st.subheader("② 법인별 여신한도 활용률 × 91일이상 연체비중")
mod2 = load_module("02_plotly_법인별활용률연체비중.py")
st.plotly_chart(mod2.build_fig(), width="stretch")
st.caption("활용률이 높은 법인이 연체비중도 함께 높은지 확인한다 — 두 선이 같은 방향이면 활용률 관리가 곧 연체 관리다.")

st.subheader("③ 연령구간별 대손충당금비율")
mod3 = load_module("03_plotly_연령구간별대손충당금비율.py")
st.plotly_chart(mod3.build_fig(), width="stretch")
st.caption("연령구간이 깊어질수록 대손충당금비율이 어떻게 증가하는지 확인한다. CLAUDE.md 기준상 91일 이상은 집합 통계 대신 개별심사 대상이다.")

st.subheader("④ 법인별 91일 이상 연체비중")
mod4 = load_module("04_plotly_법인별연체율.py")
st.plotly_chart(mod4.build_fig(), width="stretch")

st.subheader("⑤ 부보기관별 91일 이상 연체비중")
mod5 = load_module("05_plotly_부보기관별연체율.py")
st.plotly_chart(mod5.build_fig(), width="stretch")
st.caption("표본 10건 미만 구간(*)은 참고용으로만 해석한다.")

st.subheader("⑥ DSO × 여신한도 활용률 산점도")
mod6 = load_module("06_plotly_DSO활용률산점도.py")
st.plotly_chart(mod6.build_fig(), width="stretch")
st.caption("오른쪽 위(DSO도 높고 활용률도 높은) 영역에 무보증초과(빨강)가 몰려 있다면, 회수불능 리스크가 가장 큰 우선 관리 대상이다.")
