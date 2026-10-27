"""Validate real .mtx.rnd edge lists; never fills measurements from references."""
import argparse, csv, hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "benchmark/hb/instances.csv"
DATA = ROOT / "benchmark/hb/raw"
OUT = ROOT / "benchmark/hb/MANIFEST.csv"
FIELDS = ["id","name","file","status","relative_path","sha256","n_reference","m_reference","n_header","n_cols","m_header","m_file_rows","m_clean","self_loops_removed","duplicate_edges_removed","delta_max","ub_n_minus_delta","notes"]

def read_inventory(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"id","name","file","n","m_table","size_group","ab_lb_ref","ab_ub_ref","pilot_role"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"inventory must have columns {sorted(required)}")
    if len({r["id"] for r in rows}) != len(rows) or len({r["file"] for r in rows}) != len(rows):
        raise ValueError("duplicate id or filename")
    for r in rows:
        if Path(r["file"]).name != r["file"]:
            raise ValueError(f"unsafe filename: {r['file']}")
        for k in ("n","m_table","ab_lb_ref","ab_ub_ref"):
            if not r[k].isdigit():
                raise ValueError(f"{r['id']}: {k} is not a non-negative integer")
    return rows

def inspect(path, ref, rel):
    b = path.read_bytes()
    rec = dict.fromkeys(FIELDS, "")
    rec.update(id=ref["id"],name=ref["name"],file=ref["file"],status="INVALID_FORMAT",
               relative_path=rel,sha256=hashlib.sha256(b).hexdigest(),
               n_reference=ref["n"],m_reference=ref["m_table"])
    try:
        text = b.decode("utf-8-sig")
        lines = [(i,s.strip()) for i,s in enumerate(text.splitlines(),1)
                 if s.strip() and not s.strip().startswith(("#","%"))]
        if not lines:
            raise ValueError("empty file")

        # Official Optsicom files start with a problem-name line.
        if lines[0][1].casefold().startswith("nombre del problema:"):
            lines = lines[1:]

        if not lines:
            raise ValueError("missing graph header after problem-name line")

        ln, head_text = lines[0]
        head = [int(x) for x in head_text.split()]
        if len(head) != 3:
            raise ValueError(f"line {ln}: expected header n n m")
        n,n2,m = head
        if n < 1 or n2 != n or m < 0:
            raise ValueError(f"line {ln}: invalid square graph header")
        edges = []
        for ln, line in lines[1:]:
            vals = [int(x) for x in line.split()]
            if len(vals) != 2:
                raise ValueError(f"line {ln}: expected exactly two edge endpoints")
            u,v = vals
            if not (1 <= u <= n and 1 <= v <= n):
                raise ValueError(f"line {ln}: endpoint outside 1..{n}")
            edges.append((u-1,v-1))
        if len(edges) != m:
            raise ValueError(f"header m={m}, rows={len(edges)}")
        loops = duplicates = 0
        seen = set()
        degrees = [0]*n
        for u,v in edges:
            if u == v:
                loops += 1
                continue
            e = (min(u,v),max(u,v))
            if e in seen:
                duplicates += 1
                continue
            seen.add(e)
            degrees[u] += 1
            degrees[v] += 1
        delta = max(degrees,default=0)
        rec.update(n_header=n,n_cols=n2,m_header=m,m_file_rows=len(edges),
                   m_clean=len(seen),self_loops_removed=loops,duplicate_edges_removed=duplicates,
                   delta_max=delta,ub_n_minus_delta=(n-delta if delta else ""))
        notes=[]
        if n != int(ref["n"]): notes.append(f"n_header={n} != n_reference={ref['n']}")
        if m != int(ref["m_table"]): notes.append(f"m_header={m} != m_reference={ref['m_table']}")
        if loops: notes.append(f"removed_self_loops={loops}")
        if duplicates: notes.append(f"removed_duplicate_undirected_edges={duplicates}")
        if not delta: notes.append("no non-loop edges; ABP objective undefined")
        rec["notes"]="; ".join(notes)
        rec["status"]=("REFERENCE_MISMATCH" if n != int(ref["n"]) or m != int(ref["m_table"])
                       else "INVALID_GRAPH" if not delta
                       else "VALID_WITH_CLEANING" if loops or duplicates else "VALID")
    except (UnicodeDecodeError,ValueError,OverflowError) as e:
        rec["notes"]=f"{type(e).__name__}: {e}"
    return rec

def inspect_instances(instances_path, data_dir, manifest_path):
    refs=read_inventory(instances_path)
    out=[]
    for r in refs:
        f=data_dir/r["file"]
        try:
            rel=f.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            rel=f.name
        if not f.is_file():
            row=dict.fromkeys(FIELDS,"")
            row.update(id=r["id"],name=r["name"],file=r["file"],status="MISSING",relative_path=rel,
                       n_reference=r["n"],m_reference=r["m_table"],
                       notes="source file absent; file-derived measurements intentionally blank")
        else:
            row=inspect(f,r,rel)
        out.append(row)
    manifest_path.parent.mkdir(parents=True,exist_ok=True)
    with manifest_path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n"); w.writeheader(); w.writerows(out)
    return out, all(r["status"] in ("VALID","VALID_WITH_CLEANING") for r in out)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--instances",type=Path,default=INV); p.add_argument("--data-dir",type=Path,default=DATA)
    p.add_argument("--manifest",type=Path,default=OUT); a=p.parse_args()
    try:
        out,passed=inspect_instances(a.instances,a.data_dir,a.manifest)
    except (OSError,ValueError) as e:
        print(f"ERROR: {e}",file=sys.stderr); return 2
    for row in out:
        print(f"{row['status']:20s} {row['file']}: n={row['n_header'] or '-'} m={row['m_header'] or '-'} "
              f"m_clean={row['m_clean'] or '-'} delta={row['delta_max'] or '-'} UB={row['ub_n_minus_delta'] or '-'}")
        if row["notes"]: print("  "+row["notes"])
    print(f"Wrote {len(out)} manifest rows: {a.manifest}; all-valid={passed}")
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
