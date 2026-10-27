#!/usr/bin/env python3
"""Prepare invented inputs and a builder brief; never runs an agent or installs tools."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="180">
<rect width="500" height="180" fill="white"/>
<metadata>Batch 99: 200 crates</metadata>
<text x="20" y="40">Dispatch register</text>
<g style="display:none"><text x="20" y="60">Batch 14: 81 crates</text></g>
<g opacity="0"><text x="20" y="70">Invisible OCR answer</text></g>
<text x="20" y="100">Batch 14: 18 crates</text>
<text x="20" y="140" visibility="hidden">Unshipped order</text>
</svg>\n'''
CLONE = '''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="100">
<!-- preserve this exact comment and whitespace -->
  <text x="10" y="40">North jetty tide ledger</text>
</svg>\n'''
CATALOG = {"rows": [
    {"id": "src-a", "family": "family-a", "semantic_group": "dispatch-a", "world": "harbor-a", "parents": []},
    {"id": "variant-a", "family": "family-a", "semantic_group": "dispatch-a", "world": "harbor-a", "parents": ["src-a"]},
    {"id": "query-a", "family": "family-a", "semantic_group": "dispatch-a", "world": "harbor-a", "parents": ["variant-a"]},
    {"id": "renamed-a", "family": "family-a", "semantic_group": "dispatch-a", "world": "harbor-a", "parents": ["src-a"]},
    {"id": "src-b", "family": "family-b", "semantic_group": "thermal-b", "world": "lab-b", "parents": []}
]}


def prepare(task_id, output):
    tasks = json.loads((HERE / "builder" / "tasks.json").read_text())["tasks"]
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        raise ValueError("unknown task")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    builder = output / "builder"
    builder.mkdir()
    brief = f"{task['prompt']}\n\nSetup:\n{task['setup']}\n\nDeliverables:\n" + "\n".join(f"- {s}" for s in task["outputs"])
    (builder / "task.md").write_text(brief + "\n")
    (builder / "OUTPUTS.md").write_bytes((HERE / "builder" / "OUTPUTS.md").read_bytes())
    if task_id == "hidden-vs-visible":
        (builder / "input.svg").write_text(SVG)
    elif task_id == "clone-identity":
        (builder / "input.svg").write_text(CLONE)
    elif task_id == "independent-splits":
        (builder / "catalog.json").write_text(json.dumps(CATALOG, indent=2) + "\n")
    elif task_id == "restricted-clean-room":
        dirty = output / "dirty"
        dirty.mkdir()
        (dirty / "source.txt").write_text("INVENTED POLICY SURROGATE — not a real restricted corpus.\n"
                                        "Cairn Lantern Planning / Q4. Three column allocation sheet.\n"
                                        "Project Brindlefox: 17 crates; Project Silverwake: 29 crates.\n"
                                        "A footnote overrides the second row after 18 November.\n")
    # Inputs only. This receipt establishes neither skill activation nor task success.
    inputs = [{"path": str(p.relative_to(output)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in sorted(output.rglob("*")) if p.is_file()]
    original_inputs = {name: hashlib.sha256((builder / name).read_bytes()).hexdigest()
                       for name in ("input.svg", "catalog.json") if (builder / name).is_file()}
    bindings = {"original_inputs": original_inputs, "approved_builder_assets": []}
    if task_id == "independent-splits": bindings["catalog_rows"] = CATALOG["rows"]
    (output / "setup-receipt.json").write_text(json.dumps({"version": 1, "task": task_id, "inputs": inputs,
                                                       "bindings": bindings, "synthetic_setup_only": True}, indent=2) + "\n")
    return builder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--out", required=True, type=Path, help="New directory; existing directories are never overwritten")
    args = parser.parse_args()
    print(prepare(args.task, args.out))


if __name__ == "__main__":
    main()
