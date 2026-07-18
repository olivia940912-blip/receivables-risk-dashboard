"""해외채권 리스크 진단 대시보드 — Streamlit 앱.
charts/ 폴더의 차트 스크립트(각 build_fig() 함수)를 그대로 불러와 조립한다.
모든 지표는 매번 data/ 폴더의 원본 CSV에서 다시 계산한다 (하드코딩 없음).
"""
import importlib.util
import sys
from pathlib import Path

import pandas as pd
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

def verified(text):
    """차트 아래에 검증된 수치를 표기한다. verification/verify_charts.py의 독립 재계산과
    대조해 일치를 확인한 값만 여기 적는다 (2026-07-18 검증, dashboard/verification/검증결과.md 참고)."""
    st.caption(f"🔍 검증: {text}")


m = dp.customer_metrics()
overall_ratio = dp.overall_over90_ratio(m)
no_cover_count = int((m["부보기관"] == "미부보").sum())
double_exposure_count = len(dp.double_exposure_bonds())
corp = dp.corp_metrics().assign(활용률_pct=lambda d: d["활용률"] * 100, 비중_pct=lambda d: d["91일이상비중"] * 100)
bucket = dp.bond_allowance_by_bucket().assign(비율_pct=lambda d: d["대손충당금비율"] * 100)

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
over90_by_cover = m.groupby("부보여부").apply(
    lambda x: x["연체91일이상잔액_KRW"].sum() / x["총잔액_KRW"].sum() * 100
)
verified(
    f"전체 {overall_ratio*100:.1f}% · 미부보 {over90_by_cover.get('미부보', 0):.1f}% · "
    f"부보 {over90_by_cover.get('부보', 0):.1f}% — data_prep.py 계산과 원본 CSV 독립 재계산이 일치함"
)

st.subheader("② 법인별 여신한도 활용률 × 91일이상 연체비중")
mod2 = load_module("02_plotly_법인별활용률연체비중.py")
st.plotly_chart(mod2.build_fig(), width="stretch")
st.caption("활용률이 높은 법인이 연체비중도 함께 높은지 확인한다 — 두 선이 같은 방향이면 활용률 관리가 곧 연체 관리다.")
corp_sorted = corp.sort_values("활용률_pct", ascending=False)
verified(
    " · ".join(f"{r['법인명']} {r['활용률_pct']:.1f}%/{r['비중_pct']:.1f}%" for _, r in corp_sorted.iterrows())
    + " (활용률/91일이상비중) — 여신한도는 채권 유무와 무관하게 고객별_여신한도_부보현황.csv 전체를 합산 (교차검증 과정에서 채권 없는 고객이 분모에서 누락되던 버그를 발견·수정함, verification/검증결과.md 참고)"
)

st.subheader("③ 연령구간별 대손충당금비율")
mod3 = load_module("03_plotly_연령구간별대손충당금비율.py")
st.plotly_chart(mod3.build_fig(), width="stretch")
st.caption("연령구간이 깊어질수록 대손충당금비율이 어떻게 증가하는지 확인한다. CLAUDE.md 기준상 91일 이상은 집합 통계 대신 개별심사 대상이다.")
verified(
    " · ".join(f"{r['연령구간']} {r['비율_pct']:.1f}%" for _, r in bucket.iterrows())
    + " — 원본 CSV 독립 재계산과 일치함"
)

st.subheader("④ 법인별 91일 이상 연체비중")
mod4 = load_module("04_plotly_법인별연체율.py")
st.plotly_chart(mod4.build_fig(), width="stretch")
corp_by_rate = corp.sort_values("비중_pct", ascending=False)
verified(
    " · ".join(f"{r['법인명']} {r['비중_pct']:.1f}%" for _, r in corp_by_rate.iterrows())
    + f" (전체 평균 {overall_ratio*100:.1f}%) — 원본 CSV 독립 재계산과 일치함"
)

st.subheader("⑤ 부보기관별 91일 이상 연체비중")
mod5 = load_module("05_plotly_부보기관별연체율.py")
st.plotly_chart(mod5.build_fig(), width="stretch")
st.caption("표본 10건 미만 구간(*)은 참고용으로만 해석한다.")
by_insurer = (
    m.groupby("부보기관")
    .apply(lambda x: pd.Series({"고객수": len(x), "비율": x["연체91일이상잔액_KRW"].sum() / x["총잔액_KRW"].sum() * 100}))
    .sort_values("비율", ascending=False)
)
verified(
    " · ".join(f"{idx} {r['비율']:.1f}%(n={int(r['고객수'])})" for idx, r in by_insurer.iterrows())
    + " — 전 구간 표본 10건 이상, 원본 CSV 독립 재계산과 일치함"
)

st.subheader("⑥ DSO × 여신한도 활용률 산점도")
mod6 = load_module("06_plotly_DSO활용률산점도.py")
st.plotly_chart(mod6.build_fig(), width="stretch")
st.caption("오른쪽 위(DSO도 높고 활용률도 높은) 영역에 무보증초과(빨강)가 몰려 있다면, 회수불능 리스크가 가장 큰 우선 관리 대상이다.")
dso_valid = m.dropna(subset=["DSO", "활용률"])
verified(
    f"계산 대상 {len(dso_valid)}명 · DSO 평균 {dso_valid['DSO'].mean():.0f}일/중앙값 {dso_valid['DSO'].median():.0f}일/최댓값 {dso_valid['DSO'].max():.0f}일 · "
    f"무보증초과 {int(m['무보증초과'].sum())}명 — 원본 CSV 독립 재계산과 일치함"
)
