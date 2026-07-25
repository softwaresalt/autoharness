#!/usr/bin/env python3
"""Benchmark corpus runner CLI (088.006-T).

Builds the default corpus (real, read-only autoharness commands plus
clearly-labeled synthetic decline/negative-control fixtures), runs it
through the postToolUse hook + retrieval + measurement pipeline, and
writes a consolidated Markdown + JSON report.

Not wired into any CI job or pre-push hook by default — this is a manual,
opt-in benchmark tool for the 088-F throwaway experiment. Run with:

    python experiments/088-compression-experiment/brainspace/benchmark_cli.py

from the repository root.
"""

import argparse
import json
import os
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_EXPERIMENT_ROOT = os.path.dirname(_THIS_DIR)
if _EXPERIMENT_ROOT not in sys.path:
    sys.path.insert(0, _EXPERIMENT_ROOT)

from brainspace import config  # noqa: E402
from brainspace.benchmark import (  # noqa: E402
    render_json_report,
    render_markdown_report,
    run_benchmark,
)
from brainspace.corpus import build_default_corpus  # noqa: E402
from brainspace.store import BrainspaceStore  # noqa: E402

_DEFAULT_OUT_DIR = os.path.join(_EXPERIMENT_ROOT, "reports")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=os.getcwd())
    parser.add_argument("--out-dir", default=_DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    os.makedirs(args.out_dir, exist_ok=True)

    # Enable the experiment flag only for this process's own run — never
    # persisted, never leaked into the ambient environment for other
    # processes (disabled-by-default invariant stays intact).
    previously_set = os.environ.get(config.ENABLED_ENV_VAR)
    os.environ[config.ENABLED_ENV_VAR] = "1"
    try:
        with tempfile.TemporaryDirectory() as tmp_store_dir:
            store = BrainspaceStore(tmp_store_dir)
            try:
                cases = build_default_corpus(args.repo_root)
                report = run_benchmark(cases, store=store)
            finally:
                store.close()
    finally:
        if previously_set is None:
            os.environ.pop(config.ENABLED_ENV_VAR, None)
        else:
            os.environ[config.ENABLED_ENV_VAR] = previously_set

    markdown = render_markdown_report(report)
    payload = render_json_report(report)

    md_path = os.path.join(args.out_dir, "benchmark-report.md")
    json_path = os.path.join(args.out_dir, "benchmark-report.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
