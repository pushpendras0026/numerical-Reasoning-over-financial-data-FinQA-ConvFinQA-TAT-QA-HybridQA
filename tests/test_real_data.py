"""Real release regressions. Missing external inputs are skipped visibly by unittest;
validate_local reports their exact availability separately and never substitutes fixtures.
"""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nrqa.core import canonical
from nrqa.datasets import multi,hybrid
from nrqa.data_paths import source_path,corpus_path,ROOT
from nrqa.data_validation import audit_hybrid,check_example
from nrqa.scoring import official_score,convert_output
from nrqa.core import PredictionExample,ReferenceRecord

DEV=ROOT.parent/'MultiHiertt_data/multihiertt_data/dev.json'

class PathsAndMissingCorpus(unittest.TestCase):
    def test_explicit_root_override(self):
        with patch.dict('os.environ',{'NRQA_MULTIHIERTT_ROOT':'/tmp/nrqa-alternate-data'}):
            self.assertEqual(source_path({'dataset':'multihiertt','source':'../other/dev.json'}),Path('/tmp/nrqa-alternate-data/dev.json'))
        with patch.dict('os.environ',{'NRQA_HYBRIDQA_CORPUS':'/tmp/explicit-missing-corpus'}):
            self.assertEqual(corpus_path({'corpus':'auto'}),Path('/tmp/explicit-missing-corpus'))
    def test_missing_resources_block_every_affected_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'dev.json';path.write_text(json.dumps([
                {'question_id':'q1','question':'x','table_id':'table-a'},
                {'question_id':'q2','question':'y','table_id':'table-a'},
                {'question_id':'q3','question':'z','table_id':'table-b'}]))
            report=audit_hybrid({'dataset':'hybridqa','source':str(path),'split':'test','corpus':str(Path(tmp)/'missing')})
            self.assertEqual(report['questions'],3);self.assertEqual(report['unique_tables'],2)
            self.assertEqual(report['validated_prediction_inputs'],0);self.assertEqual(report['blocked_question_ids'],['q1','q2','q3'])
            self.assertEqual(len(report['missing_resources']),2)

@unittest.skipUnless(DEV.exists(),'Real MultiHiertt release not present')
class RealMultiHiertt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=json.loads(DEV.read_text())
    def test_td_headers_units_markers_and_firewall(self):
        raw=self.rows[0];ex,_=multi(raw,'dev',str(DEV),0);check_example(ex)
        target=next(f for f in ex.facts if f.source.get('cell_id')=='0-2-4')
        facts={f.id:f for f in ex.facts};ancestors=set()
        def visit(fid):
            for dep in facts[fid].dependencies:
                if dep not in ancestors:ancestors.add(dep);visit(dep)
        visit(target.id);texts={facts[fid].raw.strip() for fid in ancestors}
        self.assertTrue({'Total Revenues','Group retirement products','2007','(in millions)','## Table 0 ##'}<=texts)
        changed=dict(raw,qa={'question':raw['qa']['question'],'answer':'POISON','table_evidence':['POISON']},table_description='POISON')
        self.assertEqual(canonical(asdict(ex)),canonical(asdict(multi(changed,'dev',str(DEV),0)[0])))
        self.assertEqual(len(ex.document['table_text_links']),len(raw['tables']))
    def test_real_cell_descriptions_resolve_through_geometry(self):
        found=False
        for i,raw in enumerate(self.rows):
            ex,_=multi(raw,'dev',str(DEV),i)
            for cid in raw['table_description']:
                if cid in ex.document['cell_aliases'] and ex.document['cell_aliases'][cid]!=cid:
                    found=True;anchor=ex.document['cell_aliases'][cid]
                    self.assertTrue(any(f.source.get('cell_id')==anchor for f in ex.facts));break
            if found:break
        self.assertTrue(found,'Expected real merged-cell coordinate regression')
    def test_official_numeric_output_and_mixed_scoring(self):
        # This is an evaluator contract with a real numeric span reference, not inference.
        raw=next(r for r in self.rows if r['qa']['question_type']=='span_selection' and r['qa']['answer'].isdigit())
        answer=raw['qa']['answer'];n=int(answer)
        result={'status':'ok','answer':answer,'tokens':['subtract(',str(n+1),'1',')','EOF']}
        self.assertIsInstance(convert_output('multihiertt',raw['uid'],result)['predicted_ans'],float)
        ex=PredictionExample('multihiertt','contract','dev',raw['uid'],raw['qa']['question'],{},())
        with tempfile.TemporaryDirectory() as tmp:
            score=official_score('multihiertt',[ex],[ReferenceRecord(ex.id,raw['qa'])],{ex.id:result},tmp,ROOT.parent)
            self.assertEqual(score['metrics']['em'],1)
    @unittest.skipUnless((ROOT.parent/'MultiHiertt_data/multihiertt_data/train.json').exists(),'Real train split absent')
    def test_real_section_unit_cycle_regression(self):
        rows=json.loads((ROOT.parent/'MultiHiertt_data/multihiertt_data/train.json').read_text())
        row=next(r for r in rows if r['uid']=='c828c7a59c2840a6a5927228bc746f8f')
        ex,_=multi(row,'train','real-train',0);check_example(ex)
        facts={f.id:f for f in ex.facts}
        copper=next(f for f in ex.facts if f.source.get('cell_id')=='2-8-1')
        units={facts[d].raw for d in copper.dependencies if 'in millions' in facts[d].raw or 'in thousands' in facts[d].raw}
        self.assertIn('(pounds in millions)',units);self.assertNotIn('(ounces in thousands)',units)
