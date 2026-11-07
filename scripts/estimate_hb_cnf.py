"""Formula-only CNF counts from published n,m references; does not build a CNF."""
import argparse,csv,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def estimate_pairwise(n,m,k):
    dist=m*2*sum(n-d for d in range(1,k))
    amo=2*n*math.comb(n,2); alo=2*n
    return {"abp_encoding":"pairwise","amo_encoding":"pairwise","variables_total":n*n,"distance_clauses":dist,
            "amo_clauses":amo,"assignment_alo_clauses":alo,"clauses_total":dist+amo+alo,
            "method":"closed-form; does not allocate the CNF"}

def estimate_order(n,m,k):
    dist=m*2*sum(n-d for d in range(1,k))
    monotonic=n*(n-2); permutation=n*math.comb(n,2)
    return {"abp_encoding":"order","amo_encoding":"N/A (order replaces AMO)","variables_total":n*(n-1),
            "distance_clauses":dist,"amo_clauses":0,"assignment_monotonicity_clauses":monotonic,
            "permutation_assignment_clauses":permutation,"clauses_total":dist+monotonic+permutation,
            "method":"closed-form; does not allocate the CNF"}

def count(n,m,k):
    if not 1 <= k < n: raise ValueError("K must be in 1..n-1")
    pair=estimate_pairwise(n,m,k); pair["status"]="FORMULA_ESTIMATE_NOT_MEASURED"
    order=estimate_order(n,m,k); order["status"]="FORMULA_ESTIMATE_NOT_MEASURED"
    dist=order["distance_clauses"]
    seq={"abp_encoding":"pairwise","amo_encoding":"seqcounter","variables_total":None,"aux_variables":None,
         "distance_clauses":dist,"amo_clauses":None,"clauses_total":None,"status":"PENDING_PYSAT_ENCODER"}
    try:
        from pysat.card import CardEnc,EncType
        from pysat.formula import IDPool
        pool=IDPool(start_from=n*n+1)
        cnf=CardEnc.atmost(list(range(1,n+1)),bound=1,encoding=EncType.seqcounter,vpool=pool)
        c=len(cnf.clauses); aux=max(0,cnf.nv-n*n)
        seq.update(variables_total=n*n+2*n*aux,aux_variables=2*n*aux,one_group_amo_clauses=c,
                   amo_clauses=2*n*c,clauses_total=dist+2*n+2*n*c,status="FORMULA_ESTIMATE_NOT_MEASURED")
    except Exception as e:
        seq["note"]=f"{type(e).__name__}: PySAT seqcounter count not available in this environment"
    return [pair,seq,order]

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--instances",type=Path,default=ROOT/"benchmark/hb/instances.csv")
    p.add_argument("--name"); p.add_argument("--k",default="max"); p.add_argument("--output",type=Path); a=p.parse_args()
    with a.instances.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    result=[]
    for r in rows:
        if a.name and a.name not in (r["id"],r["name"],r["file"]): continue
        n,m=int(r["n"]),int(r["m_table"]); k=n-1 if a.k=="max" else int(a.k)
        result.append({"id":r["id"],"file":r["file"],"n_reference":n,"m_reference":m,"K_estimate":k,
                       "evidence":"PUBLISHED_REFERENCE_VALUES_NOT_LOCAL_FILE_MEASUREMENTS","encodings":count(n,m,k)})
    if a.name and not result: p.error(f"unknown instance: {a.name}")
    s=json.dumps(result,indent=2,ensure_ascii=False)
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(s+"\n",encoding="utf-8")
    else: print(s)

if __name__ == "__main__":
    main()
