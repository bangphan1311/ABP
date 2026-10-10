
import pytest

from src.common.models import Instance
from src.common.verify import verify
from src.exact.oracle import solve_oracle


def test_oracle_on_path4():
    instance = Instance(
        id="path4",
        name="Path graph with 4 vertices",
        n=4,
        edges=((0, 1), (1, 2), (2, 3)),
        source="test",
        tier="small",
    )

    result = solve_oracle(instance)

    assert result.status == "OPT"
    assert result.lb == 2
    assert result.ub == 2
    assert result.gap == 0.0
    assert verify(instance, result.solution) == result.lb
    assert result.metadata["labelings_checked"] == 24


def test_oracle_on_cycle5():
    instance = Instance(
        id="cycle5",
        name="Cycle graph with 5 vertices",
        n=5,
        edges=((0, 1), (1, 2), (2, 3), (3, 4), (4, 0)),
        source="test",
        tier="small",
    )

    result = solve_oracle(instance)

    assert result.status == "OPT"
    assert result.lb == 2
    assert result.ub == 2
    assert verify(instance, result.solution) == 2
    assert result.metadata["labelings_checked"] == 120


def test_oracle_rejects_graph_too_large():
    instance = Instance(
        id="path10",
        name="Path graph with 10 vertices",
        n=10,
        edges=tuple((i, i + 1) for i in range(9)),
        source="test",
        tier="small",
    )

    with pytest.raises(ValueError, match="tối đa"):
        solve_oracle(instance)