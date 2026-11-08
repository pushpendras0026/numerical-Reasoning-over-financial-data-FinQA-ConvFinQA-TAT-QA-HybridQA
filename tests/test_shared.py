import copy
import json
from dataclasses import asdict,replace
from pathlib import Path
import tempfile
import unittest
from nrqa.datasets import read,hybrid,multi,tat,conversation
from nrqa.core import canonical,pack_method,EvidenceFact,PredictionExample
from nrqa.model import parse_and_execute
from nrqa.scoring import official_score

ROOT=Path(__file__).resolve().parents[1]

class Readers(unittest.TestCase):
    def test_all_readers_and_label_mutation(self):
        for name in ('tatqa','tathqa','convfinqa','hybridqa','multihiertt'):
            path=ROOT/'tests/fixtures'/f'{name}.json';raw=json.loads(path.read_text())
            before=list(read(name,path,'train',ROOT/'tests/fixtures/corpus'))
            changed=copy.deepcopy(raw)
            for row in changed:
                if name in ('tatqa','tathqa'):
                    row['questions']=[{k:v for k,v in q.items() if k in ('question','uid','order')}|{'answer':'POISON','facts':'POISON','rel_question':'POISON','question_if_part':'POISON'} for q in row['questions']]
                elif name=='convfinqa':row['annotation']={'dialogue_break':row['annotation']['dialogue_break']};row['qa']={'question':'POISON','program':'POISON'}
                elif name=='hybridqa':row['answer-text']='POISON';row['answer-node']='POISON'
                else:row['qa']={'question':row['qa']['question'],'program':'POISON','answer':'POISON'};row['table_description']='POISON'
            with tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'mutated.json';target.write_text(canonical(changed));after=list(read(name,target,'train',ROOT/'tests/fixtures/corpus'))
                # source paths differ; compare identical paths via conversion functions instead.
                for (a,_),(b,_) in zip(before,after):
                    fa=[replace(f,source={k:v for k,v in f.source.items() if k!='file'}) for f in a.facts]
                    fb=[replace(f,source={k:v for k,v in f.source.items() if k!='file'}) for f in b.facts]
                    self.assertEqual(replace(a,facts=tuple(fa)),replace(b,facts=tuple(fb)),name)
                    self.assertNotIn('POISON',canonical(asdict(b)),name)
                    ids={f.id for f in b.facts}
                    self.assertTrue(all(set(f.dependencies)<=ids for f in b.facts))
                    for method in ('ordinary','dependency','length_matched'):
                        packed=pack_method(b,method,1200);self.assertLessEqual(packed['token_count'],1200)
                        if method=='length_matched':self.assertGreaterEqual(packed['matching_gap'],0)
    def test_no_future_questions_and_link_closure(self):
        raw=json.loads((ROOT/'tests/fixtures/convfinqa.json').read_text())[0]
        before=list(conversation(raw,'train','fixed',0));raw['annotation']['dialogue_break'][-1]='FUTURE_POISON'
        after=list(conversation(raw,'train','fixed',0))
        self.assertEqual(before[0][0],after[0][0]);self.assertNotIn('FUTURE_POISON',canonical(asdict(after[0][0])))
        row=json.loads((ROOT/'tests/fixtures/hybridqa.json').read_text())[0]
        ex=hybrid(row,'train','fixed',0,ROOT/'tests/fixtures/corpus')[0]
        link=next(f for f in ex.facts if 'link' in f.source)
        from nrqa.core import pack
        bundle=pack(ex,[link.id],10000,True);ids={f['id'] for f in bundle['facts']}
        self.assertTrue(set(link.dependencies)<=ids)
        with self.assertRaises(FileNotFoundError):hybrid(row,'train','fixed',0,None)
    def test_html_geometry_and_ancestors(self):
        raw=json.loads((ROOT/'tests/fixtures/multihiertt.json').read_text())[0];ex=multi(raw,'dev','fixture',0)[0]
        target=next(f for f in ex.facts if f.raw=='15')
        deps={f.id:f.raw for f in ex.facts}
        self.assertTrue({'Revenue','2021','North'} <= {deps[d] for d in target.dependencies})
        self.assertEqual(ex.document['geometry'][0][0]['rowspan'],2)
        self.assertNotIn('DO NOT USE',canonical(asdict(ex)))

class Tools(unittest.TestCase):
    def bundle(self):return {'question':'If revenue increases by 10%, what is revenue?', 'facts':[
        {'id':'a','raw':'100','unit':'USD'}, {'id':'b','raw':'20','unit':'USD'},
        {'id':'name','raw':'North','unit':'unknown'}]}
    def a(self,id='a',end=3):return {'fact':id,'start':0,'end':end}
    def runplan(self,plan):return parse_and_execute(canonical(plan),self.bundle())[1]
    def test_modes_units_and_invalid_shapes(self):
        a,b=self.a(),self.a('b',2)
        self.assertEqual(self.runplan({'kind':'aggregate','op':'mean','operands':[a,b]})['answer'],'60')
        self.assertEqual(self.runplan({'kind':'count','operands':[a,b]})['answer'],'2')
        self.assertEqual(self.runplan({'kind':'count','operands':[a,a]})['status'],'invalid')
        self.assertEqual(self.runplan({'kind':'extract','operand':self.a('name',5)})['answer'],'North')
        self.assertEqual(self.runplan({'kind':'multi_extract','operands':[self.a('name',5)]})['answer'],['North'])
        self.assertEqual(self.runplan({'kind':'select','mode':'max','values':[a,b],'labels':[self.a('name',5),b]})['answer'],'North')
        for bad in [{'kind':'extract','operand':dict(a,start=True)}, {'kind':'aggregate','op':'sum','operands':[]},
                    {'kind':'count','operands':[a],'answer':2}, {'kind':'arithmetic','steps':[{'op':'exec','args':[a,b]}]}]:
            self.assertEqual(self.runplan(bad)['status'],'invalid')
    def test_overlay_question_grounding(self):
        q=self.bundle()['question'];start=q.index('10%')
        change={'target':self.a(),'condition':{'fact':'__question__','start':0,'end':len(q)},
                'amount':{'fact':'__question__','start':start,'end':start+3},'op':'percent_change'}
        plan={'kind':'arithmetic','changes':[change],'steps':[{'op':'add','args':[self.a(),self.a('b',2)]}]}
        self.assertEqual(self.runplan(plan)['answer'],'130.0')
        change['condition']['fact']='name';self.assertEqual(self.runplan(plan)['status'],'invalid')
    def test_cumulative_predicted_programs(self):
        from nrqa.execute import execute
        evidence={'facts':[{'id':'prior','raw':'5','kind':'history','unit':'unknown','source':{'program_tokens':['subtract(','10','5',')','EOF']}}]}
        p={'kind':'arithmetic','steps':[{'op':'divide','args':[{'fact':'prior','start':0,'end':1},{'constant':'100'}]}]}
        result=execute(p,evidence)
        self.assertEqual(result['tokens'],['subtract(','10','5',')','divide(','#0','const_100',')','EOF'])

class OfficialContracts(unittest.TestCase):
    def test_six_official_scorers_and_failures(self):
        from nrqa.core import ReferenceRecord
        cases={
          'finqa':({'program':'subtract(15, 3)','exe_ans':12},{'status':'ok','answer':'12','tokens':['subtract(','15','3',')','EOF']}),
          'convfinqa':({'program':'15','exe_ans':15},{'status':'ok','answer':'15','tokens':None}),
          'tatqa':({'answer':'0','answer_type':'arithmetic','scale':'','derivation':'1-1','answer_from':'table'},{'status':'ok','answer':'0','scale':''}),
          'tathqa':({'answer':'0','answer_type':'arithmetic','scale':''},{'status':'ok','answer':'0','scale':''}),
          'hybridqa':({'answer':'Ghurids'},{'status':'ok','answer':'Ghurids'}),
          'multihiertt':({'answer':12,'program':'subtract(15, 3)'},{'status':'ok','answer':'12','tokens':['subtract(','15','3',')','EOF']})}
        for name,(labels,result) in cases.items():
            ex=PredictionExample(name,'fixture','train','fixture','q',{'table':[]},())
            with tempfile.TemporaryDirectory() as tmp:
                scores=official_score(name,[ex],[ReferenceRecord('fixture',labels)],{'fixture':result},tmp,ROOT/'third_party')
                metric='execution' if name in ('finqa','convfinqa') else 'em'
                self.assertEqual(scores['metrics'][metric],1,name)
                scores=official_score(name,[ex],[ReferenceRecord('fixture',labels)],{'fixture':{'status':'abstain'}},tmp,ROOT/'third_party')
                self.assertEqual(scores['metrics'][metric],0,name)
                self.assertEqual(scores['denominator'],1)

class Boundaries(unittest.TestCase):
    def test_negative_hypothetical_and_partial_numbers(self):
        q='If revenue decreases by 10%, what remains?'
        b={'question':q,'facts':[{'id':'x','raw':'100','unit':'USD'}]};target={'fact':'x','start':0,'end':3};start=q.index('10%')
        plan={'kind':'extract','operand':target,'changes':[{'target':target,'condition':{'fact':'__question__','start':0,'end':len(q)},
                    'amount':{'fact':'__question__','start':start,'end':start+3},'op':'percent_decrease'}]}
        self.assertEqual(parse_and_execute(canonical(plan),b)[1]['answer'],'90.0')
        partial={'kind':'arithmetic','steps':[{'op':'add','args':[dict(target,start=1),{'constant':'1'}]}]}
        self.assertEqual(parse_and_execute(canonical(partial),b)[1]['status'],'invalid')
    def test_history_inline_question_number_cannot_replace_prediction(self):
        from nrqa.execute import execute
        f={'id':'history','raw':'In 2019? | 5','kind':'history','unit':'unknown','source':{'predicted_value':'5','program_tokens':['subtract(','10','5',')','EOF']}}
        p={'kind':'arithmetic','steps':[{'op':'add','args':[{'fact':'history','start':3,'end':7},{'constant':'1'}]}]}
        self.assertEqual(execute(p,{'facts':[f]})['status'],'invalid')
        p['steps'][0]['args'][0]={'fact':'history','start':11,'end':12}
        self.assertEqual(execute(p,{'facts':[f]})['answer'],'6')
    def test_hidden_labels_still_export_complete_submission(self):
        from nrqa.core import ReferenceRecord
        ex=PredictionExample('convfinqa','fixture','test','conversation_0','q',{'table':[]},())
        with tempfile.TemporaryDirectory() as tmp:
            score=official_score('convfinqa',[ex],[ReferenceRecord(ex.id,{})],{ex.id:{'status':'ok','answer':'5','tokens':None}},tmp,ROOT/'third_party')
            self.assertEqual(score['status'],'hidden_labels');self.assertTrue(score['submission_exported'])
            self.assertEqual(json.loads((Path(tmp)/'official_predictions.json').read_text()),[{'id':ex.id,'predicted':['5','EOF']}])
    def test_complete_table_row_official_export_and_partial_rejection(self):
        from nrqa.finqa import convert
        from nrqa.core import pack
        raw={'id':'fixture','filename':'fixture.pdf','table':[['Metric','2020','2021'],['Revenue','10','15']],
             'pre_text':[],'post_text':[],'qa':{'question':'What is total revenue?'}}
        example=convert(raw,'train','fixture',0)[0]
        for dependent in (False,True):
            bundle=pack(example,[f.id for f in example.facts if f.kind=='cell'],10000,dependent)
            cells=[f for f in bundle['facts'] if f['kind']=='cell'];first=cells[0]
            row_text=first['raw'];start=row_text.index('Revenue') if not dependent else 0
            if dependent:
                header=next(f for f in bundle['facts'] if f['raw']=='Revenue');row={'fact':header['id'],'start':0,'end':7}
            else:row={'fact':first['id'],'start':start,'end':start+7}
            spans=[]
            for cell in cells:
                value=cell['source']['cell_raw'];start=cell['raw'].rindex(value);spans.append({'fact':cell['id'],'start':start,'end':start+len(value)})
            plan={'kind':'table_aggregate','op':'sum','row':row,'operands':spans}
            result=parse_and_execute(canonical(plan),bundle)[1]
            self.assertEqual(result['answer'],'25');self.assertEqual(result['tokens'],['table_sum(','Revenue','none',')','EOF'])
            from nrqa.evaluation import load_official
            official=load_official(ROOT/'third_party/FinQA/code/evaluate/evaluate.py')
            self.assertEqual(official.eval_program(result['tokens'],raw['table']),(0,25.))
            plan['operands']=spans[:1];self.assertEqual(parse_and_execute(canonical(plan),bundle)[1]['status'],'invalid')
    def test_oversized_history_program_is_rejected(self):
        from nrqa.execute import execute
        f={'id':'h','raw':'1','kind':'history','source':{'program_tokens':['add(','1','1',')']*257+['EOF']}}
        p={'kind':'arithmetic','steps':[{'op':'add','args':[{'fact':'h','start':0,'end':1},{'constant':'1'}]}]}
        self.assertEqual(execute(p,{'facts':[f]})['status'],'invalid')
