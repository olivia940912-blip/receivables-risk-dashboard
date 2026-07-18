"""차트① (Plotly 버전) — 부보여부별 91일이상 연체잔액 비중 비교.
matplotlib 버전(01_matplotlib_부보연체비교.py)과 같은 계산, 같은 결론을 인터랙티브로 재현한다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import plotly.express as px
import data_prep as dp
import theme


def build_fig():
    m = dp.customer_metrics()
    overall = dp.overall_over90_ratio(m) * 100
    g = m.groupby("부보여부").apply(
        lambda x: x["연체91일이상잔액_KRW"].sum() / x["총잔액_KRW"].sum() * 100
    )
    no_cover = g.get("미부보", 0.0)

    plot_df = pd.DataFrame(
        {"구분": ["전체 고객", "미부보 고객"], "91일이상비중": [overall, no_cover]}
    )
    fig = px.bar(
        plot_df,
        x="구분",
        y="91일이상비중",
        color="구분",
        color_discrete_map={"전체 고객": theme.MUTE, "미부보 고객": theme.DANGER},
        text=plot_df["91일이상비중"].map(lambda v: f"{v:.1f}%"),
    )
    fig.update_traces(textposition="outside", hovertemplate="%{x}<br>91일이상비중: %{y:.1f}%<extra></extra>")
    fig.update_layout(
        title="부보여부별 91일 이상 연체잔액 비중",
        yaxis_title="91일 이상 연체잔액 비중 (%)",
        xaxis_title=None,
        showlegend=False,
    )
    return theme.apply_theme(fig)


if __name__ == "__main__":
    build_fig().show()
