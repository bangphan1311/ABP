import csv
import hashlib
from pathlib import Path

from experiments import pilot_exact_p1 as pilot


def make_inputs(root: Path):
    hb = root / "benchmark" / "hb"
    raw = hb / "raw"
    raw.mkdir(parents=True)

    ids = list(pilot.VALIDATION_IDS) + list(pilot.LARGE_IDS)
    ids += [f"other_{i:02d}" for i in range(11)]

    inventory_rows = []
    manifest_rows = []
    for index, instance_id in enumerate(ids):
        filename = f"{instance_id}.mtx.rnd"
        inventory_rows.append({
            "id": instance_id,
            "name": instance_id,
            "file": filename,
            "size_group": "small" if index < 12 else "large",
            "n": 4,
            "m_table": 3,
        })

        if instance_id in pilot.VALIDATION_IDS or instance_id in pilot.LARGE_IDS:
            path = raw / filename
            path.write_text("4 4 3\n1 2\n2 3\n3 4\n", encoding="utf-8")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            status = "VALID"
            n_header, n_cols, m_header, m_rows, m_clean = 4, 4, 3, 3, 3
            loops, duplicates, delta, ub = 0, 0, 2, 2
        else:
            sha = ""
            status = "MISSING"
            n_header = n_cols = m_header = m_rows = m_clean = ""
            loops = duplicates = delta = ub = ""

        manifest_rows.append({
            "id": instance_id, "name": instance_id, "file": filename,
            "status": status, "sha256": sha, "n_reference": 4, "m_reference": 3,
            "n_header": n_header, "n_cols": n_cols, "m_header": m_header,
            "m_file_rows": m_rows, "m_clean": m_clean,
            "self_loops_removed": loops, "duplicate_edges_removed": duplicates,
            "delta_max": delta, "ub_n_minus_delta": ub, "notes": "",
        })

    with (hb / "instances.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["id", "name", "file", "size_group", "n", "m_table"],
        )
        writer.writeheader()
        writer.writerows(inventory_rows)

    with (hb / "MANIFEST.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)

    return hb / "instances.csv", hb / "MANIFEST.csv", raw


def test_exact_pilot_plan_has_40_sequential_runs(monkeypatch, tmp_path):
    inventory, manifest, raw = make_inputs(tmp_path)
    monkeypatch.setattr(pilot, "INVENTORY", inventory)
    monkeypatch.setattr(pilot, "MANIFEST", manifest)
    monkeypatch.setattr(pilot, "RAW_DIR", raw)

    plan = pilot.load_run_plan()

    assert len(plan) == 40
    assert [item[0] for item in plan[:4]] == [pilot.VALIDATION_IDS[0]] * 4
    assert [item[2] for item in plan[:4]] == list(pilot.EXACT_METHODS)
    assert all(item[3] == pilot.PILOT_TIME_LIMIT for item in plan)


def test_exact_pilot_large_adds_only_12_runs(monkeypatch, tmp_path):
    inventory, manifest, raw = make_inputs(tmp_path)
    monkeypatch.setattr(pilot, "INVENTORY", inventory)
    monkeypatch.setattr(pilot, "MANIFEST", manifest)
    monkeypatch.setattr(pilot, "RAW_DIR", raw)

    plan = pilot.load_run_plan(include_large=True)

    assert len(plan) == 52
    large = [item for item in plan if item[0] in pilot.LARGE_IDS]
    assert len(large) == 12
    assert all(item[3] == pilot.PILOT_LARGE_TIME_LIMIT for item in large)


def test_exact_pilot_refuses_missing_selected_raw_data(monkeypatch, tmp_path):
    inventory, manifest, raw = make_inputs(tmp_path)
    (raw / "pores_1.mtx.rnd").unlink()
    monkeypatch.setattr(pilot, "INVENTORY", inventory)
    monkeypatch.setattr(pilot, "MANIFEST", manifest)
    monkeypatch.setattr(pilot, "RAW_DIR", raw)

    try:
        pilot.load_run_plan()
    except FileNotFoundError as exc:
        assert "pores_1.mtx.rnd" in str(exc)
    else:
        raise AssertionError("missing raw HB input must stop before any solver starts")
