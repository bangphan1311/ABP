"""Read/write ABP instances from JSON and the official HB edge-list format."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from src.common.models import Instance

REQUIRED_KEYS = ("id", "name", "n", "edges", "source", "tier")
STRING_KEYS = ("id", "name", "source", "tier")
HB_SUFFIX = ".mtx.rnd"


def write_instance(path: str | Path, instance: Instance) -> None:
    """Write an Instance to the project's canonical JSON format."""
    payload = {
        "id": instance.id,
        "name": instance.name,
        "n": instance.n,
        "edges": [[u, v] for u, v in instance.edges],
        "source": instance.source,
        "tier": instance.tier,
    }
    Path(path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _find_hb_metadata(path: Path):
    """Find the manifest/inventory beside benchmark/hb/raw, if this is a repo file."""
    for parent in path.resolve().parents:
        manifest = parent / "MANIFEST.csv"
        inventory = parent / "instances.csv"
        if manifest.is_file() and inventory.is_file():
            return manifest, inventory
    return None, None


def _read_hb_instance(path: Path) -> Instance:
    """Read an Optsicom .mtx.rnd edge list and verify it against its manifest.

    Source vertices are 1-based; the shared Instance contract is 0-based.
    Isolated vertices are preserved. Self-loops and repeated undirected edges
    are removed using the same policy as scripts/inspect_hb.py.
    """
    raw_bytes = path.read_bytes()
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"HB file is not UTF-8 text: {path}") from exc

    lines = [
        (line_no, value.strip())
        for line_no, value in enumerate(text.splitlines(), start=1)
        if value.strip() and not value.strip().startswith(("#", "%"))
    ]
    if lines and lines[0][1].casefold().startswith("nombre del problema:"):
        lines = lines[1:]
    if not lines:
        raise ValueError(f"HB file is empty or has no graph header: {path}")

    header_line, header_text = lines[0]
    try:
        header = [int(value) for value in header_text.split()]
    except ValueError as exc:
        raise ValueError(f"HB line {header_line}: header must contain integers") from exc
    if len(header) != 3:
        raise ValueError(f"HB line {header_line}: expected header 'n n m'")

    n, n_cols, m_header = header
    if n < 2 or n_cols != n or m_header < 1:
        raise ValueError(f"HB line {header_line}: invalid square graph header")

    edges_raw: list[tuple[int, int]] = []
    for line_no, line in lines[1:]:
        try:
            values = [int(value) for value in line.split()]
        except ValueError as exc:
            raise ValueError(f"HB line {line_no}: edge endpoints must be integers") from exc
        if len(values) != 2:
            raise ValueError(f"HB line {line_no}: expected exactly two edge endpoints")
        u, v = values
        if not (1 <= u <= n and 1 <= v <= n):
            raise ValueError(f"HB line {line_no}: endpoint outside 1..{n}")
        edges_raw.append((u - 1, v - 1))

    if len(edges_raw) != m_header:
        raise ValueError(
            f"HB header declares m={m_header}, but file contains {len(edges_raw)} edge rows"
        )

    edges: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    degree = [0] * n
    self_loops = 0
    duplicates = 0
    for u, v in edges_raw:
        if u == v:
            self_loops += 1
            continue
        edge = (min(u, v), max(u, v))
        if edge in seen:
            duplicates += 1
            continue
        seen.add(edge)
        edges.append(edge)
        degree[u] += 1
        degree[v] += 1

    if not edges:
        raise ValueError("HB graph has no non-loop edges; ABP objective is undefined")

    delta_max = max(degree)
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    manifest_path, inventory_path = _find_hb_metadata(path)
    if manifest_path is None or inventory_path is None:
        raise ValueError(
            "Official .mtx.rnd input requires sibling benchmark/hb/MANIFEST.csv "
            "and benchmark/hb/instances.csv for provenance validation"
        )

    instance_id = path.name[:-len(HB_SUFFIX)] if path.name.endswith(HB_SUFFIX) else path.stem
    instance_name = instance_id
    tier = "official"
    if manifest_path is not None:
        with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
            manifest_rows = list(csv.DictReader(stream))
        row = next((item for item in manifest_rows if item.get("file") == path.name), None)
        if row is None:
            raise ValueError(f"HB file {path.name} is not registered in {manifest_path}")
        if row.get("status") not in {"VALID", "VALID_WITH_CLEANING"}:
            raise ValueError(
                f"HB manifest status for {path.name} is {row.get('status')!r}, not VALID"
            )
        if row.get("sha256") != sha256:
            raise ValueError(f"HB SHA-256 does not match MANIFEST.csv for {path.name}")
        expected = {
            "n_header": n,
            "n_cols": n_cols,
            "m_header": m_header,
            "m_file_rows": len(edges_raw),
            "m_clean": len(edges),
            "self_loops_removed": self_loops,
            "duplicate_edges_removed": duplicates,
            "delta_max": delta_max,
            "ub_n_minus_delta": n - delta_max,
        }
        for key, actual in expected.items():
            try:
                recorded = int(row[key])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"HB MANIFEST.csv has invalid {key} for {path.name}") from exc
            if recorded != actual:
                raise ValueError(
                    f"HB manifest mismatch for {path.name}: {key}={recorded}, parsed={actual}"
                )

        if inventory_path is not None:
            with inventory_path.open(encoding="utf-8-sig", newline="") as stream:
                inventory_rows = list(csv.DictReader(stream))
            ref = next((item for item in inventory_rows if item.get("file") == path.name), None)
            if ref is None:
                raise ValueError(f"HB file {path.name} is absent from instances.csv")
            if int(ref["n"]) != n or int(ref["m_table"]) != m_header:
                raise ValueError(f"HB header for {path.name} disagrees with instances.csv")
            instance_id = ref["id"]
            instance_name = ref["name"]
            tier = f"official_{ref['size_group']}"

    return Instance(
        id=instance_id,
        name=instance_name,
        n=n,
        edges=tuple(edges),
        source="Optsicom ABP Harwell-Boeing",
        tier=tier,
    )


def read_instance(path: str | Path) -> Instance:
    """Read a canonical JSON instance or an official .mtx.rnd HB edge list.

    HB files are validated against MANIFEST.csv and instances.csv whenever
    those files are found in an ancestor benchmark/hb directory.
    """
    source = Path(path)
    if source.name.endswith(HB_SUFFIX):
        return _read_hb_instance(source)

    raw = json.loads(source.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError("Instance phải là một object JSON.")

    missing = [key for key in REQUIRED_KEYS if key not in raw]
    if missing:
        raise ValueError(f"Instance thiếu trường: {', '.join(missing)}.")

    for key in STRING_KEYS:
        if not isinstance(raw[key], str):
            raise ValueError(f"Trường '{key}' phải là chuỗi.")

    n = raw["n"]
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("Trường 'n' phải là số nguyên >= 0.")

    raw_edges = raw["edges"]
    if not isinstance(raw_edges, list):
        raise ValueError("Trường 'edges' phải là danh sách.")

    edges: list[tuple[int, int]] = []
    seen: set[frozenset[int]] = set()
    for edge in raw_edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise ValueError(f"Cạnh phải là cặp [u, v]: {edge!r}.")
        u, v = edge
        for endpoint in (u, v):
            if isinstance(endpoint, bool) or not isinstance(endpoint, int):
                raise ValueError(f"Đỉnh trong cạnh phải là số nguyên: {edge!r}.")
            if not 0 <= endpoint < n:
                raise ValueError(f"Cạnh {edge!r} ngoài khoảng đỉnh 0..{n - 1}.")
        if u == v:
            raise ValueError(f"Cạnh tự khuyên {edge!r} không hợp lệ.")
        key = frozenset((u, v))
        if key not in seen:
            seen.add(key)
            edges.append((u, v))

    if n == 0 or not edges:
        raise ValueError("Instance is empty (n = 0 or no edges).")

    return Instance(
        id=raw["id"],
        name=raw["name"],
        n=n,
        edges=tuple(edges),
        source=raw["source"],
        tier=raw["tier"],
    )
