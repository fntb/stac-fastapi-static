from typing import Optional

import os
import csv
import warnings

import pytest


class Benchmark():

    _data: dict[str, list[float]]

    def __init__(self):
        self._data = {}

    def collect(self, route: str, time: float):
        if route not in self._data:
            self._data[route] = []

        self._data[route].append(time)

    def summarize(self, dir: Optional[str] = "doc"):
        dir = os.path.abspath(dir)

        os.makedirs(dir, exist_ok=True)

        headers = self._data.keys()
        n = max(*(len(self._data[header]) for header in headers))

        with open(os.path.join(dir, "benchmark.csv"), "w", newline="") as f:
            spamwriter = csv.writer(f)
            spamwriter.writerow(headers)
            for i in range(n):
                spamwriter.writerow([
                    self._data[header][i] if i < len(self._data[header]) else None
                    for header
                    in headers
                ])

        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ModuleNotFoundError:
            warnings.warn("Cannot plot benchmark results - missing dependencies matplotlib and numpy")
            return

        labels = list(self._data.keys())
        values = list(self._data.values())

        if not values:
            return

        fig, (ax1, ax2) = plt.subplots(1, 2)

        ax1.set_title("Response Time")
        ax1.set_ylabel("ms")
        ax1.set_yscale("log")

        ax1.set_xticklabels(labels, rotation=90, fontsize=8)
        ax1.set_xlim(0.25, len(labels) + 0.75)
        ax1.set_xlabel("Route")

        ax1.boxplot(values)

        ax2.set_title("Response Time (linear scale, cropped)")
        ax2.set_ylabel("ms")
        ax2.set_ylim([0, min(
            np.quantile(np.array([value for _values in values for value in _values]), 0.90),
            250
        )])

        ax2.set_xticklabels(labels, rotation=90, fontsize=8)
        ax2.set_xlim(0.25, len(labels) + 0.75)
        ax2.set_xlabel("Route")

        ax2.boxplot(values)

        plt.tight_layout()
        plt.savefig(os.path.join(dir, "benchmark.png"), bbox_inches="tight", dpi=200)


_benchmark = Benchmark()


@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    if exitstatus == 0:
        _benchmark.summarize()


@pytest.fixture
def benchmark() -> Benchmark:
    return _benchmark
