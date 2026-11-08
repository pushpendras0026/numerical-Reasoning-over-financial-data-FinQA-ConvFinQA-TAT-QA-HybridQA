"""Report figures drawn from saved artifacts; nothing here calls a model.

Writes report/generated/doc_sizes.pdf (matplotlib), token_strips.tex and replay.tex (TikZ).
Inputs: artifacts/v11/label_cost.json, report_numbers.json, video_examples.json.
"""
import json
from pathlib import Path

ART, GEN = Path('artifacts/v11'), Path('report/generated')
COST = json.loads((ART / 'label_cost.json').read_text())
NUMBERS = json.loads((ART / 'report_numbers.json').read_text())
EX = json.loads((ART / 'video_examples.json').read_text())
NAME = {'hybridqa': 'HybridQA', 'multihiertt': 'MultiHiertt', 'finqa': 'FinQA', 'convfinqa': 'ConvFinQA',
        'tatqa': 'TAT-QA', 'tathqa': 'TAT-HQA'}


def split(cost, parts):
    sizes = [len(p.encode()) for p in parts]
    raw = [cost * s / sum(sizes) for s in sizes]
    whole = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: whole[i] - raw[i])[:cost - sum(whole)]:
        whole[i] += 1
    return whole


def doc_sizes():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 7.5, 'font.family': 'serif', 'axes.spines.top': False, 'axes.spines.right': False})
    rows = ['tathqa', 'tatqa', 'convfinqa', 'finqa', 'multihiertt', 'hybridqa']
    fig, axis = plt.subplots(figsize=(3.4, 1.75), constrained_layout=True)
    for i, key in enumerate(rows):
        cap = int(NUMBERS['coverage'][key]['cap'])
        once, every = COST[key]['doc_dependency_median'] / cap, COST[key]['doc_ordinary_median'] / cap
        axis.barh(i, every, height=0.62, color='#2A78D6')
        axis.barh(i, once, height=0.62, color='#EB6834')
        axis.text(every + 0.08, i, f"{COST[key]['doc_dependency_median']:,.0f} / {COST[key]['doc_ordinary_median']:,.0f}",
                  va='center', fontsize=6.5)
    axis.set_yticks(range(len(rows)), [f"{NAME[k]} ({int(NUMBERS['coverage'][k]['cap']):,})" for k in rows])
    axis.axvline(1, color='#1F2328', linestyle='--', linewidth=0.9)
    axis.set_xlim(0, 9.2)
    axis.set_xlabel('median document size, in budgets (budget in brackets)')
    axis.legend(handles=[plt.Rectangle((0, 0), 1, 1, color='#EB6834'), plt.Rectangle((0, 0), 1, 1, color='#2A78D6')],
                labels=['each label once (D)', 'labels in every cell (O)'], frameon=False, loc='lower right', fontsize=6.5)
    fig.savefig(GEN / 'doc_sizes.pdf')


def strip(x, y, counts, colors, step=0.105, side=0.085):
    out = []
    for n, color in zip(counts, colors):
        for _ in range(n):
            out.append(f'\\fill[{color}] ({x:.3f},{y:.3f}) rectangle ++({side},{side});')
            x += step
    return out, x


def token_strips():
    visa = EX['visa']
    lines = ['\\begin{tikzpicture}[font=\\scriptsize]']
    lanes = [('Ordinary', 'ordblue', 0.0, [(f['value'], f['parts'], ['colhead', 'rowlab', 'ink']) for f in visa['ordinary']],
              visa['cumulative']['ordinary']),
             ('Dependency', 'deporange', -0.75, [(f['value'], f['parts'], [{'column': 'colhead', 'row': 'rowlab', 'value': 'ink'}[k] for k in f['kinds']])
                                                 for f in visa['dependency']], visa['cumulative']['dependency'])]
    length = []
    for f in visa['length_matched']:
        header, row, value = f['raw'].split(' | ')
        length.append((value, split(f['cost'], [f'c1={header} | ', f'{row} | ', f'{value} | ']), ['colhead', 'rowlab', 'ink']))
    lanes.append(('Length-matched', 'lenaqua', -1.5, length, None))
    for name, color, y, groups, totals in lanes:
        lines.append(f'\\node[anchor=east,text={color},font=\\scriptsize\\bfseries] at (-0.1,{y + 0.04:.2f}) {{{name}}};')
        x = 0.0
        for i, (value, counts, colors) in enumerate(groups):
            squares, end = strip(x, y, counts, colors)
            lines += squares
            lines.append(f'\\node[above] at ({(x + end) / 2:.3f},{y + 0.06:.2f}) {{{value}}};')
            if totals:
                lines.append(f'\\node[below,text={color}] at ({end - 0.05:.3f},{y + 0.02:.2f}) {{{totals[i]}}};')
            x = end + 0.12
    lines.append('\\end{tikzpicture}')
    (GEN / 'token_strips.tex').write_text('\n'.join(lines) + '\n')


def replay():
    r = EX['replay']
    scale, para = 0.115, 1.1
    lines = ['\\begin{tikzpicture}[font=\\scriptsize]']
    for name, color, y, facts in (('O', 'ordblue', 0.0, r['ordinary']['facts']), ('D', 'deporange', -0.95, r['dependency']['facts'])):
        method = r['ordinary' if name == 'O' else 'dependency']
        lines.append(f'\\node[anchor=east,text={color},font=\\scriptsize\\bfseries,align=right] at (-0.1,{y + 0.15:.2f}) {{{name}: {method["used"]}}};')
        paragraphs = sum(f['cost'] for f in facts if f['kind'] == 'text')
        lines.append(f'\\fill[rule] (0,{y}) rectangle ({para},{y + 0.3:.2f}); \\node at ({para / 2},{y + 0.15:.2f}) {{text {paragraphs}}};')
        x, last = para + 0.03, -1.0
        for f in facts:
            if f['kind'] == 'text':
                continue
            w = f['cost'] * scale
            if f['kind'] == 'cell' and ' | ' in f['raw']:
                *labels, value = f['raw'].split(' | ')
                lab, val = split(f['cost'], [' | '.join(labels) + ' | ', value + ' | '])
                lines.append(f'\\fill[rowlab] ({x:.3f},{y}) rectangle ++({lab * scale:.3f},0.3);')
                lines.append(f'\\fill[ink] ({x + lab * scale:.3f},{y}) rectangle ++({val * scale:.3f},0.3);')
            else:
                value = f['raw']
                lines.append(f'\\fill[{"ink" if f["kind"] == "cell" else "colhead"}] ({x:.3f},{y}) rectangle ++({w:.3f},0.3);')
            lines.append(f'\\draw[white,line width=.5pt] ({x:.3f},{y}) rectangle ++({w:.3f},0.3);')
            if f['kind'] == 'cell':
                above = x + w / 2 - 0.2 > last
                lines.append(f'\\node[{"above" if above else "below"}] at ({x + w / 2:.3f},{y + (0.3 if above else 0):.2f}) {{{value.strip()}}};')
                last = x + w / 2 + 0.2 if above else last
            x += w
    cap_x = para + 0.03 + (r['ordinary']['cap'] - sum(f['cost'] for f in r['ordinary']['facts'] if f['kind'] == 'text')) * scale
    lines.append(f'\\draw[densely dashed] ({cap_x:.3f},-1.15) -- ({cap_x:.3f},0.75) node[above] {{budget {r["ordinary"]["cap"]}}};')
    lines.append('\\end{tikzpicture}')
    (GEN / 'replay.tex').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    doc_sizes()
    token_strips()
    replay()
    print('wrote', [p.name for p in sorted(GEN.glob('*')) if p.name in ('doc_sizes.pdf', 'token_strips.tex', 'replay.tex')])
