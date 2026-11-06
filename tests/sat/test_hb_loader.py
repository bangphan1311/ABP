import csv
import hashlib
from pathlib import Path

import pytest

from src.sat.loader import read_instance


def write_hb(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_metadata(root: Path, file_name: str, sha: str, *, n: int, m: int, delta: int):
    hb = root / "benchmark" / "hb"
    hb.mkdir(parents=True, exist_ok=True)
    raw_dir = hb / "raw"
    raw_dir.mkdir(exist_ok=True)
    with (hb / "instances.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["id", "name", "file", "size_group", "n", "m_table"],
        )
        writer.writeheader()
        writer.writerow({
            "id": "path4", "name": "path4", "file": file_name,
            "size_group": "small", "n": n, "m_table": m,
        })
    with (hb / "MANIFEST.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "id", "name", "file", "status", "sha256", "n_header", "n_cols",
                "m_header", "m_file_rows", "m_clean", "self_loops_removed",
                "duplicate_edges_removed", "delta_max", "ub_n_minus_delta",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "id": "path4", "name": "path4", "file": file_name, "status": "VALID",
            "sha256": sha, "n_header": n, "n_cols": n, "m_header": m,
            "m_file_rows": m, "m_clean": m, "self_loops_removed": 0,
            "duplicate_edges_removed": 0, "delta_max": delta,
            "ub_n_minus_delta": n - delta,
        })


def test_read_hb_mtx_rnd_converts_one_based_edges_and_keeps_vertices(tmp_path):
    name = "path4.mtx.rnd"
    hb_root = tmp_path / "benchmark" / "hb"
    raw_dir = hb_root / "raw"
    raw_dir.mkdir(parents=True)
    content = "Nombre del problema: path4\n4 4 3\n1 2\n2 3\n3 4\n"
    sha = write_hb(raw_dir / name, content)
    write_metadata(tmp_path, name, sha, n=4, m=3, delta=2)

    instance = read_instance(raw_dir / name)

    assert instance.id == "path4"
    assert instance.name == "path4"
    assert instance.n == 4
    assert instance.edges == ((0, 1), (1, 2), (2, 3))
    assert instance.source == "Optsicom ABP Harwell-Boeing"
    assert instance.tier == "official_small"


def test_read_hb_removes_reversed_duplicates_and_self_loops_consistently(tmp_path):
    name = "path4.mtx.rnd"
    hb_root = tmp_path / "benchmark" / "hb"
    raw_dir = hb_root / "raw"
    raw_dir.mkdir(parents=True)
    content = "% comment\n4 4 5\n1 2\n2 1\n2 2\n2 3\n3 4\n"
    sha = write_hb(raw_dir / name, content)
    # The manifest is the single source of truth for the cleaning policy.
    hb = hb_root
    with (hb / "instances.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "name", "file", "size_group", "n", "m_table"])
        writer.writeheader()
        writer.writerow({"id": "path4", "name": "path4", "file": name, "size_group": "small", "n": 4, "m_table": 5})
    with (hb / "MANIFEST.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "id","name","file","status","sha256","n_header","n_cols","m_header",
            "m_file_rows","m_clean","self_loops_removed","duplicate_edges_removed",
            "delta_max","ub_n_minus_delta"
        ])
        writer.writeheader()
        writer.writerow({
            "id":"path4","name":"path4","file":name,"status":"VALID_WITH_CLEANING",
            "sha256":sha,"n_header":4,"n_cols":4,"m_header":5,"m_file_rows":5,
            "m_clean":3,"self_loops_removed":1,"duplicate_edges_removed":1,
            "delta_max":2,"ub_n_minus_delta":2
        })

    instance = read_instance(raw_dir / name)
    assert instance.n == 4
    assert instance.edges == ((0, 1), (1, 2), (2, 3))


def test_read_hb_rejects_hash_mismatch_against_manifest(tmp_path):
    name = "path4.mtx.rnd"
    raw_dir = tmp_path / "benchmark" / "hb" / "raw"
    raw_dir.mkdir(parents=True)
    sha = write_hb(raw_dir / name, "4 4 3\n1 2\n2 3\n3 4\n")
    write_metadata(tmp_path, name, "0" * 64, n=4, m=3, delta=2)

    with pytest.raises(ValueError, match="SHA-256"):
        read_instance(raw_dir / name)


def test_read_hb_rejects_manifest_measurement_mismatch(tmp_path):
    name = "path4.mtx.rnd"
    raw_dir = tmp_path / "benchmark" / "hb" / "raw"
    raw_dir.mkdir(parents=True)
    sha = write_hb(raw_dir / name, "4 4 3\n1 2\n2 3\n3 4\n")
    write_metadata(tmp_path, name, sha, n=4, m=3, delta=3)

    with pytest.raises(ValueError, match="delta_max"):
        read_instance(raw_dir / name)


def test_json_instance_reader_remains_compatible(tmp_path):
    path = tmp_path / "path4.json"
    path.write_text(
        '{"id":"path4","name":"path4","n":4,"edges":[[0,1],[1,2],[2,3]],"source":"test","tier":"toy"}',
        encoding="utf-8",
    )

    instance = read_instance(path)
    assert instance.id == "path4"
    assert instance.edges == ((0, 1), (1, 2), (2, 3))
