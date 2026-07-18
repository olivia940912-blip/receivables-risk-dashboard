"""차트⑥ — DSO × 여신한도 활용률 산점도, color=무보증초과 여부.
DSO는 매출 급감 고객에서 극단값이 나올 수 있어 x축을 로그 스케일로 표시한다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotly.express as px
import data_prep as dp
import theme


def build_fig():
    m = dp.customer_metrics().dropna(subset=["DSO", "활용률"]).copy()
    m["구분"] = m["무보증초과"].map({True: "무보증초과", False: "그 외"})
    m["활용률_pct"] = m["활용률"] * 100

    fig = px.scatter(
        m,
        x="DSO",
        y="활용률_pct",
        color="구분",
        color_discrete_map={"무보증초과": theme.DANGER, "그 외": theme.ASH},
        log_x=True,
        hover_data={"고객ID": True, "법인명": True, "DSO": ":.0f", "활용률_pct": ":.1f", "구분": False},
    )
    fig.add_hline(y=100, line_dash="dot", line_color=theme.MUTE, annotation_text="활용률 100%")
    fig.update_layout(
        title="DSO × 여신한도 활용률 (무보증초과 강조, x축 로그 스케일)",
        xaxis_title="DSO (일, 로그축)",
        yaxis_title="여신한도 활용률 (%)",
    )
    return theme.apply_theme(fig)


if __name__ == "__main__":
    build_fig().show()
