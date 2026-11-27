import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(repo))

from src.sat import order, pairwise
from src.sat.loader import read_instance
from src.common.verify import verify


def formula(name, k, encoding):
    graph = read_instance(repo / "benchmark/hb/raw" / (name + ".mtx.rnd"))
    encoder = order if encoding == "order" else pairwise
    return graph, encoder, encoder.build_cnf(graph, k)


def worker(name, k, encoding):
    from pysat.solvers import Solver
    g, enc, cnf = formula(name, k, encoding)
    with Solver(name="cadical195", bootstrap_with=cnf.clauses) as sat:
        start = time.perf_counter()
        ok = sat.solve()
        elapsed = time.perf_counter() - start
        stats = sat.accum_stats()
        if ok and verify(g, enc.decode_model(cnf, sat.get_model())) < k:
            raise ValueError("Invalid SAT witness")
        print(json.dumps(dict(status="SAT" if ok else "UNSAT", solve_s=elapsed, **stats)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["list", "scan", "worker"])
    p.add_argument("instance", nargs="?")
    p.add_argument("--seconds", type=int, default=120)
    p.add_argument("--k", type=int)
    p.add_argument("--encoding", choices=["order", "pairwise"], default="order")
    a = p.parse_args()
    if a.mode == "worker":
        return worker(a.instance, a.k, a.encoding)
    rows = {}
    refs = repo / "results/threshold_scan/opt_references.json"
    for j in json.loads(refs.read_text(encoding="utf-8")):
        if j["status"] == "OPT" and j["lb"] == j["ub"]:
            rows[j["instance"]] = j
    if a.mode == "list":
        for name, j in sorted(rows.items()):
            print(name, j["lb"])
        return
    if a.instance not in rows or a.seconds <= 0:
        p.error("Choose an OPT instance from list and a positive time limit.")
    name = a.instance
    j = rows[name]
    b = j["lb"]
    graph = read_instance(repo / "benchmark/hb/raw" / (name + ".mtx.rnd"))
    if verify(graph, {int(v): x for v, x in j["solution"].items()}) != b:
        raise ValueError("Invalid source witness")
    output_dir = repo / "results" / "threshold_scan" / "reruns"
    output_dir.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix="abp-" + a.mode + "-" + name + "-", dir=output_dir))
    print(out, flush=True)
    if a.mode == "scan":
        for k in range(max(1,b-2), min(graph.n,b+2)+1):
            for enc in ("pairwise", "order"):
                cmd = [sys.executable,"-B",__file__,"worker",name,"--k",str(k),"--encoding",enc]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=a.seconds)
                    data = json.loads(r.stdout) if not r.returncode else dict(status="ERR", error=r.stderr)
                except subprocess.TimeoutExpired:
                    data = dict(status="TO")
                data.update(instance=name, optimum=b, k=k, encoding=enc, solver="cadical195", limit_s=a.seconds)
                (out / f"{enc}-{k}.json").write_text(json.dumps(data), encoding="utf-8")
                print(k, enc, data["status"], flush=True)
                if data["status"] in ("SAT","UNSAT") and (data["status"]=="SAT") != (k<=b):
                    raise ValueError("Threshold result contradicts reference optimum")


if __name__ == "__main__":
    main()
