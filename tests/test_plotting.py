import pytest

plt = pytest.importorskip("matplotlib.pyplot")

from saltshaker.plotting import plot_visibility


def test_plot_visibility_runs(sirius):
    import matplotlib
    matplotlib.use("Agg")
    ax = plot_visibility(sirius, "2026-01-15")
    assert ax.get_ylabel().startswith("Track length")
    plt.close("all")
