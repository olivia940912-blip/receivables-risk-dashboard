"""차트② — 법인별 여신한도 활용률 × 91일이상 연체비중, 단일 축 그룹 막대.

원래 이중축(secondary_y) 결합차트였으나, 두 지표 모두 이미 %(0~100대) 스케일이라
축을 임의로 늘리거나 줄일 필요가 없다. 이중축은 두 축의 정렬 기준이 임의적이라
실제로는 없는 상관관계를 있어 보이게 만들 수 있어(anti-pattern) 단일 축 그룹
막대로 바꿨다 — 두 막대를 같은 %축에서 직접 비교할 수 있다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import plotly.express as px
import data_prep as dp
import theme


def build_fig():
    corp = dp.corp_metrics()
    g = corp.assign(활용률=corp["활용률"] * 100, 연체91비중=corp["91일이상비중"] * 100).sort_values(
        "활용률", ascending=False
    )
    long_df = g.melt(
        id_vars="법인명",
        value_vars=["활용률", "연체91비중"],
        var_name="지표",
        value_name="값",
    )
    long_df["지표"] = long_df["지표"].map({"활용률": "여신한도 활용률(%)", "연체91비중": "91일이상 연체비중(%)"})

    fig = px.bar(
        long_df,
        x="법인명",
        y="값",
        color="지표",
        barmode="group",
        color_discrete_map={"여신한도 활용률(%)": theme.ACCENT, "91일이상 연체비중(%)": theme.DANGER},
        text=long_df["값"].map(lambda v: f"{v:.1f}%"),
        category_orders={"법인명": list(g["법인명"])},
    )
    fig.update_traces(textposition="outside")
    fig.add_hline(y=100, line_dash="dot", line_color=theme.MUTE, annotation_text="활용률 100%")
    fig.update_layout(
        title="법인별 여신한도 활용률 × 91일 이상 연체비중 (같은 %축)",
        xaxis_title=None,
        yaxis_title="%",
        legend_title=None,
    )
    return theme.apply_theme(fig)


if __name__ == "__main__":
    build_fig().show()
