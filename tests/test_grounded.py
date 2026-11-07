import unittest,json
from nrqa.grounded import parse,request
class GroundedTests(unittest.TestCase):
 def setUp(self):
  self.p={'question':'What is percentage growth?','facts':[{'id':'long:id:a','raw':'80','unit':'unknown'},{'id':'long:id:b','raw':'100','unit':'unknown'}]}
 def test_multistep(self):
  plan={'kind':'arithmetic','scale':'percent','steps':[{'op':'subtract','args':[{'fact':'f1','text':'100'},{'fact':'f0','text':'80'}]},{'op':'divide','args':[{'step':0},{'fact':'f0','text':'80'}]},{'op':'multiply','args':[{'step':1},{'constant':'100'}]}]}
  _,r=parse(json.dumps(plan),self.p)
  self.assertEqual(r['status'],'ok');self.assertEqual(float(r['answer']),25)
  self.assertEqual(r['tokens'][-5:],['multiply(','#1','const_100',')','EOF'])
 def test_invented_quote(self):
  _,r=parse(json.dumps({'kind':'extract','operand':{'fact':'f0','text':'90'},'scale':''}),self.p)
  self.assertEqual(r['status'],'invalid')
 def test_partial_number(self):
  _,r=parse(json.dumps({'kind':'arithmetic','steps':[{'op':'add','args':[{'fact':'f0','text':'8'},{'constant':'1'}]}],'scale':''}),self.p)
  self.assertEqual(r['status'],'invalid')
 def test_ambiguous_quote(self):
  self.p['facts'][0]['raw']='80 and 80'
  _,r=parse(json.dumps({'kind':'extract','operand':{'fact':'f0','text':'80'},'scale':''}),self.p)
  self.assertEqual(r['status'],'invalid')
 def test_request_no_labels(self):
  self.p['gold_answer']='secret'
  r=request(self.p['question'],self.p,{},{});self.assertNotIn('secret',json.dumps(r));self.assertEqual(r['input']['evidence'][0]['id'],'f0')
if __name__=='__main__':unittest.main()
