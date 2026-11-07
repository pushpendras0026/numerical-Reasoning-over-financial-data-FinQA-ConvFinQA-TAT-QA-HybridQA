import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from nrqa.experiment import ROOT, Mock, freeze, run

class BoundedCheckpointTests(unittest.TestCase):
    def test_interrupt_cannot_mark_complete_and_keeps_inflight(self):
        class Interrupt(Mock):
            def generate(self,request):raise KeyboardInterrupt()
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);freeze(ROOT/'experiments/smoke.json',d/'f.json')
            m=run(d/'f.json',d/'out','mock',Interrupt)
            self.assertEqual(m['status'],'stopped')
            self.assertEqual(m['uncertain_requests'],1)
            self.assertEqual(m['completed_requests'],0)
    def test_deadline_prevents_new_dispatch(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'NRQA_DISPATCH_DEADLINE':'0'}):
            d=Path(d);freeze(ROOT/'experiments/smoke.json',d/'f.json')
            m=run(d/'f.json',d/'out','mock')
            self.assertEqual(m['status'],'stopped')
            self.assertEqual(m['model_calls'],0)
