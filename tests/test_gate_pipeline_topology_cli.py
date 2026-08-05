"""CLI smoke tests for `autoharness gate pipeline-topology`."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from autoharness.cli import main


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - CLI harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


class PipelineTopologyHelpTests(unittest.TestCase):
    def test_gate_help_lists_pipeline_topology(self) -> None:
        out, _, _ = _run('gate', '--help')
        self.assertIn('pipeline-topology', out)
        self.assertIn('--shipment', out)
        self.assertIn('--phase', out)

    def test_pipeline_topology_help(self) -> None:
        out, _, _ = _run('gate', 'pipeline-topology', '--help')
        self.assertIn('pipeline-topology', out)
        self.assertIn('--shipment', out)
        self.assertIn('--phase', out)


class PipelineTopologyArgTests(unittest.TestCase):
    def test_unknown_flag_exits_2(self) -> None:
        _, _, code = _run('gate', 'pipeline-topology', '--bogus')
        self.assertEqual(code, 2)

    def test_agent_mode_requires_shipment(self) -> None:
        _, _, code = _run('gate', 'pipeline-topology', '--mode', 'agent', '--phase', 'pre_claim')
        self.assertEqual(code, 2)

    def test_agent_mode_requires_non_ambient_phase(self) -> None:
        _, _, code = _run('gate', 'pipeline-topology', '--mode', 'agent', '--shipment', '114-S', '--phase', 'ambient')
        self.assertEqual(code, 2)

    def test_manual_mode_defaults_to_ambient(self) -> None:
        out, _, code = _run('gate', 'pipeline-topology', '--json')
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload['phase'], 'ambient')
        self.assertIsNone(payload['target_shipment_id'])

    def test_agent_mode_echoes_target_and_phase(self) -> None:
        out, _, code = _run(
            'gate', 'pipeline-topology',
            '--mode', 'agent',
            '--shipment', '114-S',
            '--phase', 'pre_claim',
            '--json',
        )
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload['mode'], 'agent')
        self.assertEqual(payload['phase'], 'pre_claim')
        self.assertEqual(payload['target_shipment_id'], '114-S')


if __name__ == '__main__':
    unittest.main()
