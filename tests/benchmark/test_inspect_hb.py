import csv
from pathlib import Path
from scripts.inspect_hb import inspect_instances

def make_inventory(p, n=4, m=3):
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["id","name","file","size_group","n","m_table","ab_lb_ref","ab_ub_ref","pilot_role"]); w.writeheader()
        w.writerow({"id":"path4","name":"path4","file":"path4.mtx.rnd","size_group":"small","n":n,"m_table":m,"ab_lb_ref":2,"ab_ub_ref":2,"pilot_role":"test"})

def test_valid_file_computes_delta_and_ub(tmp_path):
    inv=tmp_path/"instances.csv"; data=tmp_path/"raw"; data.mkdir(); make_inventory(inv)
    (data/"path4.mtx.rnd").write_text("4 4 3\n1 2\n2 3\n3 4\n",encoding="utf-8")
    rows,passed=inspect_instances(inv,data,tmp_path/"MANIFEST.csv")
    assert passed is True; row=rows[0]
    assert row["status"]=="VALID"; assert row["n_rows"]==4; assert row["m_clean"]==3
    assert row["delta_max"]==2; assert row["ub_n_minus_delta"]==2; assert len(row["sha256"])==64

def test_duplicate_reverse_edge_and_loop_are_reported(tmp_path):
    inv=tmp_path/"instances.csv"; data=tmp_path/"raw"; data.mkdir(); make_inventory(inv,m=5)
    (data/"path4.mtx.rnd").write_text("4 4 5\n1 2\n2 1\n2 2\n2 3\n3 4\n",encoding="utf-8")
    rows,passed=inspect_instances(inv,data,tmp_path/"MANIFEST.csv")
    row=rows[0]; assert passed is True; assert row["status"]=="VALID_WITH_CLEANING"
    assert row["self_loops_removed"]==1; assert row["duplicate_edges_removed"]==1; assert row["m_clean"]==3

def test_missing_file_metrics_remain_blank(tmp_path):
    inv=tmp_path/"instances.csv"; data=tmp_path/"raw"; data.mkdir(); make_inventory(inv)
    rows,passed=inspect_instances(inv,data,tmp_path/"MANIFEST.csv")
    assert passed is False; assert rows[0]["status"]=="MISSING"
    assert rows[0]["n_header"]=="" and rows[0]["delta_max"]=="" and rows[0]["ub_n_minus_delta"]==""

def test_reference_mismatch_fails(tmp_path):
    inv=tmp_path/"instances.csv"; data=tmp_path/"raw"; data.mkdir(); make_inventory(inv,n=5,m=3)
    (data/"path4.mtx.rnd").write_text("4 4 3\n1 2\n2 3\n3 4\n",encoding="utf-8")
    rows,passed=inspect_instances(inv,data,tmp_path/"MANIFEST.csv")
    assert passed is False and rows[0]["status"]=="REFERENCE_MISMATCH"
