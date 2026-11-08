"""Bounded, source-grounded answer interpreter. No eval, generated code or imports."""
import re
from decimal import Decimal, DecimalException, localcontext

NUMBER=re.compile(r'[-+]?\d[\d,]*(?:\.\d+)?\s*%?')
# Constant names accepted by the official FinQA/ConvFinQA program language.
CONSTANTS={s:Decimal(s) for s in ('1','2','3','4','5','6','7','10','12','100','1000','10000','100000','1000000')}
CONSTANTS['m1']=Decimal(-1)
SCALES={'','thousand','million','billion','percent','percent_fraction'}
OPS={'add','subtract','multiply','divide','greater','less','equal','exp','min','max'}


def number(text):
    text=text.strip().replace('$','').replace(',','').strip()
    if text.startswith('(') and text.endswith(')'):text='-'+text[1:-1].strip()
    percent=text.endswith('%');value=Decimal(text.rstrip('%').strip())
    if not value.is_finite() or abs(value)>Decimal('1e100'):raise ValueError('Nonfinite or oversized value')
    return value/100 if percent else value


def execute(plan,evidence):
    facts={f['id']:f for f in evidence['facts']};results=[];tokens=[];trace=[];overrides={};history_offsets={}
    def span(arg):
        if not isinstance(arg,dict) or set(arg)!={'fact','start','end'}:raise ValueError('Invalid span shape')
        f=facts[arg['fact']];a,b=arg['start'],arg['end']
        if type(a) is not int or type(b) is not int or not 0<=a<b<=len(f['raw']):raise ValueError('Invalid span')
        return f,f['raw'][a:b]
    def resolve(arg):
        if not isinstance(arg,dict):raise ValueError('Invalid operand')
        if set(arg)=={'step'}:
            i=arg['step']
            if type(i)is not int or not 0<=i<len(results):raise ValueError('Invalid prior step')
            v,t,u=results[i];return v,t,u
        if set(arg)=={'constant'}:return CONSTANTS[arg['constant']],'const_'+arg['constant'],'constant'
        f,raw=span(arg);key=(arg['fact'],arg['start'],arg['end'])
        a,b=arg['start'],arg['end']
        raw_text=f['raw']
        # A '.' or ',' only continues a number when a digit sits on its far side;
        # sentence punctuation ("was 123.") must not reject a complete literal.
        before=a>0 and (raw_text[a-1].isdigit() or (raw_text[a-1] in '.,' and a>1 and raw_text[a-2].isdigit()))
        after=b<len(raw_text) and (raw_text[b] in '0123456789%' or (raw_text[b] in '.,' and b+1<len(raw_text) and raw_text[b+1].isdigit()))
        if before or after:
            raise ValueError('Partial numeric literal')
        value=overrides.get(key,number(raw));symbol=raw.replace(',','').replace('$','').replace(' ','').strip()
        if '(' in symbol or ')' in symbol:symbol=str(number(raw))
        if key in overrides:symbol=str(value) # overlay has no official program equivalence guarantee
        if f.get('kind')=='history':
            predicted=f.get('source',{}).get('predicted_value',f['raw'])
            if raw!=predicted or arg['end']!=len(f['raw']):raise ValueError('History operand must be the complete prior prediction')
            prior=f.get('source',{}).get('program_tokens')
            if prior and len(prior)>2:
                if f['id'] not in history_offsets:
                    if len(tokens)+len(prior)-1>1024:raise ValueError('Cumulative program exceeds 256 operations')
                    offset=len(tokens)//4
                    for t in prior[:-1]:tokens.append('#'+str(int(t[1:])+offset) if t.startswith('#') else t)
                    history_offsets[f['id']]=len(tokens)//4-1
                symbol='#'+str(history_offsets[f['id']])
        return value,symbol,f.get('unit','unknown')
    def emit(op,args):
        a,at,au=resolve(args[0]);b,bt,bu=resolve(args[1])
        if isinstance(a,str) or isinstance(b,str):raise ValueError('Numeric operands required')
        if op in ('add','subtract','greater','less','equal','min','max') and au!=bu and not {'unknown','derived','constant'}&{au,bu}:raise ValueError('Unit mismatch')
        if op=='add':value=a+b
        elif op=='subtract':value=a-b
        elif op=='multiply':value=a*b
        elif op=='divide':value=a/b
        elif op=='exp' and b==int(b) and abs(b)<=10:value=a**int(b)
        elif op=='greater':value='yes' if a>b else 'no'
        elif op=='less':value='yes' if a<b else 'no'
        elif op=='equal':value='yes' if a==b else 'no'
        elif op=='min':value=min(a,b)
        elif op=='max':value=max(a,b)
        else:raise ValueError('Unsupported operation or exponent')
        if isinstance(value,Decimal) and (not value.is_finite() or abs(value)>Decimal('1e100')):raise ValueError('Result exceeds bounds')
        if len(tokens)>=1024:raise ValueError('Cumulative program exceeds 256 operations')
        index=len(tokens)//4;tokens.extend([op+'(',at,bt,')']);results.append((value,'#'+str(index),'derived'))
        trace.append({'op':op,'args':args,'result':str(value),'unknown_unit':'unknown' in (au,bu)})
    try:
        kind=plan['kind'];scale=plan.get('scale','')
        if scale not in SCALES:raise ValueError('Unsupported answer scale')
        if kind=='abstain':return {'status':'abstain','tokens':['EOF']}
        if kind=='table_aggregate':
            if plan.get('changes'):raise ValueError('Whole-row export does not support overlays')
            from .table_ops import table_aggregate
            return table_aggregate(plan,evidence)
        with localcontext() as ctx:
            ctx.prec=28
            for change in plan.get('changes',[]):
                target=change['target'];span(target);amount=resolve(change['amount'])[0];old=resolve(target)[0]
                # The operation and amount must be grounded in the question itself.
                condition,_=span(change['condition'])
                if condition.get('kind')!='question' or change['amount'].get('fact')!=condition['id']:raise ValueError('Ungrounded hypothetical condition')
                if not change['condition']['start']<=change['amount']['start']<change['amount']['end']<=change['condition']['end']:raise ValueError('Amount outside hypothetical clause')
                op=change['op']
                value={'replace':lambda:amount,'add':lambda:old+amount,'subtract':lambda:old-amount,
                       'multiply':lambda:old*amount,'percent_change':lambda:old*(1+amount),'percent_increase':lambda:old*(1+amount),'percent_decrease':lambda:old*(1-amount)}[op]()
                if not value.is_finite() or abs(value)>Decimal('1e100'):raise ValueError('Overlay exceeds bounds')
                overrides[target['fact'],target['start'],target['end']]=value
                trace.append({'intervention':change,'before':str(old),'after':str(value)})
            if kind=='extract':
                f,answer=span(plan['operand']);outtokens=None
                target=plan['operand'];answer=str(overrides.get((target['fact'],target['start'],target['end']),answer))
                if f.get('kind')=='history' and answer==f.get('source',{}).get('predicted_value',f['raw']) and plan['operand']['end']==len(f['raw']):outtokens=f.get('source',{}).get('program_tokens')
                return {'status':'ok','answer':answer,'scale':scale,'tokens':outtokens,'trace':trace+[plan['operand']]}
            if kind in ('multi_extract','count'):
                spans=plan['operands'];keys=[(a['fact'],a['start'],a['end']) for a in spans]
                if len(set(keys))!=len(keys):raise ValueError('Duplicate counted/extracted span')
                answers=[str(overrides.get((a['fact'],a['start'],a['end']),span(a)[1])) for a in spans]
                return {'status':'ok','answer':str(len(answers)) if kind=='count' else answers,'scale':scale,'tokens':None,'trace':trace+spans}
            if kind=='select':
                values=[resolve(a)[0] for a in plan['values']]
                if any(isinstance(v,str) for v in values):raise ValueError('Invalid comparison value')
                best=(max if plan['mode']=='max' else min)(values)
                # First tie, explicitly deterministic.
                answer=span(plan['labels'][values.index(best)])[1]
                return {'status':'ok','answer':answer,'scale':scale,'tokens':None,'trace':trace}
            if kind=='aggregate':
                args=plan['operands'];op=plan['op'];values=[resolve(a)[0] for a in args]
                if not values:raise ValueError('Empty aggregate')
                units={resolve(a)[2] for a in args}-{'unknown','derived'}
                if len(units)>1:raise ValueError('Unit mismatch')
                if op in ('sum','mean') and len(args)>1:
                    emit('add',args[:2])
                    for arg in args[2:]:emit('add',[{'step':len(results)-1},arg])
                    if op=='mean':
                        # Derived count is grounded in the validated operand list.
                        value=results[-1][0]/len(args);index=len(tokens)//4
                        tokens.extend(['divide(',results[-1][1],'const_'+str(len(args)),')'])
                        results.append((value,'#'+str(index),'derived'))
                    value=results[-1][0]
                    if abs(value)>Decimal('1e100'):raise ValueError('Aggregate exceeds bounds')
                    return {'status':'ok','answer':str(value),'scale':scale,'tokens':tokens+['EOF'] if not overrides else None,'trace':trace}
                if op=='mean':value=sum(values)/len(values)
                elif op=='sum':value=sum(values)
                elif op=='min':value=min(values)
                elif op=='max':value=max(values)
                else:raise ValueError('Unsupported aggregate')
                if abs(value)>Decimal('1e100'):raise ValueError('Aggregate exceeds bounds')
                return {'status':'ok','answer':str(value),'scale':scale,'tokens':None,'trace':trace+[{'aggregate':op,'operands':args}]}
            if kind!='arithmetic' or not 1<=len(plan['steps'])<=32:raise ValueError('Invalid plan')
            for step in plan['steps']:
                if len(step['args'])!=2:raise ValueError('Invalid operands')
                emit(step['op'],step['args'])
        exportable=all(t.rstrip('(') not in ('less','equal','min','max') for t in tokens[::4]) and not overrides
        return {'status':'ok','answer':str(results[-1][0]),'scale':scale,'tokens':tokens+['EOF'] if exportable else None,'trace':trace}
    except (KeyError,ValueError,TypeError,IndexError,DecimalException,OverflowError) as error:
        return {'status':'invalid','error':str(error),'tokens':['EOF'],'trace':trace}
