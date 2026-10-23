"""Unit tests for shared exact-solver validation and configuration warnings."""
import warnings
import pytest

from src.common.models import Config, Instance
from src.exact.common import validate_exact_input, warn_ignored_config
from src.exact.gurobi_mip import solve_gurobi_mip
from src.exact.cplex_mip import solve_cplex_mip
from src.exact.cplex_cp import solve_cplex_cp

EXACT_SOLVERS = [
    ("gurobi_mip", solve_gurobi_mip),
    ("cplex_mip", solve_cplex_mip),
    ("cplex_cp", solve_cplex_cp),
]


def instance(n=3, edges=((0, 1),)):
    return Instance("test", "test", n, tuple(edges), "test", "toy")


@pytest.mark.parametrize(
    "inst",
    [
        instance(n=1),
        instance(edges=()),
        instance(edges=((0, 0),)),
        instance(edges=((0, 3),)),
        instance(edges=((0, True),)),
    ],
)
def test_invalid_instance_raises_value_error(inst):
    with pytest.raises(ValueError):
        validate_exact_input(inst, Config(method="gurobi_mip"))


@pytest.mark.parametrize("limit", [0, -1, float("inf"), float("nan")])
def test_invalid_time_limit_raises_value_error(limit):
    with pytest.raises(ValueError, match="time_limit"):
        validate_exact_input(
            instance(), Config(method="gurobi_mip", time_limit=limit)
        )


def test_default_config_does_not_warn():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        warn_ignored_config(Config(method="gurobi_mip"), supported=("seed",))
    assert not record


def test_ignored_non_default_config_warns():
    with pytest.warns(UserWarning, match="memory_limit"):
        warn_ignored_config(
            Config(method="gurobi_mip", memory_limit=512),
            supported=("seed",),
        )


def test_seed_is_reported_as_ignored_when_backend_does_not_support_it():
    with pytest.warns(UserWarning, match="seed"):
        warn_ignored_config(
            Config(method="cplex_cp", seed=2),
            supported=(),
        )


@pytest.mark.parametrize("method,solve", EXACT_SOLVERS, ids=[item[0] for item in EXACT_SOLVERS])
@pytest.mark.parametrize(
    "inst",
    [instance(n=1), instance(edges=()), instance(edges=((0, 0),)), instance(edges=((0, 3),))],
)
def test_exact_solver_adapters_raise_for_invalid_instances(method, solve, inst):
    with pytest.raises(ValueError):
        solve(inst, Config(method=method))


@pytest.mark.parametrize("method,solve", EXACT_SOLVERS, ids=[item[0] for item in EXACT_SOLVERS])
@pytest.mark.parametrize("limit", [0, -1, float("inf"), float("nan")])
def test_exact_solver_adapters_raise_for_invalid_time_limits(method, solve, limit):
    with pytest.raises(ValueError, match="time_limit"):
        solve(instance(), Config(method=method, time_limit=limit))
