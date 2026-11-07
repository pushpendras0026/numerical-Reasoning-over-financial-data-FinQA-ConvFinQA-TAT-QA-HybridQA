"""Prediction-only adapters. References are returned separately, never indexed."""
from dataclasses import replace
from pathlib import Path
import json
import re
import zipfile
from html.parser import HTMLParser
from .core import EvidenceFact as Fact, PredictionExample as Example, ReferenceRecord
from .finqa import convert as finqa
from .execute import number

VERSIONS = {'finqa':'0f16e2867befa6840783e58be38c9efb9229d742',
 'tatqa':'870accc41953dcde885aabeb963d94aabdc0fbc3',
 'convfinqa':'cf3eed2d5984960bf06bb8145bcea5e80b0222a6',
 'hybridqa':'db22fda8c5951438fade3c69d75b350335ba93b3',
 'tathqa':'8b821d89f0fbfeceea07e4f5faf46b33150fee07',
 'multihiertt':'45bd9ccdf3142ea059bd5e69c0afb83437fa539c'}


def grid_facts(prefix, grid, source, table_id='0'):
    """First row/column plus preceding section rows; all inferred, flagged uncertain."""
    facts, section = [], None
    def fid(r,c): return f'{prefix}:table:{table_id}:{r}:{c}'
    for r,row in enumerate(grid):
        is_section = r > 0 and bool(row) and bool(str(row[0]).strip()) and all(not str(x).strip() for x in row[1:])
        if is_section: section = fid(r,0)
        for c,value in enumerate(row):
            deps = []
            if r > 0 and c > 0:
                if c < len(grid[0]): deps.append(fid(0,c))
                deps.append(fid(r,0))
                if grid[0] and grid[0][0]: deps.append(fid(0,0))
                if section: deps.append(section)
            facts.append(Fact(fid(r,c),str(value),dict(source,table=table_id,row=r,column=c,row_width=len(row),row_label=str(row[0]) if row else '',cell_raw=str(value)),
                              tuple(dict.fromkeys(deps)), 'header' if r == 0 or c == 0 or is_section else 'cell',
                              'USD' if '$' in str(value) else 'unknown',True))
    return facts


def paragraphs(prefix, values, source):
    result=[]
    for i,p in enumerate(values):
        text = p['text'] if isinstance(p,dict) else p
        pid = str(p.get('uid',i)) if isinstance(p,dict) else str(i)
        result.append(Fact(f'{prefix}:paragraph:{pid}',text,dict(source,paragraph=pid,order=p.get('order',i) if isinstance(p,dict) else i,start=0,end=len(text))))
    return result


def unit_dependencies(facts):
    units=tuple(f.id for f in facts if f.kind=='text' and re.search(r'\bin (?:thousands|millions|billions)|amounts in|dollars in',f.raw,re.I))
    return [replace(f,dependencies=tuple(dict.fromkeys(f.dependencies+units))) if f.kind=='cell' else f for f in facts]


def tat(raw, dataset, split, source, index):
    table=raw['table']; prefix=f"{dataset}:{split}:{table['uid']}"
    base={'file':source,'record_index':index,'document':table['uid']}
    facts=unit_dependencies(grid_facts(prefix,table['table'],base)+paragraphs(prefix,raw['paragraphs'],base))
    doc={'id':table['uid'],'tables':[table['table']], 'paragraphs':[{k:p[k] for k in ('uid','order','text') if k in p} for p in raw['paragraphs']],
         'hierarchy':'inferred section rows; uncertain'}
    for q in raw['questions']:
        yield Example(dataset,VERSIONS[dataset],split,q['uid'],q['question'],doc,tuple(facts)),ReferenceRecord(q['uid'],{k:v for k,v in q.items() if k not in ('uid','question','order')})


def conversation(raw, split, source,index):
    questions=raw['annotation']['dialogue_break']
    # Deliberately construct a fresh FinQA-shaped INPUT, never pass source qa.
    safe={k:raw[k] for k in ('id','filename','table','pre_text','post_text')}
    safe['table_ori']=raw.get('table_ori');safe['qa']={'question':''}
    base=finqa(safe,split,source,index)[0]
    ann=raw['annotation']
    for turn,q in enumerate(questions):
        qid=f"{raw['id']}_{turn}"
        doc=dict(base.document,conversation_id=raw['id'],turn=turn)
        labels={}
        if 'turn_program' in ann: labels['program']=ann['turn_program'][turn]
        if 'exe_ans_list' in ann: labels['exe_ans']=ann['exe_ans_list'][turn]
        yield replace(base,dataset='convfinqa',version=VERSIONS['convfinqa'],id=qid,question=q,
                      document=doc,earlier_questions=tuple(questions[:turn])),ReferenceRecord(qid,labels)


def hybrid(raw,split,source,index,corpus):
    if corpus is None: raise FileNotFoundError('HybridQA needs corpus/tables_tok and corpus/request_tok; see docs/acquisition.md')
    tid=raw['table_id'];root=Path(corpus)
    table=json.loads((root/'tables_tok'/f'{tid}.json').read_text())
    requests=json.loads((root/'request_tok'/f'{tid}.json').read_text())
    prefix=f'hybridqa:{split}:{tid}';base={'file':source,'record_index':index,'document':tid}
    grid=[[h[0] for h in table['header']]]+[[c[0] for c in row] for row in table['data']]
    facts=grid_facts(prefix,grid,base)
    links=[]
    for r,row in enumerate([table['header']]+table['data']):
        for c,cell in enumerate(row):
            anchor=f'{prefix}:table:0:{r}:{c}'
            for link in cell[1]:
                if link not in requests: raise ValueError(f'Unresolved HybridQA passage: {tid} / {link}')
                text=requests[link]
                if not isinstance(text,str) or not text.strip(): raise ValueError(f'Empty or invalid HybridQA passage: {tid} / {link}')
                # Separate sentences give bounded, question-ranked passage expansion.
                for n,m in enumerate(re.finditer(r'[^.!?]+(?:[.!?]+|$)',text)):
                    pid=f'{prefix}:link:{r}:{c}:{link}:{n}'
                    facts.append(Fact(pid,m.group(),dict(base,link=link,row=r,column=c,start=m.start(),end=m.end()),(anchor,), 'text'))
                links.append({'cell':anchor,'target':link})
    # Never include arbitrary metadata from the loaded corpus.
    doc={'id':tid,'tables':[grid], 'links':links,'title':table.get('title','')}
    return Example('hybridqa',VERSIONS['hybridqa'],split,raw['question_id'],raw['question'],doc,tuple(facts)),ReferenceRecord(raw['question_id'],{'answer':raw.get('answer-text')})


class HTMLTable(HTMLParser):
    """Keep HTML cell coordinates and merged geometry; do not flatten away spans."""
    def __init__(self):
        super().__init__(convert_charrefs=True);self.cells=[];self.row=-1;self.col=0;self.cell=None;self.occupied={};self.ordinal=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='tr':self.row+=1;self.col=0;self.ordinal=0
        if tag in ('td','th'):
            while (self.row,self.col) in self.occupied:self.col+=1
            rs,cs=int(attrs.get('rowspan',1)),int(attrs.get('colspan',1))
            if not 1<=rs<=1000 or not 1<=cs<=1000:raise ValueError('Invalid HTML span')
            self.cell={'ordinal_column':self.ordinal,'links':[],'row':self.row,'column':self.col,'rowspan':rs,'colspan':cs,'tag':tag,'raw':''}
        if tag=='a' and self.cell is not None and attrs.get('href'):self.cell['links'].append(attrs['href'])
        if tag=='br' and self.cell is not None:self.cell['raw']+='\n'
    def handle_data(self,data):
        if self.cell is not None:self.cell['raw']+=data
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            cell=self.cell;self.cells.append(cell)
            for r in range(cell['row'],cell['row']+cell['rowspan']):
                for c in range(cell['column'],cell['column']+cell['colspan']):
                    if (r,c) in self.occupied:raise ValueError('Overlapping HTML cells')
                    self.occupied[r,c]=True
            self.col+=cell['colspan'];self.ordinal+=1;self.cell=None


def multi(raw,split,source,index):
    prefix=f"multihiertt:{split}:{raw['uid']}";base={'file':source,'record_index':index,'document':raw['uid']}
    if not isinstance(raw['qa']['question'],str) or not all(isinstance(x,str) for x in raw['tables']+raw['paragraphs']):
        raise ValueError('MultiHiertt expects question, HTML tables and paragraphs as strings')
    facts=[];geometries=[];aliases={};table_links=[]
    text_facts=paragraphs(prefix,raw['paragraphs'],base)
    markers={}
    for i,fact in enumerate(text_facts):
        match=re.fullmatch(r'\s*## Table (\d+) ##\s*',fact.raw)
        if match:
            ti=int(match[1])
            if ti>=len(raw['tables']):raise ValueError('Table marker has no HTML table')
            markers.setdefault(ti,[]).append(fact.id)
            # Explicit marker links the table to its position; adjacent caption is inferred.
            if i>0:text_facts[i]=replace(fact,dependencies=(text_facts[i-1].id,),structure_uncertain=True)
            table_links.append({'table':str(ti),'paragraph':fact.id,'caption':text_facts[i-1].id if i else None,'caption_inferred':bool(i)})
    def numeric(text):
        try:number(text);return True
        except Exception:return False
    unit_pattern=re.compile(r'\b(?:in|dollars in)\s+(?:thousands|millions|billions)|\$\s*in\s+',re.I)
    for ti,html in enumerate(raw['tables']):
        parser=HTMLTable();parser.feed(html);parser.close()
        if not parser.cells or parser.cell is not None:raise ValueError('Empty or unclosed HTML table')
        geometries.append(parser.cells)
        by_row={}
        for cell in parser.cells:by_row.setdefault(cell['row'],[]).append(cell)
        def fid(cell):return f"{prefix}:cell:{ti}-{cell['row']}-{cell['column']}"
        # The release uses td for every header. Infer a leading header block from
        # raw HTML only, then retain later section headings with explicit uncertainty.
        data_rows=[]
        for r,cells in by_row.items():
            if r>0 and any(c['column']==0 and c['raw'].strip() for c in cells) and any(c['column']>0 and numeric(c['raw']) for c in cells):data_rows.append(r)
        first_data=min(data_rows,default=1)
        width=max(c['column']+c['colspan'] for c in parser.cells)
        initial_sections=[]
        for r,cells in by_row.items():
            values=[c for c in cells if c['raw'].strip()]
            if 0<r<first_data and values and values[0]['column']==0 and all(c['column']==0 or unit_pattern.search(c['raw']) for c in values):initial_sections.extend(values)
        leading=[c for c in parser.cells if c['row']<first_data and c not in initial_sections and not unit_pattern.search(c['raw'])]
        explicit_headers=[c for c in parser.cells if c['tag']=='th' and c not in leading]
        unit_cells=[c for c in parser.cells if unit_pattern.search(c['raw'])]
        sections=list(initial_sections)
        for r,cells in by_row.items():
            nonempty=[c for c in cells if c['raw'].strip()]
            section_cells=nonempty if data_rows and r>=first_data and nonempty and nonempty[0]['column']==0 and r not in data_rows else []
            section=section_cells[0] if section_cells else None
            if section:
                # A year starts a new section; consecutive textual headings form a chain.
                if re.fullmatch(r'\s*(?:19|20)\d{2}\s*',section['raw']):sections=[]
                elif sections and sections[-1]['row']!=r-1:sections=[]
                sections.extend(section_cells)
            for cell in cells:
                c=cell['column'];cid=f'{ti}-{r}-{c}'
                for rr in range(r,r+cell['rowspan']):
                    for cc in range(c,c+cell['colspan']):aliases[f'{ti}-{rr}-{cc}']=cid
                deps=[]
                if r>=first_data and cell not in section_cells:
                    for header in leading:
                        if header['row']<r and header['column']<=c<header['column']+header['colspan']:deps.append(fid(header))
                    for header in cells:
                        if header['column']==0 and header['column']<c:deps.append(fid(header))
                    deps.extend(fid(h) for h in sections if h['row']<r)
                    if numeric(cell['raw']) and c>0:
                        applicable=[h for h in unit_cells if h['row']<=r and h is not cell and (h['column']==0 or h['column']<=c<h['column']+h['colspan'])]
                        latest=max((h['row'] for h in applicable),default=-1)
                        deps.extend(fid(h) for h in applicable if h['row']==latest)
                # Explicit th headers outside the inferred leading block remain available.
                deps.extend(fid(h) for h in explicit_headers if h['tag']=='th' and h['row']<r and h['column']<=c<h['column']+h['colspan'] and h not in leading)
                deps.extend(markers.get(ti,[]))
                kind='header' if cell['tag']=='th' or r<first_data or (c==0 and width>1) or cell in section_cells or cell in unit_cells else 'cell'
                facts.append(Fact(fid(cell),cell['raw'],dict(base,table=str(ti),cell_id=cid,**{k:cell[k] for k in ('row','column','rowspan','colspan','ordinal_column','links')}),
                                  tuple(dict.fromkeys(deps)),kind,'USD' if '$' in cell['raw'] else 'unknown',cell['tag']!='th'))
    facts=unit_dependencies(facts+text_facts)
    # Aliases come only from rowspan/colspan geometry, never from gold evidence or descriptions.
    doc={'id':raw['uid'],'tables_html':raw['tables'],'geometry':geometries,'paragraphs':raw['paragraphs'],
         'cell_aliases':aliases,'table_text_links':table_links,'header_inference':'leading td rows and section headings; uncertain'}
    return Example('multihiertt',VERSIONS['multihiertt'],split,raw['uid'],raw['qa']['question'],doc,tuple(facts)),ReferenceRecord(raw['uid'],{k:v for k,v in raw['qa'].items() if k!='question'})


def read(dataset,path,split,corpus=None,member=None):
    path=Path(path)
    if member:
        with zipfile.ZipFile(path) as z:rows=json.loads(z.read(member))
    else:rows=json.loads(path.read_text())
    for i,row in enumerate(rows):
        if dataset=='finqa':yield finqa(row,split,str(path),i)
        elif dataset in ('tatqa','tathqa'):yield from tat(row,dataset,split,str(path),i)
        elif dataset=='convfinqa':yield from conversation(row,split,str(path),i)
        elif dataset=='hybridqa':yield hybrid(row,split,str(path),i,corpus)
        elif dataset=='multihiertt':yield multi(row,split,str(path),i)
        else:raise ValueError('Unknown dataset')
