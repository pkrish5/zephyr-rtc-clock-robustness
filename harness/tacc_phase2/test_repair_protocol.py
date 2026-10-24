"""Offline policy checks only; no compiler, model, Renode or SSH calls."""
import copy
import unittest
from pathlib import Path
from support import read, sha
from finalize_e import gate_valid

ROOT=Path(__file__).resolve().parents[2]


class RepairProtocolChecks(unittest.TestCase):
    def test_infrastructure_missingness_cannot_pass_gate(self):
        base=dict(builds={'nominal':{'status':'pass'}},nominal_outcomes=[{'outcome':'pass'} for _ in range(5)])
        self.assertTrue(gate_valid(base,5))
        for status in ('fail','harness_error','timeout','unknown'):
            changed=copy.deepcopy(base)
            changed['nominal_outcomes'][3]['outcome']=status
            self.assertFalse(gate_valid(changed,5),status)
        changed=copy.deepcopy(base);changed['nominal_outcomes'].pop()
        self.assertFalse(gate_valid(changed,5))
        changed=copy.deepcopy(base);changed['builds']['nominal']['status']='build_fail'
        self.assertFalse(gate_valid(changed,5))

    def test_split_is_not_confounded_by_shortening_in_v1(self):
        vs=read(ROOT/'notes/repair_execution_20261024_v2/variants.json')['versions']
        self.assertEqual(len(vs),165)
        for v in vs.values():
            if v['variant']=='V1':
                self.assertGreaterEqual(v['scalar_ceiling_ms'],v['original_budget_ms'])
                if v['original_budget_ms']>=20824:
                    self.assertEqual(v['variant_source_sha256'],v['source_sha256'])
            if v['variant']=='V1b':self.assertEqual(v['scalar_ceiling_ms'],20824)

    def test_approved_v2_v3_examples_are_byte_identical(self):
        vs=read(ROOT/'notes/repair_execution_20261024_v2/variants.json')['versions']
        for sid,label in [('human-rtc_alarm_callback','upstream_callback'),
                          ('sol-range_absent-rtc_alarm_pending-r03','generated_sol_pending')]:
            for name in ('V2','V3'):
                self.assertEqual(sha(ROOT/vs[sid+'--'+name]['variant_source_path']),
                    sha(ROOT/'notes/repair_review_2026-10-24/examples'/label/name/'test.c'))


if __name__=='__main__':unittest.main()
