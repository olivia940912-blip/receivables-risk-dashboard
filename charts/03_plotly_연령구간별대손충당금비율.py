"""차트③ — 연령구간별 대손충당금비율(집합), 전체 평균 기준선 포함."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotly.express as px
import data_prep as dp
import theme


def build_fig():
    df = dp.bond_allowance_by_bucket()
    df["대손충당금비율_pct"] = df["대손충당금비율"] * 100
    overall = df["대손충당금_KRW"].sum() / df["채권잔액_KRW"].sum() * 100

    colors = [theme.ACCENT] * len(df)
    over90_idx = df.index[df["연령구간"] == dp.OVER90_BUCKET]
    for i in over90_idx:
        colors[i] = theme.DANGER

    fig = px.bar(
        df,
        x="연령구간",
        y="대손충당금비율_pct",
        text=df["대손충당금비율_pct"].map(lambda v: f"{v:.1f}%"),
    )
    fig.update_traces(marker_color=colors, textposition="outside")
    fig.add_hline(
        y=overall,
        line_dash="dot",
        line_color=theme.INK,
        annotation_text=f"전체 평균 {overall:.1f}%",
        annotation_position="top left",
    )
    fig.update_layout(
        title="연령구간별 대손충당금비율 (91일 이상 강조)",
        xaxis_title="연령구간",
        yaxis_title="대손충당금비율 (%)",
    )
    return theme.apply_theme(fig)


if __name__ == "__main__":
    build_fig().show()
