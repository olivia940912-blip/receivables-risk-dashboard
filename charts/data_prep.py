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
    """고객 단위: 채권잔액, 91일이상 비중, 여신한도 활용률, 부보여부, DSO, 회수지연일수,
    무보증초과·부보초과잔여리스크·이중익스포저 여부."""
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
    # CLAUDE.md 기준: 활용률 100% 초과 + 부보기관이 있어도 자기부담율이 높으면(20%↑)
    # 부보로 커버되지 않는 잔여 리스크(= 채권잔액 × 자기부담율)가 남는다.
    m["부보초과잔여리스크"] = (m["활용률"] > 1.0) & (m["부보기관"] != "미부보") & (m["자기부담율"] >= 0.2)
    m["잔여리스크_KRW"] = m["총잔액_KRW"] * m["자기부담율"]

    rev3 = revenue[revenue["기준월"].isin(RECENT_MONTHS)]
    avg_rev = (
        rev3.groupby("고객ID", as_index=False)["매출액_KRW"]
        .mean()
        .rename(columns={"매출액_KRW": "최근3개월평균매출_KRW"})
    )
    m = m.merge(avg_rev, on="고객ID", how="left")
    m["DSO"] = m["총잔액_KRW"] / m["최근3개월평균매출_KRW"] * DSO_PERIOD_DAYS

    net_terms = revenue.groupby("고객ID", as_index=False)["표준지급조건_일"].first()
    m = m.merge(net_terms, on="고객ID", how="left")
    m["회수지연일수"] = m["DSO"] - m["표준지급조건_일"]

    de_customers = double_exposure_customers(ar=ar)
    m["이중익스포저"] = m["고객ID"].isin(de_customers)

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


def double_exposure_customers(ar=None):
    """이중 익스포저 채권을 1건이라도 보유한 고객(회사) 집합."""
    if ar is None:
        ar = load_raw()["ar"]
    bonds = double_exposure_bonds()
    return set(ar.loc[ar["채권ID"].isin(bonds), "고객ID"])


def priority_watchlist(top_n=10):
    """관리 우선순위 워치리스트 — 5개 위험 플래그(무보증초과·부보초과잔여리스크·
    고연체·회수지연·이중익스포저)를 합산한 점수로 회사를 정렬한다.
    통계적 스코어링 모델이 아니라 CLAUDE.md의 관리 기준을 그대로 합산한 실무용 우선순위표다.
    """
    m = customer_metrics()
    m = m.copy()
    m["고연체"] = m["연체91일이상비중"] >= 0.5
    m["회수지연"] = m["회수지연일수"] > 30

    flags = ["무보증초과", "부보초과잔여리스크", "고연체", "회수지연", "이중익스포저"]
    m["위험플래그수"] = m[flags].sum(axis=1)

    def reason(row):
        labels = {
            "무보증초과": "무보증초과",
            "부보초과잔여리스크": "부보초과잔여리스크",
            "고연체": "91일이상 과반",
            "회수지연": "회수지연 30일+",
            "이중익스포저": "이중익스포저",
        }
        return " · ".join(labels[f] for f in flags if row[f])

    m["사유"] = m.apply(reason, axis=1)
    watch = m[m["위험플래그수"] > 0].sort_values(
        ["위험플래그수", "총잔액_KRW"], ascending=[False, False]
    )
    return watch.head(top_n)[
        [
            "고객ID", "법인명", "총잔액_KRW", "활용률", "연체91일이상비중",
            "회수지연일수", "부보여부", "위험플래그수", "사유",
        ]
    ].reset_index(drop=True)


def key_insights():
    """핵심 인사이트 — 여러 차트를 가로질러 종합한 발견을 심각도순으로 반환한다.
    각 항목은 근거(수치) → 해석 → 시사점 구조이며 숫자는 매번 원본 CSV에서 재계산한다.
    """
    m = customer_metrics()
    overall = overall_over90_ratio(m)
    corp = corp_metrics()
    bucket = bond_allowance_by_bucket()

    over90_by_cover = m.groupby("부보여부").apply(
        lambda x: x["연체91일이상잔액_KRW"].sum() / x["총잔액_KRW"].sum()
    )
    no_cover_ratio = over90_by_cover.get("미부보", 0.0)
    cover_ratio = over90_by_cover.get("부보", 0.0)

    bucket_pct = bucket["대손충당금비율"] * 100
    bucket_delta = bucket_pct.diff()
    max_delta_idx = bucket_delta.idxmax()
    max_delta_bucket = bucket.loc[max_delta_idx, "연령구간"]
    max_delta_prev = bucket.loc[max_delta_idx - 1, "연령구간"]

    top_util = corp.sort_values("활용률", ascending=False).iloc[0]
    top_over90 = corp.sort_values("91일이상비중", ascending=False).iloc[0]

    delay_share = (m["회수지연일수"] > 0).mean()
    delay_mean = m["회수지연일수"].mean()

    double_flag_count = int(((m["무보증초과"]) & (m["이중익스포저"])).sum())
    no_cover_count = int((m["부보기관"] == "미부보").sum())

    insights = [
        {
            "심각도": "critical" if no_cover_ratio > overall * 1.3 else "warning",
            "제목": "무보증 고객의 장기연체 비중이 부보 고객보다 뚜렷하게 높다",
            "근거": f"미부보 고객 91일이상비중 {no_cover_ratio*100:.1f}% vs 부보 고객 {cover_ratio*100:.1f}% (전체 평균 {overall*100:.1f}%)",
            "해석": f"리스크 이전 수단이 없는 고객군에서 장기연체가 약 {no_cover_ratio/cover_ratio:.1f}배 더 많이 발생한다.",
            "시사점": f"무보증 고객 {no_cover_count}사에 대해 부보 가입(K-SURE/Euler Hermes 등) 확대를 우선 검토해야 한다.",
        },
        {
            "심각도": "critical",
            "제목": f"연체 {max_delta_prev}→{max_delta_bucket} 구간에서 대손충당금비율이 가장 크게 뛴다",
            "근거": f"구간별 증가폭: {' → '.join(f'{d:+.1f}%p' for d in bucket_delta.dropna())} (마지막 구간이 최대)",
            "해석": "91일 문턱을 넘는 순간 예상손실율이 비선형적으로 급증한다 — 61~90일 구간에서 조치하지 못하면 손실 인식이 두 배 이상 뛴다.",
            "시사점": "91일 이상 개별심사 대상뿐 아니라, 61~90일 구간 채권을 91일 진입 전에 회수/재조정하는 것이 손실 예방 효과가 가장 크다.",
        },
        {
            "심각도": "warning",
            "제목": "여신한도 활용률과 실제 연체율의 1위 법인이 서로 다르다",
            "근거": f"활용률 1위: {top_util['법인명']} ({top_util['활용률']*100:.1f}%) / 91일이상비중 1위: {top_over90['법인명']} ({top_over90['91일이상비중']*100:.1f}%)",
            "해석": "활용률이 높다고 반드시 연체율도 높은 것은 아니다 — 두 지표가 같은 위험을 가리키지 않는다.",
            "시사점": "활용률만으로 법인별 관리 우선순위를 정하면 안 되고, 91일이상비중·DSO 등과 교차확인해야 한다.",
        },
        {
            "심각도": "warning",
            "제목": "고객 대다수가 계약된 지급조건보다 늦게 갚고 있다",
            "근거": f"DSO가 표준지급조건(NET)을 초과하는 고객 비율 {delay_share*100:.1f}%, 평균 초과일수 {delay_mean:.0f}일",
            "해석": "연체구간 통계에 잡히지 않는 '정상' 채권도 실제로는 계약 조건보다 느리게 회수되고 있다.",
            "시사점": "연령구간 기준 관리에 더해, 고객별 회수지연일수(DSO-NET)를 월별로 추적할 필요가 있다.",
        },
        {
            "심각도": "critical",
            "제목": "무보증초과 + 이중익스포저가 동시에 걸리는 회사가 존재한다",
            "근거": f"두 조건을 모두 충족하는 회사 {double_flag_count}사 (전체 {len(m)}사 중 {double_flag_count/len(m)*100:.1f}%)",
            "해석": "리스크 이전 수단이 아예 없는 상태에서, 이미 받은 팩토링 자금까지 상환해야 할 수 있는 이중 위험 구조다.",
            "시사점": "이 회사들은 다른 어떤 지표보다 우선해서 개별 심사·회수 조치가 필요하다 (하단 [00] 워치리스트 참고).",
        },
    ]
    return insights
