"""FinQA allowlist reader. No label-derived retrieval fields enter inputs."""
import re
from .execute import number
from .core import EvidenceFact, PredictionExample, ReferenceRecord

VERSION = '0f16e2867befa6840783e58be38c9efb9229d742'


def convert(raw, split, source_file, record_index):
    prefix = f"finqa:{split}:{raw['id']}"
    base = {'file': source_file, 'record_index': record_index, 'document': raw['filename']}
    facts = []
    table = raw['table']
    for r, row in enumerate(table):
        for c, value in enumerate(row):
            fid = f'{prefix}:table:{r}:{c}'
            deps = () if r == 0 or c == 0 else (f'{prefix}:table:0:{c}', f'{prefix}:table:{r}:0')
            facts.append(EvidenceFact(fid, value, dict(base, field='table', table='0', row=r, column=c, row_width=len(row), row_label=row[0] if row else '', cell_raw=value), deps,
                                      'header' if r == 0 or c == 0 else 'cell',
                                      'USD' if '$' in value else 'unknown', bool(deps)))
    for field in ('pre_text', 'post_text'):
        for i, text in enumerate(raw[field]):
            # Offset is local to the original paragraph string, not a reconstructed PDF.
            facts.append(EvidenceFact(f'{prefix}:{field}:{i}', text,
                         dict(base, field=field, paragraph=i, start=0, end=len(text))))
    # Conservative input-only unit dependencies. These mentions may describe the
    # table; uncertainty is explicit rather than assigning a guessed scale.
    unit_sources = tuple(f.id for f in facts if f.kind == 'text' and
                         re.search(r'\b(?:in millions|in thousands|in billions|dollars in|amounts in)\b', f.raw, re.I))
    if unit_sources:
        from dataclasses import replace
        facts = [replace(f, dependencies=f.dependencies + unit_sources,
                         structure_uncertain=True) if f.kind == 'cell' else f for f in facts]
    from dataclasses import replace
    enriched = []
    for fact in facts:
        try:
            value = str(number(fact.raw))
        except Exception:
            value = None
        enriched.append(replace(fact, parsed_decimal=value,
                                scale='percent' if value is not None and fact.raw.strip().endswith('%') else 'unknown'))
    facts = enriched
    # Preserve both raw table views. Never copy an entire raw record.
    document = {'id': prefix, 'filename': raw['filename'], 'table': table,
                'table_ori': raw.get('table_ori'), 'pre_text': raw['pre_text'],
                'post_text': raw['post_text'], 'hierarchy': None,
                'header_inference': 'first row/column; uncertain; no invented ancestors'}
    prediction = PredictionExample('finqa', VERSION, split, raw['id'], raw['qa']['question'], document, tuple(facts))
    reference = ReferenceRecord(raw['id'], {k: v for k, v in raw['qa'].items() if k != 'question'})
    return prediction, reference
