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
from brainspace.workspace import WorkspaceContainmentError, resolve_workspace_root  # noqa: E402

_DEFAULT_OUT_DIR = os.path.join(_EXPERIMENT_ROOT, "reports")


def _resolve_contained_out_dir(out_dir: str, *, repo_root: str) -> str:
    """Resolve ``out_dir`` against ``repo_root`` and reject any target that
    escapes it (P-018 round-3 finding #4). A relative ``out_dir`` is joined
    onto ``repo_root``; an absolute path or a ``..``-relative path that
    resolves outside ``repo_root`` is rejected before anything is created or
    written, per the repository's non-negotiable CLI containment rule.
    """
    candidate = out_dir if os.path.isabs(out_dir) else os.path.join(repo_root, out_dir)
    real_repo_root = os.path.realpath(repo_root)
    real_candidate = os.path.realpath(candidate)
    try:
        common = os.path.commonpath([real_candidate, real_repo_root])
    except ValueError:
        common = None
    if common != real_repo_root:
        raise ValueError(
            f"--out-dir must resolve inside --repo-root ({repo_root!r}); "
            f"got {out_dir!r} which resolves to {real_candidate!r}"
        )
    return candidate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=os.getcwd())
    parser.add_argument("--out-dir", default=_DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    # P-018 round-3 follow-up finding: --out-dir was contained only relative
    # to --repo-root, but --repo-root itself was trusted verbatim -- an
    # unrelated --repo-root would create the cache and reports outside the
    # current working tree, bypassing this round's containment rule
    # entirely. Reuse the same containment validation applied to every
    # other 088-F entry point's explicit_root.
    try:
        args.repo_root = resolve_workspace_root(explicit_root=args.repo_root)
    except WorkspaceContainmentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    args.out_dir = _resolve_contained_out_dir(args.out_dir, repo_root=args.repo_root)
    os.makedirs(args.out_dir, exist_ok=True)

    # Enable the experiment flag only for this process's own run — never
    # persisted, never leaked into the ambient environment for other
    # processes (disabled-by-default invariant stays intact).
    previously_set = os.environ.get(config.ENABLED_ENV_VAR)
    os.environ[config.ENABLED_ENV_VAR] = "1"
    try:
        # Anchor the ephemeral benchmark store under the repo-local,
        # gitignored store directory -- NOT the OS temp area (P-018
        # re-review finding #3, new round). TemporaryDirectory() with no
        # ``dir=`` kwarg defaults to the OS temp area, which violates the
        # containment requirement in config.py even though the directory is
        # short-lived and auto-cleaned.
        store_parent_dir = os.path.join(args.repo_root, config.STORE_RELATIVE_DIR)
        os.makedirs(store_parent_dir, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=store_parent_dir) as tmp_store_dir:
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
