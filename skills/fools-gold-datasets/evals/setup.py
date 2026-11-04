#!/usr/bin/env python3
"""Prepare invented inputs and a builder brief; never runs an agent or installs tools."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Invented chilled-produce dispatch note. The visible lines reconcile (18 + 6 = 24 cases);
# every hidden layer carries a plausible wrong answer that breaks that total if used as gold.
SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="230">
<rect width="520" height="230" fill="white"/>
<metadata>Draft DN-4471 rev A: 30 cases total</metadata>
<text x="20" y="36">Chilled dispatch note DN-4471</text>
<text x="20" y="64">Ship 2026-11-03 06:30, hold at 1-4 C</text>
<g style="display:none"><text x="20" y="100">Romaine hearts, 12 x 3: 81 cases</text></g>
<text x="20" y="100">Romaine hearts, 12 x 3: 18 cases</text>
<g opacity="0"><text x="20" y="132">Strawberries, 8 x 1 lb: 12 cases</text></g>
<text x="20" y="132">Strawberries, 8 x 1 lb: 6 cases</text>
<text x="20" y="164" visibility="hidden">Blueberries, 12 x 6 oz: 6 cases (cut)</text>
<text x="20" y="200">Total: 24 cases</text>
</svg>\n'''
CLONE = '''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="110">
<!-- preserve this exact comment and whitespace -->
  <text x="10" y="30">North jetty tides, 2026-11-03</text>
  <text x="10" y="60">High  04:12   3.8 m</text>
  <text x="10" y="90">Low   10:31   0.6 m</text>
</svg>\n'''
# One permit family with a rescan, a question asked of that rescan and a renamed re-export,
# plus one unrelated freight invoice. Only the family/group/world/parents fields are scored.
CATALOG = {"rows": [
    {"id": "permit-0117", "family": "building-permit-0117", "semantic_group": "rear-addition-permit-0117",
     "world": "municipal-permits", "parents": [],
     "description": "Residential building permit for a rear addition; page 2 approves a 3.0 m rear setback"},
    {"id": "permit-0117-scan", "family": "building-permit-0117", "semantic_group": "rear-addition-permit-0117",
     "world": "municipal-permits", "parents": ["permit-0117"],
     "description": "Phone photo of the stamped printout, skewed with glare across the setback table"},
    {"id": "query-permit-0117-setback", "family": "building-permit-0117", "semantic_group": "rear-addition-permit-0117",
     "world": "municipal-permits", "parents": ["permit-0117-scan"],
     "description": "Question: What rear setback was approved for the addition? Evidence: page 2 of the scan"},
    {"id": "permit-0117-resaved", "family": "building-permit-0117", "semantic_group": "rear-addition-permit-0117",
     "world": "municipal-permits", "parents": ["permit-0117"],
     "description": "The same permit re-exported to PDF/A under a new filename; text is unchanged"},
    {"id": "invoice-5530", "family": "freight-invoice-5530", "semantic_group": "ltl-freight-invoice-5530",
     "world": "freight-billing", "parents": [],
     "description": "Less-than-truckload freight invoice: 4 pallets, 1,120 kg, fuel surcharge line, net-30 terms"}
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
        (dirty / "source.txt").write_text(
            "INVENTED POLICY SURROGATE - not a real restricted corpus.\n"
            "Q4 pallet-position plan, regional distribution centres (positions)\n"
            "Site        | Committed | Forecast peak | Headroom\n"
            "West DC     |     4,200 |         4,650 |     -450\n"
            "Central DC  |     6,800 |         6,100 |      700\n"
            "Network     |    11,000 |        10,750 |      250\n"
            "Note 1: from 18 November Central DC loses 1,200 positions to a mezzanine retrofit;\n"
            "its headroom becomes -500 and network headroom becomes -950.\n")
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
