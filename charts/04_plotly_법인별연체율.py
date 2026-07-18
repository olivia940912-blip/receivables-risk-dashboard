"""차트④ — 법인별 91일이상 연체비중(연체율)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import plotly.express as px
import data_prep as dp


def build_fig():
    m = dp.customer_metrics()
    overall = dp.overall_over90_ratio(m) * 100

    g = (
        m.groupby("법인명")
        .apply(lambda x: x["연체91일이상잔액_KRW"].sum() / x["총잔액_KRW"].sum() * 100)
        .reset_index(name="연체율")
        .sort_values("연체율", ascending=False)
    )

    fig = px.bar(
        g,
        x="법인명",
        y="연체율",
        text=g["연체율"].map(lambda v: f"{v:.1f}%"),
        color=g["연체율"] > overall,
        color_discrete_map={True: "#d64545", False: "#8c9aab"},
    )
    fig.update_traces(textposition="outside")
    fig.add_hline(y=overall, line_dash="dot", line_color="#333", annotation_text=f"전체 평균 {overall:.1f}%")
    fig.update_layout(
        title="법인별 91일 이상 연체비중",
        xaxis_title=None,
        yaxis_title="91일 이상 연체비중 (%)",
        showlegend=False,
    )
    return fig


if __name__ == "__main__":
    build_fig().show()
