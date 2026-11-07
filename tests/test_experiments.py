import copy
import json
from pathlib import Path
import tempfile
import unittest
from nrqa.experiment import freeze,run,evaluate,ROOT
from nrqa.preparation import prepare

class ExperimentContract(unittest.TestCase):
    def test_freeze_three_methods_mock_resume_full_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);frozen=tmp/'frozen.json';out=tmp/'mock'
            freeze(ROOT/'experiments/smoke.json',frozen)
            first=run(frozen,out,'mock');second=run(frozen,out,'mock')
            self.assertEqual(first['completed_requests'],9);self.assertEqual(second['new_calls'],0);self.assertEqual(second['cache_hits'],9)
            self.assertEqual(first['successful_requests'],9);self.assertEqual(first['failed_requests'],0);self.assertEqual(first['uncertain_requests'],0)
            metrics=evaluate(frozen,out)
            for score in metrics.values():
                self.assertEqual(score['denominator'],3);self.assertEqual(score['counts'],{'abstain':3});self.assertEqual(score['metrics']['execution'],0)
            rows=json.loads((out/'results.json').read_text());rows.pop();(out/'results.json').write_text(json.dumps(rows))
            metrics=evaluate(frozen,out);self.assertEqual(metrics['length_matched']['counts'],{'abstain':2,'missing':1})
            with self.assertRaises(ValueError):run(frozen,out,'prepare')
    def test_python_preparation_edges_and_no_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=prepare([ROOT/'experiments/tatqa_pilot.json',ROOT/'experiments/tathqa_pilot.json'],tmp,2)
            self.assertEqual(result['joined_count'],4);self.assertEqual(result['unresolved_edges'],0)
            for path in Path(tmp).glob('*.jsonl'):
                self.assertNotIn('"answer"',path.read_text());self.assertNotIn('"program"',path.read_text())
    def test_freeze_refuses_partial_conversations_and_invalid_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);config=json.loads((ROOT/'experiments/convfinqa_pilot.json').read_text())
            from nrqa.experiment import load_examples
            example=load_examples(config)[0][0];config['ids']=[example.id]
            path=tmp/'config.json';path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'complete conversations'):freeze(path,tmp/'frozen.json')
            config=json.loads((ROOT/'experiments/smoke.json').read_text());config['spending_ceiling_usd']=1;path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'zero-spend'):freeze(path,tmp/'frozen.json')
    def test_direct_diagnostic_and_disabled_overlay(self):
        from nrqa.experiment import Mock
        class DirectMock(Mock):
            def generate(self,request):return {'model':'abstention-fixture','text':json.dumps({'kind':'direct','answer':'10','scale':''})}
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);config=json.loads((ROOT/'experiments/smoke.json').read_text());config['answering']='direct'
            path=tmp/'config.json';path.write_text(json.dumps(config));frozen=tmp/'frozen.json';freeze(path,frozen)
            run(frozen,tmp/'run','mock',DirectMock)
            metrics=evaluate(frozen,tmp/'run')
            self.assertEqual(set(metrics['ordinary']['metrics']),{'direct_numeric_auxiliary'})
    def test_model_pins_survive_preflight_stop(self):
        from nrqa.experiment import Mock
        from nrqa.providers import ProviderError
        class Blocked(Mock):
            def verify_free(self):raise ProviderError('quota_exhausted')
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);frozen=tmp/'frozen.json';out=tmp/'run';freeze(ROOT/'experiments/smoke.json',frozen)
            first=run(frozen,out,'mock');blocked=run(frozen,out,'mock',Blocked)
            self.assertEqual(first['identity'],blocked['identity']);self.assertEqual(first['resolved_models'],blocked['resolved_models'])
            self.assertEqual((blocked['successful_requests'],blocked['failed_requests'],blocked['uncertain_requests']),(0,0,0))
            resumed=run(frozen,out,'mock');self.assertEqual(resumed['new_calls'],0)
    def test_repeated_contexts_are_not_new_documents(self):
        import copy
        source=json.loads((ROOT.parent/'FinQA/dataset/train.json').read_text())[0]
        second=copy.deepcopy(source);second['id']='same-context-new-question';second['qa']['question']='Another question about this context?'
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);data=tmp/'data.json';data.write_text(json.dumps([source,second]))
            config=tmp/'config.json';config.write_text(json.dumps({'dataset':'finqa','split':'fixture','source':str(data)}))
            output=tmp/'prepared';prepare([config],output)
            manifest=json.loads((output/'source_manifest.json').read_text())
            self.assertEqual(manifest['questions'],2);self.assertEqual(manifest['documents'],1)
            rows=[json.loads(x) for x in (output/'facts.jsonl').read_text().splitlines()]
            self.assertTrue(all(len(row['source_ids'])==2 for row in rows))
