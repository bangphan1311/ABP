
import pytest

from src.common.models import Instance
from src.common.verify import verify


def make_path_instance() -> Instance:
    """Đường đi có 4 đỉnh: 0--1--2--3."""
    return Instance(
        id="path4",
        name="Path graph with 4 vertices",
        n=4,
        edges=((0, 1), (1, 2), (2, 3)),
        source="test",
        tier="small",
    )


def test_verify_path_graph():
    instance = make_path_instance()
    labeling = {0: 1, 1: 3, 2: 2, 3: 4}

    assert verify(instance, labeling) == 1


def test_verify_cycle_graph():
    """Chu trình 5 đỉnh với labeling có antibandwidth bằng 2."""
    instance = Instance(
        id="cycle5",
        name="Cycle graph with 5 vertices",
        n=5,
        edges=((0, 1), (1, 2), (2, 3), (3, 4), (4, 0)),
        source="test",
        tier="small",
    )
    labeling = {0: 1, 1: 3, 2: 5, 3: 2, 4: 4}

    assert verify(instance, labeling) == 2


def test_verify_missing_vertex():
    instance = make_path_instance()
    labeling = {0: 1, 1: 2, 2: 3}

    with pytest.raises(ValueError):
        verify(instance, labeling)


def test_verify_duplicate_labels():
    instance = make_path_instance()
    labeling = {0: 1, 1: 2, 2: 2, 3: 4}

    with pytest.raises(ValueError):
        verify(instance, labeling)


def test_verify_invalid_label_range():
    instance = make_path_instance()
    labeling = {0: 0, 1: 2, 2: 3, 3: 4}

    with pytest.raises(ValueError):
        verify(instance, labeling)
