from typing import Optional


import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "perf(): Performance tests.")


class Perfs():

    _data: dict[str, list[float]]

    def __init__(self):
        self._data = {}

    def collect(self, route: str, time: float):
        if route not in self._data:
            self._data[route] = []

        self._data[route].append(time)

    def plot(self, file: Optional[str] = None):
        ...
        # import matplotlib.pyplot as plt
        # import numpy as np

        # fig = plt.figure()

        # ax = fig.gca()
        # ax.set_title("Response Time\n(median, 0.01/0.05-quantiles, distribution)")
        # ax.set_ylabel("ms")
        # ax.set_yscale("log")

        # labels = list(self._data.keys())
        # values = list(self._data.values())

        # if not values:
        #     return

        # ax.set_xticks(np.arange(1, len(labels) + 1), labels=labels, rotation=90)
        # ax.set_xlim(0.25, len(labels) + 0.75)
        # ax.set_xlabel("Route")

        # ax.violinplot(values, showmedians=True, quantiles=[[0.01, 0.05, 0.95, 0.99] for _ in labels])

        # if not file:
        #     plt.show()
        # else:
        #     plt.savefig(file, bbox_inches="tight")


_perfs = Perfs()


@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    if exitstatus == 0:
        _perfs.plot("doc/perf.png")


@pytest.fixture
def perfs(request: pytest.FixtureRequest) -> Perfs:
    return _perfs
