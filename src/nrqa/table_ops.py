"""Whole-row aggregate contract: all numeric cells must be selected and grounded."""
from decimal import Decimal
from .execute import number


def table_aggregate(plan,evidence):
    facts={f['id']:f for f in evidence['facts']}
    def span(arg):
        f=facts[arg['fact']];a,b=arg['start'],arg['end']
        if type(a)is not int or type(b)is not int or not 0<=a<b<=len(f['raw']):raise ValueError('Invalid row span')
        return f,f['raw'][a:b]
    header,label=span(plan['row']);source=header.get('source',{})
    if not source.get('row_label') or label!=source['row_label']:raise ValueError('Row label must match supplied table')
    width=source['row_width'];values=[];columns=[]
    if type(width)is not int or width<2:raise ValueError('Numeric row required')
    for arg in plan['operands']:
        f,raw=span(arg);s=f.get('source',{})
        if any(s.get(k)!=source.get(k) for k in ('document','table','row','field','row_width','row_label')):raise ValueError('Mixed table rows')
        c=s['column']
        if not 1<=c<width:raise ValueError('Invalid numeric column')
        # Match the upstream row parser's removal of parenthetical annotations.
        original=s['cell_raw'].replace('$','').strip().split('(')[0].strip()
        value=number(raw)
        if value!=number(original):raise ValueError('Selected span does not represent original table value')
        columns.append(c);values.append(value)
    if sorted(columns)!=list(range(1,width)):raise ValueError('Complete row required; missing or repeated cell')
    op=plan['op']
    if op=='sum':value=sum(values)
    elif op=='mean':value=sum(values)/len(values)
    elif op=='min':value=min(values)
    elif op=='max':value=max(values)
    else:raise ValueError('Unsupported row aggregate')
    if not value.is_finite() or abs(value)>Decimal('1e100'):raise ValueError('Aggregate exceeds bounds')
    operator={'sum':'table_sum','mean':'table_average','min':'table_min','max':'table_max'}[op]
    return {'status':'ok','answer':str(value),'scale':plan.get('scale',''),
            'tokens':[operator+'(',label,'none',')','EOF'],
            'trace':[{'row':plan['row'],'operands':plan['operands'],'complete_columns':columns,'operation':operator}]}
