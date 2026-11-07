from src.exact.common import remaining_time_budget


def test_unlimited_time_budget_stays_unlimited():
    assert remaining_time_budget(None, 123.0) is None


def test_remaining_budget_deducts_build_time():
    assert remaining_time_budget(1800.0, 125.0) == 1675.0


def test_elapsed_time_cannot_make_remaining_budget_negative():
    assert remaining_time_budget(600.0, 900.0) == 0.0


def test_negative_elapsed_is_treated_as_zero():
    assert remaining_time_budget(10.0, -5.0) == 10.0
