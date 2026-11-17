import argparse
from pathlib import Path
from scripts.dry_run_benchmark import plan
ROOT=Path(__file__).resolve().parents[2]
def args(stage):
    return argparse.Namespace(stage=stage,instances=ROOT/"benchmark/hb/instances.csv",data_dir=ROOT/"benchmark/hb/raw",
        time_limit=None,memory_limit_gib=12.0,abp_encoding=None,amo_encoding=None,output=None)
def test_plan_counts_and_labels_are_plan_only():
    for stage,count in {"pilot-rq1":30,"pilot-exact":40,"pilot-large":21,"official":120}.items():
        rows=plan(args(stage))
        assert len(rows)==count
        assert len({r["run_id_plan"] for r in rows})==count
        assert all(r["execution_status"]=="PLAN_ONLY_NOT_EXECUTED" for r in rows)
def test_rq2_requires_canonical_config():
    try: plan(args("pilot-rq2"))
    except ValueError as exc: assert "canonical config" in str(exc)
    else: raise AssertionError("must not invent the canonical SAT config")
def test_zero_time_limit_is_rejected():
    a=args("pilot-rq1");a.time_limit=0
    try: plan(a)
    except ValueError as exc: assert "positive" in str(exc)
    else: raise AssertionError("time limit 0 must not silently select a default")


def test_official_plan_uses_frozen_sat_config_and_resource_cap():
    rows = plan(args("official"))
    sat_rows = [row for row in rows if row["method"] == "sat"]
    assert len(sat_rows) == 24
    assert all(row["abp_encoding"] == "order" for row in sat_rows)
    assert all(row["amo_encoding"] == "pairwise" for row in sat_rows)
    assert all(row["solver"] == "glucose4" for row in sat_rows)
    assert all(row["memory_limit_gib"] == 12.0 for row in rows)


def test_rq1_and_rq2_keep_their_distinct_solver_choices():
    rq1 = plan(args("pilot-rq1"))
    assert all(row["solver"] == "cadical" for row in rq1)
    rq2_args = args("pilot-rq2")
    rq2_args.abp_encoding = "order"
    rq2_args.amo_encoding = "pairwise"
    rq2 = plan(rq2_args)
    assert all(row["solver"] == "glucose4" for row in rq2)
