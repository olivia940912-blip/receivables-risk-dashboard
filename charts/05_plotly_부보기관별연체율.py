"""차트⑤ — 부보기관별 91일이상 연체비중(연체율). 표본 10건 미만은 참고용으로 캡션 처리."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import plotly.express as px
import data_prep as dp
import theme

MIN_SAMPLE = 10


def build_fig():
    m = dp.customer_metrics()
    overall = dp.overall_over90_ratio(m) * 100

    g = (
        m.groupby("부보기관")
        .apply(
            lambda x: pd.Series(
                {
                    "고객수": len(x),
                    "연체율": x["연체91일이상잔액_KRW"].sum() / x["총잔액_KRW"].sum() * 100,
                }
            )
        )
        .reset_index()
        .sort_values("연체율", ascending=False)
    )
    g["표본부족"] = g["고객수"] < MIN_SAMPLE
    g["라벨"] = g.apply(
        lambda r: f"{r['연체율']:.1f}%" + ("*" if r["표본부족"] else ""), axis=1
    )

    fig = px.bar(
        g,
        x="부보기관",
        y="연체율",
        text="라벨",
        color=g["부보기관"] == "미부보",
        color_discrete_map={True: theme.DANGER, False: theme.ACCENT},
    )
    fig.update_traces(textposition="outside")
    fig.add_hline(y=overall, line_dash="dot", line_color=theme.INK, annotation_text=f"전체 평균 {overall:.1f}%")
    fig.update_layout(
        title="부보기관별 91일 이상 연체비중 (* = 표본 10건 미만, 참고용)",
        xaxis_title=None,
        yaxis_title="91일 이상 연체비중 (%)",
        showlegend=False,
    )
    return theme.apply_theme(fig)


if __name__ == "__main__":
    build_fig().show()
