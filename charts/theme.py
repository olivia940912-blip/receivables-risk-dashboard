"""차트 공통 테마 — 시스템 UI 폰트(가독성 우선) + 부드러운 화이트 카드 + 파랑/빨강 상태색.
6개 차트가 전부 이 모듈의 색·폰트 토큰과 apply_theme()를 써서 화면 전체가 하나의 톤으로 보이게 한다.
색상은 dataviz 스킬의 검증된 참조 팔레트(references/palette.md) 값을 그대로 사용한다.
"""

INK = "#0b0b0b"        # 기본 텍스트
MUTE = "#52514e"       # 보조 텍스트
ASH = "#898781"        # 축·비강조 계열
CANVAS = "#fcfcfb"     # 차트(카드) 배경
HAIRLINE = "#e1e0d9"   # 그리드/축선
ACCENT = "#2a78d6"      # 중립/정보성 계열(카테고리컬 slot 1)
DANGER = "#d03b3b"      # 위험 강조(상태색 critical) — 미부보·91일이상·무보증초과 등 관리 대상 전용

# 시스템 기본 UI 폰트를 그대로 쓴다 — 삼성 기기에서는 삼성 자체 시스템 폰트, 그 외에는
# 각 OS 기본 폰트(Windows: 맑은 고딕/Segoe UI, mac: Apple SD 산돌고딕)로 렌더링되어
# 특정 서체 라이선스 없이도 각 사용자 환경에서 가장 자연스럽고 가독성 높은 글꼴로 보인다.
FONT_FAMILY = (
    "system-ui, -apple-system, 'Segoe UI', 'Malgun Gothic', Roboto, "
    "'Helvetica Neue', Arial, sans-serif"
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
