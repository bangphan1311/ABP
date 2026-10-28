"""Plan-only run-matrix checker for ABP W3; this script never launches a solver."""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/"benchmark/hb/instances.csv"
RAW=ROOT/"benchmark/hb/raw"
VALIDATION=["pores_1","bcsstk01","bcspwr02","curtis54","will57","impcol_b","ash85","nos4","dwt_234","bcspwr03"]
PILOT_LARGE=["bcsstk06","nos6","can_715"]
EXACT_METHODS=["cp_sat","gurobi_mip","cplex_mip","cplex_cp"]
RQ1_CONFIGS=[("pairwise","pairwise"),("pairwise","seqcounter"),("order","pairwise")]
FIELDS=["stage","run_id_plan","instance_id","filename","source_file_present","method","abp_encoding","amo_encoding","solver","time_limit_s","memory_limit_gib","execution_status","notes"]

def load_inventory(path):
    with path.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    required={"id","name","file","n","m_table"}
    if not rows or not required.issubset(rows[0]): raise ValueError(f"inventory needs {sorted(required)}")
    if len(rows)!=24 or len({r["id"] for r in rows})!=24: raise ValueError("inventory must have 24 unique instances")
    by_id={r["id"]:r for r in rows}
    for item in VALIDATION+PILOT_LARGE:
        if item not in by_id: raise ValueError(f"required protocol instance missing: {item}")
    return rows,by_id

def plan(args):
    if args.time_limit is not None and args.time_limit<=0: raise ValueError("time-limit must be positive")
    if args.memory_limit_gib is not None and args.memory_limit_gib<=0: raise ValueError("memory-limit-gib must be positive")
    rows,by_id=load_inventory(args.instances); out=[]
    def add(stage,inst,method,abp,amo,solver,limit,notes=""):
        r=by_id[inst]; present=(args.data_dir/r["file"]).is_file()
        rid="|".join([stage,inst,method,abp or "PENDING",amo or "PENDING",solver or "PENDING",str(limit)])
        out.append({"stage":stage,"run_id_plan":rid,"instance_id":inst,"filename":r["file"],
            "source_file_present":str(present).lower(),"method":method,"abp_encoding":abp or "PENDING_CANONICAL_CONFIG",
            "amo_encoding":amo or "PENDING_CANONICAL_CONFIG","solver":solver or "PENDING","time_limit_s":limit,
            "memory_limit_gib":args.memory_limit_gib if args.memory_limit_gib is not None else "PENDING",
            "execution_status":"PLAN_ONLY_NOT_EXECUTED","notes":notes})
    stage=args.stage
    if stage=="pilot-rq1":
        for inst in VALIDATION:
            for abp,amo in RQ1_CONFIGS: add(stage,inst,"sat",abp,amo,"cadical",args.time_limit if args.time_limit is not None else 1800)
    elif stage=="pilot-rq2":
        if not args.abp_encoding or not args.amo_encoding: raise ValueError("pilot-rq2 needs canonical config via --abp-encoding and --amo-encoding")
        for inst in VALIDATION: add(stage,inst,"sat",args.abp_encoding,args.amo_encoding,"glucose4",args.time_limit if args.time_limit is not None else 1800,"Kissat excluded until a native binary passes correctness tests")
    elif stage=="pilot-exact":
        for inst in VALIDATION:
            for method in EXACT_METHODS: add(stage,inst,method,None,None,None,args.time_limit if args.time_limit is not None else 600)
    elif stage=="pilot-large":
        for inst in PILOT_LARGE:
            for abp,amo in RQ1_CONFIGS: add(stage,inst,"sat",abp,amo,"cadical",args.time_limit if args.time_limit is not None else 1800,"Only run after hard memory limit is tested on target OS")
            for method in EXACT_METHODS: add(stage,inst,method,None,None,None,args.time_limit if args.time_limit is not None else 1800,"Only run after hard memory limit and license checks")
    elif stage=="official":
        for r in rows:
            add(stage,r["id"],"sat",args.abp_encoding,args.amo_encoding,"cadical",args.time_limit if args.time_limit is not None else 1800,"Canonical SAT config must be selected before official run")
            for method in EXACT_METHODS: add(stage,r["id"],method,None,None,None,args.time_limit if args.time_limit is not None else 1800,"License/size limit must be verified before official run")
    ids=[r["run_id_plan"] for r in out]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate planned run IDs")
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage",choices=["pilot-rq1","pilot-rq2","pilot-exact","pilot-large","official"],required=True)
    p.add_argument("--instances",type=Path,default=INV);p.add_argument("--data-dir",type=Path,default=RAW)
    p.add_argument("--time-limit",type=int);p.add_argument("--memory-limit-gib",type=float,help="metadata only; no memory enforcement")
    p.add_argument("--abp-encoding",choices=["pairwise","order"]);p.add_argument("--amo-encoding",choices=["pairwise","seqcounter"])
    p.add_argument("--output",type=Path);a=p.parse_args()
    try: rows=plan(a)
    except (OSError,ValueError) as e: print(f"ERROR: {e}",file=sys.stderr);return 2
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open("w",encoding="utf-8-sig",newline="") as f: w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    else:
        w=csv.DictWriter(sys.stdout,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    print(f"# plan-only; stage={a.stage}; runs={len(rows)}; raw files present={sum(x['source_file_present']=='true' for x in rows)}/{len(rows)}; no solver launched",file=sys.stderr)
    return 0
if __name__=="__main__": raise SystemExit(main())
