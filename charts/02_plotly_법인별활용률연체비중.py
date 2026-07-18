"""차트② — 법인별 여신한도 활용률(막대) × 91일이상 연체비중(선), 결합차트(dual-axis)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import data_prep as dp
import theme


def build_fig():
    corp = dp.corp_metrics()
    g = corp.assign(활용률=corp["활용률"] * 100, 연체91비중=corp["91일이상비중"] * 100).sort_values(
        "활용률", ascending=False
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=g["법인명"],
            y=g["활용률"],
            name="여신한도 활용률(%)",
            marker_color=theme.INK,
            hovertemplate="%{x}<br>활용률: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=g["법인명"],
            y=g["연체91비중"],
            name="91일이상 연체비중(%)",
            mode="lines+markers",
            line=dict(color=theme.DANGER, width=3),
            hovertemplate="%{x}<br>91일이상비중: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_hline(y=100, line_dash="dot", line_color=theme.MUTE, secondary_y=False, annotation_text="활용률 100%")
    fig.update_layout(title="법인별 여신한도 활용률 × 91일 이상 연체비중")
    fig.update_yaxes(title_text="여신한도 활용률 (%)", secondary_y=False)
    fig.update_yaxes(title_text="91일 이상 연체비중 (%)", secondary_y=True, showgrid=False)
    return theme.apply_theme(fig)


if __name__ == "__main__":
    build_fig().show()
