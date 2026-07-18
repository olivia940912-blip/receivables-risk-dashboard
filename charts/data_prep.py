"""공용 데이터 전처리 모듈 — 6개 차트와 app.py가 모두 이 모듈의 함수로 원본 CSV를 읽어 재계산한다.
숫자를 하드코딩하지 않고, 매번 dashboard/data/*.csv에서 직접 계산한다.
"""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

OVER90_BUCKET = "91-180일"
RECENT_MONTHS = ["2025-04", "2025-05", "2025-06"]
DSO_PERIOD_DAYS = 91  # 최근 3개월(4~6월) 기간일수


def _read(name):
    return pd.read_csv(DATA_DIR / name, encoding="utf-8-sig")


def load_raw():
    return {
        "ar": _read("해외법인_채권잔액_연령별_202506.csv"),
        "credit": _read("고객별_여신한도_부보현황.csv"),
        "allowance": _read("연체채권_대손충당금_202506.csv"),
        "factoring": _read("법인별_고객별_채권팩토링_실행내역.csv"),
        "revenue": _read("거래선별_매출_지급조건_월별.csv"),
        "collection": _read("채권회수내역_월별_202501_202506.csv"),
    }


def customer_metrics():
    """고객 단위: 채권잔액, 91일이상 비중, 여신한도 활용률, 부보여부, DSO, 무보증초과 여부."""
    raw = load_raw()
    ar, credit, revenue = raw["ar"], raw["credit"], raw["revenue"]

    bal = ar.groupby(["고객ID", "법인명"], as_index=False).agg(
        채권건수=("채권ID", "count"),
        총잔액_KRW=("잔액_KRW", "sum"),
    )
    over90 = (
        ar[ar["연령구간"] == OVER90_BUCKET]
        .groupby("고객ID", as_index=False)["잔액_KRW"]
        .sum()
        .rename(columns={"잔액_KRW": "연체91일이상잔액_KRW"})
    )
    m = bal.merge(over90, on="고객ID", how="left")
    m["연체91일이상잔액_KRW"] = m["연체91일이상잔액_KRW"].fillna(0)
    m["연체91일이상비중"] = m["연체91일이상잔액_KRW"] / m["총잔액_KRW"]

    m = m.merge(
        credit[["고객ID", "부보기관", "여신한도_KRW", "자기부담율"]], on="고객ID", how="left"
    )
    m["부보여부"] = m["부보기관"].apply(lambda x: "미부보" if x == "미부보" else "부보")
    m["활용률"] = m["총잔액_KRW"] / m["여신한도_KRW"]
    m["무보증초과"] = (m["활용률"] > 1.0) & (m["부보기관"] == "미부보")

    rev3 = revenue[revenue["기준월"].isin(RECENT_MONTHS)]
    avg_rev = (
        rev3.groupby("고객ID", as_index=False)["매출액_KRW"]
        .mean()
        .rename(columns={"매출액_KRW": "최근3개월평균매출_KRW"})
    )
    m = m.merge(avg_rev, on="고객ID", how="left")
    m["DSO"] = m["총잔액_KRW"] / m["최근3개월평균매출_KRW"] * DSO_PERIOD_DAYS

    return m


def corp_metrics():
    """법인 단위 여신한도 활용률 × 91일이상비중.

    customer_metrics()를 법인별로 그룹핑해 합산하면 안 된다 — customer_metrics()는
    ar(채권잔액)에 존재하는 고객만 포함하므로, 채권이 하나도 없지만 여신한도는
    배정된 고객(예: OC101, OC116, OC190)의 한도가 분모에서 누락되어 활용률이
    실제보다 높게 나온다(검증 과정에서 독일법인 83.2%→83.0%, 중국법인 81.1%→81.0%로
    드러남). 따라서 여신한도는 고객별_여신한도_부보현황.csv 전체를 법인별로 직접
    합산한다.
    """
    raw = load_raw()
    ar, credit = raw["ar"], raw["credit"]

    bal = ar.groupby("법인명")["잔액_KRW"].sum().rename("총잔액_KRW")
    over90 = (
        ar[ar["연령구간"] == OVER90_BUCKET].groupby("법인명")["잔액_KRW"].sum().rename("91일이상잔액_KRW")
    )
    limit = credit.groupby("법인명")["여신한도_KRW"].sum().rename("여신한도_KRW")

    df = pd.concat([bal, over90, limit], axis=1).fillna(0)
    df["활용률"] = df["총잔액_KRW"] / df["여신한도_KRW"]
    df["91일이상비중"] = df["91일이상잔액_KRW"] / df["총잔액_KRW"]
    return df.reset_index().rename(columns={"index": "법인명"})


def overall_over90_ratio(m=None):
    """전체 평균 91일이상 잔액 비중 (기준선용)."""
    if m is None:
        m = customer_metrics()
    return m["연체91일이상잔액_KRW"].sum() / m["총잔액_KRW"].sum()


def bond_allowance_by_bucket():
    """연령구간별 채권잔액 합계, 대손충당금 합계, 대손충당금비율."""
    raw = load_raw()
    ar, allowance = raw["ar"], raw["allowance"]
    bucket_order = ["정상(미도래)", "1-30일", "31-60일", "61-90일", OVER90_BUCKET]

    bal = ar.groupby("연령구간", as_index=False)["잔액_KRW"].sum().rename(
        columns={"잔액_KRW": "채권잔액_KRW"}
    )
    allw = allowance.groupby("연령구간", as_index=False)["대손충당금_KRW"].sum()
    df = bal.merge(allw, on="연령구간", how="left")
    df["대손충당금_KRW"] = df["대손충당금_KRW"].fillna(0)
    df["대손충당금비율"] = df["대손충당금_KRW"] / df["채권잔액_KRW"]
    df["연령구간"] = pd.Categorical(df["연령구간"], categories=bucket_order, ordered=True)
    return df.sort_values("연령구간").reset_index(drop=True)


def double_exposure_bonds():
    """소구 팩토링 실행 + 대손충당금 동시 설정된 채권(이중 익스포저 후보)."""
    raw = load_raw()
    factoring, allowance = raw["factoring"], raw["allowance"]
    recourse_bonds = set(factoring.loc[factoring["상환유형"] == "소구", "채권ID"])
    allowance_bonds = set(allowance["채권ID"])
    return recourse_bonds & allowance_bonds
