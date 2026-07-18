"""차트 공통 테마 — 모노스페이스, 크림 캔버스, 잉크 텍스트, 헤어라인, 무채색 우선(강조만 빨강).
6개 차트가 전부 이 모듈의 색·폰트 토큰과 apply_theme()를 써서 화면 전체가 하나의 톤으로 보이게 한다.
"""

INK = "#201d1d"       # 기본 텍스트·기본 막대(강조 없는 계열)
CHARCOAL = "#302c2c"
MUTE = "#646262"      # 보조 계열, 기준선
ASH = "#9a9898"       # 비강조 계열(예: "그 외" 산점도 점)
CANVAS = "#fdfcfc"    # 배경
HAIRLINE = "#d8d5d5"  # 그리드/축선
DANGER = "#ff3b30"    # 위험 강조(미부보·91일이상·무보증초과 등 관리 대상)

FONT_FAMILY = (
    "IBM Plex Mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "
    "'Liberation Mono', 'Courier New', monospace"
)


def apply_theme(fig):
    fig.update_layout(
        paper_bgcolor=CANVAS,
        plot_bgcolor=CANVAS,
        font=dict(family=FONT_FAMILY, color=INK, size=13),
        title_font=dict(family=FONT_FAMILY, color=INK, size=15),
        legend=dict(bgcolor=CANVAS, bordercolor=HAIRLINE, borderwidth=1, font=dict(family=FONT_FAMILY)),
        margin=dict(t=56, b=40, l=56, r=24),
    )
    fig.update_xaxes(showline=True, linecolor=HAIRLINE, linewidth=1, gridcolor=HAIRLINE, zeroline=False)
    fig.update_yaxes(showline=True, linecolor=HAIRLINE, linewidth=1, gridcolor=HAIRLINE, zeroline=False)
    return fig
