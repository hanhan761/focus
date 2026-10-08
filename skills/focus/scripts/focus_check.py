#!/usr/bin/env python3
"""Read-only checks for a focus checkpoint. Evidence contents are not verified."""
import argparse
import json
import math
import sys
from pathlib import Path


class FocusError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise FocusError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def records(data, key, *, required=False):
    value = data.get(key)
    require(isinstance(value, list), f"{key}: expected a list")
    require(not required or bool(value), f"{key}: must not be empty")
    require(all(isinstance(item, dict) for item in value),
            f"{key}: expected object entries")
    return value


def strings(data, keys, location):
    for key in keys:
        require(nonempty(data.get(key)), f"{location}.{key}: expected nonempty text")


def measurement(value):
    return nonempty(value) or (
        type(value) in (int, float) and math.isfinite(value)
    )


def evidence(items, location):
    require(isinstance(items, list), f"{location}: expected a list")
    for i, item in enumerate(items):
        require(isinstance(item, dict), f"{location}[{i}]: expected an object")
        strings(item, ("source", "revision", "observation"), f"{location}[{i}]")
        require(all(item[key].strip().lower() != "unknown"
                    for key in ("source", "revision", "observation")),
                f"{location}[{i}]: evidence cannot be unknown")
    return bool(items)


def unique_ids(items, location):
    ids = [item.get("id") for item in items]
    require(all(nonempty(i) for i in ids), f"{location}: nonempty IDs required")
    require(len(ids) == len(set(ids)), f"{location}: duplicate IDs")
    return set(ids)


def evaluate(data, *, stall_limit=2, complete=False):
    require(isinstance(data, dict), "checkpoint: expected an object")
    require(type(data.get("schema_version")) is int and data["schema_version"] == 1,
            "schema_version: expected 1")
    require(type(stall_limit) is int and stall_limit > 0,
            "stall_limit: expected a positive integer")
    strings(data, ("task_id", "project_root", "updated_at", "objective", "problem"),
            "checkpoint")
    require(data.get("status") in ("active", "blocked", "complete"),
            "status: expected active, blocked or complete")
    require(isinstance(data.get("plan_ref"), str), "plan_ref: expected text")
    for key in ("decisions", "parking"):
        require(isinstance(data.get(key), list)
                and all(nonempty(v) for v in data[key]), f"{key}: expected text entries")

    instructions = records(data, "instructions", required=True)
    for i, item in enumerate(instructions):
        strings(item, ("source", "scope", "rule"), f"instructions[{i}]")
    conflicts = records(data, "conflicts")
    for i, item in enumerate(conflicts):
        require(isinstance(item.get("sources"), list)
                and len(item["sources"]) >= 2
                and all(nonempty(s) for s in item["sources"]),
                f"conflicts[{i}].sources: at least two sources required")
        require(isinstance(item.get("resolution"), str),
                f"conflicts[{i}].resolution: expected text")

    metrics = records(data, "metrics", required=True)
    metric_ids = unique_ids(metrics, "metrics")
    verified, unverified = [], []
    for i, item in enumerate(metrics):
        strings(item, ("name", "check"), f"metrics[{i}]")
        for key in ("baseline", "target", "current"):
            require(measurement(item.get(key)), f"metrics[{i}].{key}: expected a value")
        require(str(item["target"]).strip().lower() != "unknown",
                f"metrics[{i}].target: a concrete target is required")
        require(item.get("status") in ("pending", "pass", "fail"),
                f"metrics[{i}].status: expected pending, pass or fail")
        has_evidence = evidence(item.get("evidence"), f"metrics[{i}].evidence")
        if item["status"] == "pass":
            if has_evidence and str(item["current"]).strip().lower() != "unknown":
                verified.append(item["id"])
            else:
                unverified.append(item["id"])

    workflow = records(data, "workflow", required=True)
    step_ids = unique_ids(workflow, "workflow")
    aligned = 0
    for i, step in enumerate(workflow):
        strings(step, ("action", "output", "check"), f"workflow[{i}]")
        require(step.get("status") in ("todo", "doing", "done"),
                f"workflow[{i}].status: expected todo, doing or done")
        links = step.get("metric_ids")
        require(isinstance(links, list) and all(nonempty(v) for v in links),
                f"workflow[{i}].metric_ids: expected text entries")
        require(len(links) == len(set(links)), f"workflow[{i}]: duplicate metric links")
        require(all(v in metric_ids for v in links), f"workflow[{i}]: unknown metric ID")
        aligned += bool(links)

    cycles = records(data, "cycles")
    for i, cycle in enumerate(cycles):
        strings(cycle, ("step_id", "action", "result"), f"cycles[{i}]")
        require(cycle["step_id"] in step_ids, f"cycles[{i}]: unknown step ID")
        require(type(cycle.get("new_evidence")) is bool,
                f"cycles[{i}].new_evidence: expected a boolean")
        has_evidence = evidence(cycle.get("evidence"), f"cycles[{i}].evidence")
        require(not cycle["new_evidence"] or has_evidence,
                f"cycles[{i}]: new evidence must include a receipt")

    checkpoint = data.get("checkpoint")
    require(isinstance(checkpoint, dict), "checkpoint: recovery fields required")
    strings(checkpoint, ("last_verified_action", "next_action"), "checkpoint")
    artifacts = records(checkpoint, "artifacts")
    for i, artifact in enumerate(artifacts):
        strings(artifact, ("path", "revision", "summary"), f"checkpoint.artifacts[{i}]")

    stalled = 0
    for cycle in reversed(cycles):
        if cycle["new_evidence"]:
            break
        stalled += 1
    unresolved = sum(not c["resolution"].strip() for c in conflicts)
    doing = sum(s["status"] == "doing" for s in workflow)
    unfinished = [s["id"] for s in workflow if s["status"] != "done"]
    pending = [m["id"] for m in metrics if m["id"] not in verified]
    warnings = []
    if aligned != len(workflow):
        warnings.append("Some workflow actions are not linked to a metric.")
    if doing > 1:
        warnings.append("The focus summary has multiple doing steps.")
    if unresolved:
        warnings.append("Resolve applicable instruction conflicts before dependent work.")
    if unverified:
        warnings.append("Some pass claims have no recorded evidence or actual current value.")
    if stalled >= stall_limit and (pending or unfinished):
        warnings.append("No new evidence in consecutive cycles: refocus and change the method.")
    eligible = not pending and not unfinished and not warnings and data["status"] != "blocked"
    if data["status"] == "complete" and not eligible:
        warnings.append("The checkpoint claims complete before the recorded acceptance gate.")
    code = 1 if warnings else (3 if complete and not eligible else 0)
    return code, {
        "task_id": data["task_id"],
        "verification": {"recorded": len(verified), "total": len(metrics),
                         "coverage_percent": round(100 * len(verified) / len(metrics), 1)},
        "action_alignment_percent": round(100 * aligned / len(workflow), 1),
        "doing_steps": doing, "unresolved_conflicts": unresolved,
        "unverified_pass_claims": unverified, "stall_streak": stalled,
        "remaining_metrics": pending, "unfinished_steps": unfinished,
        "recorded_completion_eligible": eligible, "warnings": warnings,
        "limit": "Evidence metadata only; inspect actual artifacts, inputs and revisions."
    }


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"JSON: duplicate key {key!r}")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    parser.add_argument("--complete", action="store_true", help="require recorded acceptance")
    parser.add_argument("--stall-limit", type=int, default=2)
    args = parser.parse_args()
    try:
        data = json.loads(args.checkpoint.read_text(encoding="utf-8-sig"),
                          object_pairs_hook=no_duplicate_keys)
        code, report = evaluate(data, stall_limit=args.stall_limit, complete=args.complete)
    except (OSError, ValueError, RecursionError) as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        else:
            print(f"Invalid checkpoint: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        v = report["verification"]
        print(f"Task: {report['task_id']}")
        print(f"Recorded verification: {v['recorded']}/{v['total']} ({v['coverage_percent']}%)")
        print(f"Action alignment: {report['action_alignment_percent']}%; "
              f"doing: {report['doing_steps']}; conflicts: {report['unresolved_conflicts']}; "
              f"stall streak: {report['stall_streak']}")
        print(f"Recorded acceptance eligible: {report['recorded_completion_eligible']}")
        for warning in report["warnings"]:
            print(f"Refocus: {warning}")
        print(report["limit"])
    return code


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
