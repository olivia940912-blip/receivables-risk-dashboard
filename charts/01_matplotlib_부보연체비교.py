"""차트① (matplotlib 버전) — 부보여부별 91일이상 연체잔액 비중 비교."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
import data_prep as dp

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "01_matplotlib_부보연체비교.png"


def build_fig():
    m = dp.customer_metrics()
    overall = dp.overall_over90_ratio(m) * 100
    g = m.groupby("부보여부").apply(
        lambda x: x["연체91일이상잔액_KRW"].sum() / x["총잔액_KRW"].sum() * 100
    )
    no_cover = g.get("미부보", 0.0)

    labels = ["전체 고객", "미부보 고객"]
    values = [overall, no_cover]
    colors = ["#8c9aab", "#d64545"]

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(labels, values, color=colors, width=0.5)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.5, f"{v:.1f}%", ha="center", fontsize=12, fontweight="bold")
    ax.set_ylabel("91일 이상 연체잔액 비중 (%)")
    ax.set_title("부보여부별 91일 이상 연체잔액 비중")
    ax.set_ylim(0, max(values) * 1.3)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    fig = build_fig()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150)
    print(f"저장 완료: {OUTPUT_PATH}")
