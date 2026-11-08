"""Presentation clips: one Scene per clip, each played from a slide (see ../speaker_notes.md).

Render all:  /Users/mac/CourseWork/BigDataProject/.manim/bin/manim -qh -a clips.py
Each clip is timed against its narration in the "Video clips" table of speaker_notes.md:
every sentence is a cue at ~140 spoken words per minute, and a clip ends 2 s after its
last sentence. Every number is read from artifacts/v11/*.json (scripts/video_examples.py,
scripts/label_cost.py, scripts/coverage_audit.py, scripts/report_tables.py).
"""
import json
import random
import re
from pathlib import Path

from manim import *

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'artifacts/v11'
COVERAGE = json.loads((ART / 'coverage.json').read_text())
NUMBERS = json.loads((ART / 'report_numbers.json').read_text())
EX = json.loads((ART / 'video_examples.json').read_text())
COST = json.loads((ART / 'label_cost.json').read_text())
NOTES = ROOT / 'presentation/speaker_notes.md'

config.background_color = '#FCFCFB'
INK, MUTED, RULE, PAPER, PALE = '#1F2328', '#5E6168', '#D9D7D0', '#FFFFFF', '#C9CCD1'
# Colour is meaning, fixed for every clip.
ORD, DEP, LEN = '#2A78D6', '#EB6834', '#1BAF7A'   # the three packing methods, nothing else
FOCUS = '#E3A600'                                # what to look at now; also a row label
REJECT = '#C8323C'                               # a value the checker could not find, or a wrong answer
EXEC, DIRECT = '#6B4FBB', '#8A8F98'              # Block B: executor and direct answering
FONT = 'Helvetica Neue'
WPM, AIR = 140, 2.0
ORDER = ['hybridqa', 'multihiertt', 'tathqa', 'tatqa', 'finqa', 'convfinqa']
NAME = {'hybridqa': 'HybridQA', 'multihiertt': 'MultiHiertt', 'tathqa': 'TAT-HQA', 'tatqa': 'TAT-QA',
        'finqa': 'FinQA', 'convfinqa': 'ConvFinQA'}
CAP = {k: int(NUMBERS['coverage'][k]['cap']) for k in ORDER}


def narration():
    """Clip name -> sentences, from the "Video clips" table in speaker_notes.md."""
    clips = {}
    for line in NOTES.read_text().splitlines():
        cols = [c.strip() for c in line.split('|')]
        if len(cols) == 5 and cols[3].startswith('"'):
            clips[cols[1]] = re.split(r'(?<=[.?!])\s+', cols[3].strip('"'))
    return clips


def spoken_seconds(sentence):
    """Words at WPM; a number costs about one word per digit ("3,466" ~ four)."""
    count = 0
    for token in sentence.split():
        m = re.fullmatch(r'\W*(\d[\d,]*)(?:\.(\d+))?\W*', token)
        count += len(m[1].replace(',', '')) + (1 + len(m[2]) if m[2] else 0) if m else 1
    return 60 * count / WPM


NARRATION = narration()


def words(text, size=28, color=INK, **kw):
    return Text(text, font=FONT, font_size=size, color=color, **kw)


def stack(*texts, size=28, color=INK, buff=0.14, **kw):
    return VGroup(*[words(t, size, color, **kw) for t in texts]).arrange(DOWN, buff=buff)


def card(mob, color=MUTED, pad=0.25, fill=PAPER):
    frame = RoundedRectangle(corner_radius=0.12, width=mob.width + 2 * pad, height=mob.height + 2 * pad,
                             color=color, stroke_width=2.5).set_fill(fill, 1).move_to(mob)
    return VGroup(frame, mob)


def visa_table(rows=None):
    """The real FinQA table (V/2008/page_17), header row plus the given body rows."""
    table = EX['visa']['table']
    headers = ['company', 'payments volume\n(billions)', 'total volume\n(billions)', 'total transactions\n(billions)', 'cards\n(millions)']
    widths = [2.9, 2.5, 2.4, 2.95, 1.75]
    body = [r for i, r in enumerate(table[1:], 1) if rows is None or i in rows]
    out = VGroup()
    for r, row in enumerate([headers] + [[c.replace('( 1 )', '(1)') for c in row] for row in body]):
        cells = VGroup()
        for c, value in enumerate(row):
            frame = Rectangle(width=widths[c], height=1.0 if r == 0 else 0.55, color=RULE, stroke_width=1.5).set_fill(PAPER, 1)
            text = stack(*value.split('\n'), size=24, color=MUTED if r == 0 else INK, buff=0.06)
            cells.add(VGroup(frame, text.move_to(frame)))
        out.add(cells.arrange(RIGHT, buff=0))
    return out.arrange(DOWN, buff=0)


def split(cost, parts):
    sizes = [len(p.encode()) for p in parts]
    raw = [cost * s / sum(sizes) for s in sizes]
    whole = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: whole[i] - raw[i])[:cost - sum(whole)]:
        whole[i] += 1
    return whole


def strip(counts, colors, side=0.15, step=0.17):
    """One square per token, coloured by which part of the fact it pays for."""
    squares = VGroup()
    for n, color in zip(counts, colors):
        for _ in range(n):
            squares.add(Square(side, stroke_width=0).set_fill(color, 1))
    return squares.arrange(RIGHT, buff=step - side)


class Narrated(Scene):
    clip = ''

    def begin(self, lead=0.0):
        self.t0 = self.renderer.time
        self.starts, t = [], lead
        for sentence in NARRATION[self.clip]:
            self.starts.append(t)
            t += spoken_seconds(sentence)
        self.starts.append(t)
        self.end_at = t + AIR

    def until(self, t):
        dt = self.t0 + t - self.renderer.time
        if dt > 1 / 30:
            self.wait(dt)
        elif dt < -0.3:
            print(f'[timing] {self.clip}: cue at {t:.1f}s overran by {-dt:.1f}s', flush=True)

    def cue(self, i, frac=0.0):
        self.until(self.starts[i] + frac * (self.starts[i + 1] - self.starts[i]))

    def finish(self):
        self.until(self.end_at)
        print(f'[timing] {self.clip}: {self.renderer.time - self.t0:.1f}s', flush=True)

    def title(self, text):
        heading = words(text, 34, INK, weight='BOLD').to_corner(UL).shift(0.1 * DOWN)
        self.play(FadeIn(heading, shift=0.2 * DOWN), run_time=0.8)
        return heading


class Clip1Labels(Narrated):
    clip = 'A number needs its labels'

    def construct(self):
        self.begin()
        self.title('A number needs its labels')
        table = visa_table().move_to(0.55 * DOWN)
        source = words('FinQA development set · V/2008/page_17 (Visa annual report)', 24, MUTED).to_edge(DOWN, buff=0.35)
        self.play(LaggedStart(*[FadeIn(row, shift=0.1 * UP) for row in table], lag_ratio=0.12), FadeIn(source), run_time=1.6)

        # The question
        self.cue(1)
        question = words(f'"{EX["visa"]["question"].capitalize()}"', 26, INK).move_to(2.55 * UP)
        self.play(FadeIn(question), run_time=1.0)

        # The retriever's top two cells
        self.cue(2)
        top = [table[3][1], table[3][2]]
        assert [c[1][0].text for c in top] == EX['visa']['top_cells']
        rings = VGroup(*[SurroundingRectangle(c, color=FOCUS, buff=0.02, stroke_width=5) for c in top])
        badges = VGroup()
        for i, ring in enumerate(rings, 1):
            dot = Circle(0.22, color=FOCUS, stroke_width=0).set_fill(FOCUS, 1)
            badges.add(VGroup(dot, words(str(i), 24, INK, weight='BOLD').move_to(dot)).move_to(ring.get_corner(UL)))
        self.play(Create(rings), FadeIn(badges), run_time=1.0)

        # Strip the labels
        self.cue(3)
        big = VGroup(words('637', 80), words('647', 80)).arrange(RIGHT, buff=3.0).move_to(0.1 * DOWN)
        self.play(TransformFromCopy(top[0][1], big[0]), TransformFromCopy(top[1][1], big[1]),
                  FadeOut(VGroup(table, rings, badges, source)), question.animate.set_opacity(0.4), run_time=1.6)
        marks = VGroup(*[words('?', 60, MUTED).next_to(b, UP, buff=0.5) for b in big])
        self.play(FadeIn(marks, shift=0.1 * DOWN), run_time=0.8)

        # The labels say which is which
        self.cue(4)
        labels = VGroup(stack('payments volume', '(billions)', size=30, weight='BOLD'),
                        stack('total volume', '(billions)', size=30, color=MUTED))
        for label, b in zip(labels, big):
            label.next_to(b, UP, buff=0.45)
        self.play(*[ReplacementTransform(m, l) for m, l in zip(marks, labels)], run_time=1.2)
        self.play(Create(SurroundingRectangle(VGroup(labels[0], big[0]), color=FOCUS, buff=0.2, stroke_width=4)), run_time=0.8)

        # The answer depends on them
        self.cue(5)
        answer = words('637 ÷ 5.0 = 127.4', 44, INK).move_to(2.3 * DOWN)
        reading = words('payments volume ÷ total transactions', 26, MUTED).next_to(answer, DOWN, buff=0.25)
        self.play(Write(answer), FadeIn(reading), run_time=1.6)
        self.finish()


class Clip2Budget(Narrated):
    clip = 'The budget forces a choice'

    def construct(self):
        self.begin()
        self.title('The budget forces a choice')
        x0, unit = -2.4, 1.0                      # x of "0 x budget"; one budget per unit
        ys = [1.8 - 0.72 * i for i in range(6)]
        rows = ['hybridqa', 'multihiertt', 'finqa', 'convfinqa', 'tatqa', 'tathqa']
        budget_line = DashedLine([x0 + unit, ys[0] + 0.5, 0], [x0 + unit, ys[-1] - 0.45, 0], color=INK, stroke_width=3)
        budget_tag = words('budget', 24, INK).next_to(budget_line, UP, buff=0.12)
        axis = Line([x0, ys[-1] - 0.45, 0], [x0 + 8.2 * unit, ys[-1] - 0.45, 0], color=MUTED, stroke_width=2)
        ticks = VGroup(*[words(f'{v}×', 22, MUTED).next_to([x0 + v * unit, ys[-1] - 0.45, 0], DOWN, buff=0.12) for v in (0, 1, 2, 4, 6, 8)])
        axis_label = words('median document size, in budgets', 24, MUTED).next_to(axis, DOWN, buff=0.55)
        self.play(Create(axis), FadeIn(ticks), FadeIn(axis_label), Create(budget_line), FadeIn(budget_tag), run_time=1.2)

        # The median document under each dataset's budget
        self.cue(1)
        bars, values, names = VGroup(), VGroup(), VGroup()
        for key, y in zip(rows, ys):
            size, cap = COST[key]['doc_dependency_median'], CAP[key]
            bar = Rectangle(width=unit * size / cap, height=0.42, stroke_width=0).set_fill(DEP, 0.85)
            bars.add(bar.move_to([x0 + bar.width / 2, y, 0]))
            values.add(words(f'{size:,.0f}', 24, INK).next_to(bar, RIGHT, buff=0.15))
            names.add(words(f'{NAME[key]}  ({cap:,})', 24, INK).move_to([x0 - 0.25, y, 0], aligned_edge=RIGHT))
        key_once = VGroup(Square(0.25, stroke_width=0).set_fill(DEP, 0.85), words('each label written once', 24, INK)).arrange(RIGHT, buff=0.15)
        key_once.move_to([3.6, 2.85, 0], aligned_edge=RIGHT)
        self.play(FadeIn(names), LaggedStart(*[GrowFromEdge(b, LEFT) for b in bars], lag_ratio=0.1), FadeIn(values), FadeIn(key_once), run_time=1.8)

        # HybridQA
        self.cue(2)
        ring = SurroundingRectangle(VGroup(names[0], values[0]), color=FOCUS, buff=0.1, stroke_width=4)
        self.play(Create(ring), run_time=0.8)

        # Labels in every cell make documents bigger
        self.cue(3)
        key_every = VGroup(Square(0.25, stroke_width=0).set_fill(ORD, 0.85), words('labels in every cell', 24, INK)).arrange(RIGHT, buff=0.15)
        key_every.next_to(key_once, RIGHT, buff=0.4)
        VGroup(key_once, key_every).move_to([6.9, 2.85, 0], aligned_edge=RIGHT)
        self.play(FadeOut(ring), FadeIn(key_every), run_time=0.8)
        self.cue(4)
        grown, moved = [], []
        for key, y, bar, value in zip(rows, ys, bars, values):
            size, cap = COST[key]['doc_ordinary_median'], CAP[key]
            extra = Rectangle(width=unit * size / cap - bar.width, height=0.42, stroke_width=0).set_fill(ORD, 0.85)
            extra.next_to(bar, RIGHT, buff=0)
            grown.append(extra)
            moved.append(Transform(value, words(f'{size:,.0f}', 24, ORD, weight='BOLD').next_to(extra, RIGHT, buff=0.15)))
        self.play(*[GrowFromEdge(g, LEFT) for g in grown], *moved, run_time=1.8)
        self.play(Create(ring := SurroundingRectangle(VGroup(names[1], values[1]), color=FOCUS, buff=0.1, stroke_width=4)), run_time=0.6)

        # TAT-QA fits only with labels written once
        self.cue(5)
        tat = SurroundingRectangle(VGroup(names[4], names[5], values[4], values[5]), color=FOCUS, buff=0.1, stroke_width=4)
        self.play(ReplacementTransform(ring, tat), run_time=0.8)

        # The question
        self.cue(6)
        point = words('Which facts to keep, and how to pay for their labels?', 30, INK, weight='BOLD').to_edge(DOWN, buff=0.3)
        self.play(FadeOut(tat), FadeOut(axis_label), Write(point), run_time=1.5)
        self.finish()


class Clip3Paying(Narrated):
    clip = 'Paying for labels'
    COLUMN, ROW, VALUE = PALE, FOCUS, INK

    def lane(self, name, color, y):
        label = words(name, 28, color, weight='BOLD').move_to([-5.75, y + 0.12, 0])
        return label

    def groups(self, specs, y, x=-4.45):
        """specs: list of (value, counts, colors). Returns list of (strip, value label)."""
        out = []
        for value, counts, colors in specs:
            s = strip(counts, colors).move_to([0, y, 0])
            s.shift((x - s.get_left()[0]) * RIGHT)
            out.append((s, words(value, 24, INK).next_to(s, UP, buff=0.12)))
            x = s.get_right()[0] + 0.22
        return out

    def construct(self):
        self.begin()
        self.title('Paying for labels')
        legend = VGroup(*[VGroup(Square(0.2, stroke_width=0).set_fill(c, 1), words(t, 22, MUTED)).arrange(RIGHT, buff=0.1)
                          for c, t in ((self.COLUMN, 'column header'), (self.ROW, 'row label'), (self.VALUE, 'value'))],
                        words('1 square = 1 token', 22, MUTED)).arrange(RIGHT, buff=0.35).to_corner(UR).shift(0.12 * DOWN)
        mini = visa_table(rows=[3]).scale(0.9).move_to(2.0 * UP)
        self.play(FadeIn(mini), FadeIn(legend), run_time=1.2)
        visa = EX['visa']

        # Ordinary: each cell carries its labels
        self.cue(1)
        o_y, d_y, l_y = 0.45, -1.25, -2.95
        o_label = self.lane('Ordinary', ORD, o_y)
        o_specs = [(f['value'], f['parts'], [self.COLUMN, self.ROW, self.VALUE]) for f in visa['ordinary']]
        o_groups = self.groups(o_specs, o_y)
        rendered = words(visa['ordinary'][0]['rendered'], 24, MUTED).next_to(o_groups[0][0], DOWN, buff=0.45, aligned_edge=LEFT)
        o_counts = VGroup(*[words(str(n), 24, ORD).next_to(g[0], DOWN, buff=0.12, aligned_edge=RIGHT) for g, n in zip(o_groups, visa['cumulative']['ordinary'])])
        self.play(FadeIn(o_label), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(sq) for sq in o_groups[0][0]], lag_ratio=0.08), FadeIn(o_groups[0][1]), FadeIn(rendered), run_time=1.6)
        self.play(FadeIn(o_counts[0]), run_time=0.4)

        # The row label again, in every cell
        self.cue(2)
        self.play(FadeOut(rendered), run_time=0.4)
        for (s, v), c in zip(o_groups[1:], o_counts[1:]):
            self.play(LaggedStart(*[FadeIn(sq) for sq in s], lag_ratio=0.04), FadeIn(v), FadeIn(c), run_time=0.9)
        repeats = VGroup(*[VGroup(*s[f['parts'][0]:f['parts'][0] + f['parts'][1]]) for (s, _), f in zip(o_groups, visa['ordinary'])])
        self.play(LaggedStart(*[Indicate(r, color=FOCUS, scale_factor=1.25) for r in repeats], lag_ratio=0.3), run_time=1.5)

        # Dependency: each label once
        self.cue(3)
        d_label = self.lane('Dependency', DEP, d_y)
        kind_color = {'column': self.COLUMN, 'row': self.ROW, 'value': self.VALUE}
        d_specs = [(f['value'], f['parts'], [kind_color[k] for k in f['kinds']]) for f in visa['dependency']]
        d_groups = self.groups(d_specs, d_y)
        d_counts = VGroup(*[words(str(n), 24, DEP).next_to(g[0], DOWN, buff=0.12, aligned_edge=RIGHT) for g, n in zip(d_groups, visa['cumulative']['dependency'])])
        self.play(FadeIn(d_label), run_time=0.5)

        # The first cell costs more
        self.cue(4)
        self.play(LaggedStart(*[FadeIn(sq) for sq in d_groups[0][0]], lag_ratio=0.06), FadeIn(d_groups[0][1]), run_time=1.4)
        self.play(FadeIn(d_counts[0]), run_time=0.4)
        self.play(Indicate(d_counts[0], color=DEP, scale_factor=1.5), Indicate(o_counts[0], color=ORD, scale_factor=1.5), run_time=1.0)

        # Then every further cell reuses the labels
        self.cue(5)
        for (s, v), c in zip(d_groups[1:], d_counts[1:]):
            self.play(LaggedStart(*[FadeIn(sq) for sq in s], lag_ratio=0.05), FadeIn(v), FadeIn(c), run_time=0.8)
        totals = VGroup(words(f"{visa['cumulative']['ordinary'][-1]} tokens", 26, ORD, weight='BOLD'),
                        words(f"{visa['cumulative']['dependency'][-1]} tokens", 26, DEP, weight='BOLD'))
        totals[0].next_to(o_label, DOWN, buff=0.15)
        totals[1].next_to(d_label, DOWN, buff=0.15)
        self.play(FadeIn(totals), run_time=0.6)

        # Length-matched: ordinary facts plus neighbours, to D's length
        self.cue(6)
        l_label = self.lane('Length-\nmatched', LEN, l_y)
        l_specs = []
        for f in visa['length_matched']:
            header, row, value = f['raw'].split(' | ')
            l_specs.append((value, split(f['cost'], [f'c1={header} | ', f'{row} | ', f'{value} | ']), [self.COLUMN, self.ROW, self.VALUE]))
        l_groups = self.groups(l_specs, l_y)
        self.play(FadeIn(l_label), *[FadeIn(s) for s, _ in l_groups], *[FadeIn(v) for _, v in l_groups], run_time=1.2)
        self.cue(7)
        used = sum(f['cost'] for f in visa['length_matched'])
        target = visa['cumulative']['dependency'][-1]
        neighbour = SurroundingRectangle(VGroup(*l_groups[1]), color=LEN, buff=0.08, stroke_width=3)
        note = words('Mastercard, next to 637', 24, LEN).next_to(neighbour, DOWN, buff=0.12)
        missing_cost = visa['ordinary'][2]['cost']
        ghost = strip([missing_cost], [PAPER]).next_to(l_groups[-1][0], RIGHT, buff=0.22)
        ghost_box = SurroundingRectangle(ghost, color=REJECT, buff=0.04, stroke_width=3)
        ghost_label = words(f'5.0 needs {missing_cost}, {target - used} left', 24, REJECT).next_to(ghost_box, DOWN, buff=0.12)
        self.play(Create(neighbour), FadeIn(note), run_time=0.8)
        self.play(Create(ghost_box), FadeIn(ghost_label), run_time=0.8)

        # Over every table
        self.cue(8)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        self.title('Paying for labels: every development table')
        ys = [1.9 - 0.72 * i for i in range(6)]
        rows = ['multihiertt', 'tatqa', 'tathqa', 'convfinqa', 'finqa', 'hybridqa']
        x0, scale = -2.2, 0.24
        chart = VGroup()
        for key, y in zip(rows, ys):
            o, d = COST[key]['cell_ordinary_mean'], COST[key]['cell_bare_mean']
            ob = Rectangle(width=o * scale, height=0.26, stroke_width=0).set_fill(ORD, 0.9).move_to([x0 + o * scale / 2, y + 0.15, 0])
            db = Rectangle(width=d * scale, height=0.26, stroke_width=0).set_fill(DEP, 0.9).move_to([x0 + d * scale / 2, y - 0.15, 0])
            chart.add(VGroup(words(NAME[key], 24, INK).move_to([x0 - 0.3, y, 0], aligned_edge=RIGHT), ob, db,
                             words(f'{o:.1f}', 22, ORD).next_to(ob, RIGHT, buff=0.12), words(f'{d:.1f}', 22, DEP).next_to(db, RIGHT, buff=0.12),
                             words(f'{o / d:.1f}×', 26, INK, weight='BOLD').move_to([5.6, y, 0])))
        key = VGroup(*[VGroup(Square(0.25, stroke_width=0).set_fill(c, 0.9), words(t, 24, INK)).arrange(RIGHT, buff=0.15)
                       for c, t in ((ORD, 'cell with its labels'), (DEP, 'bare cell, once its labels are packed'))]).arrange(RIGHT, buff=0.6)
        key.next_to(chart, DOWN, buff=0.45)
        unit_note = words('mean tokens per table cell, exact under the pipeline\'s counter', 22, MUTED).next_to(key, DOWN, buff=0.15)
        self.play(LaggedStart(*[FadeIn(r, shift=0.1 * RIGHT) for r in chart], lag_ratio=0.12), FadeIn(key), FadeIn(unit_note), run_time=2.0)
        self.cue(9)
        self.play(Create(SurroundingRectangle(chart[0], color=FOCUS, buff=0.08, stroke_width=4)), run_time=0.8)

        # The trade
        self.cue(10)
        trade = card(stack('a fixed cost for structure,', 'then more facts per token', size=32, weight='BOLD'), DEP, fill=PAPER)
        trade.to_edge(DOWN, buff=0.25)
        self.play(FadeOut(unit_note), FadeOut(key), FadeIn(trade, shift=0.1 * UP), run_time=1.0)
        self.finish()


class Clip4Grounding(Narrated):
    clip = 'Copy, then check'

    def construct(self):
        self.begin()
        self.title('Copy, then check')
        table = visa_table(rows=[2, 3, 4]).scale(0.95).move_to(1.25 * DOWN)
        self.cue(1)
        plan = words('divide("637", "5.0")', 44, INK).move_to(2.3 * UP)
        tag = words('the model\'s plan', 24, MUTED).next_to(plan, LEFT, buff=0.5)
        self.play(Write(plan), FadeIn(tag), FadeIn(table), run_time=1.6)
        lit = {'a': plan[8:11], 'b': plan[14:17]}

        # Code finds each copied number
        self.cue(2)
        cells = {v: table[r][c] for r, row in enumerate(table) for c, v in enumerate([x[1][0].text if len(x[1]) == 1 else '' for x in row])}
        context = [c for row in table[1:] for c in row]
        self.play(*[c.animate.set_opacity(0.3) for c in context], run_time=0.5)
        rings = {}
        for key, value in (('a', '637'), ('b', '5.0')):
            cell = cells[value]
            pair = VGroup(SurroundingRectangle(lit[key], color=FOCUS, buff=0.08, stroke_width=4),
                          SurroundingRectangle(cell, color=FOCUS, buff=0.02, stroke_width=4))
            flying = lit[key].copy()
            self.play(Create(pair[0]), run_time=0.4)
            self.play(flying.animate.move_to(cell[1]).scale(0.6).set_opacity(0), Create(pair[1]), cell.animate.set_opacity(1), run_time=0.9)
            self.remove(flying)
            rings[key] = pair

        # Both found: the plan runs
        self.cue(3)
        status = words('both found  →  637 ÷ 5.0 = 127.4', 32, INK).move_to(1.35 * UP)
        self.play(FadeIn(status, shift=0.1 * DOWN), run_time=0.8)

        # An invented number is rejected
        self.cue(4)
        new = words('640', 44, INK).move_to(lit['a'])
        self.play(FadeOut(status), FadeOut(rings['a']), cells['637'].animate.set_opacity(0.3), ReplacementTransform(lit['a'], new), run_time=0.8)
        numeric = [c for row in table[1:] for c in row[1:]]
        probe = SurroundingRectangle(numeric[0], color=REJECT, buff=0.02, stroke_width=4)
        self.play(Create(probe), run_time=0.2)
        for c in numeric[1:]:
            self.play(probe.animate.move_to(c), run_time=0.12)
        self.play(FadeOut(probe), run_time=0.2)
        cross = Cross(new, stroke_color=REJECT, stroke_width=6)
        status = words('640 is in no cell: plan rejected', 32, REJECT).move_to(1.35 * UP)
        self.play(Create(cross), FadeIn(status), run_time=0.8)

        # A wrong real number passes
        self.cue(5)
        wrong = words('647', 44, INK).move_to(new)
        ring = VGroup(SurroundingRectangle(wrong, color=FOCUS, buff=0.08, stroke_width=4),
                      SurroundingRectangle(cells['647'], color=FOCUS, buff=0.02, stroke_width=4))
        self.play(FadeOut(cross), FadeOut(status), ReplacementTransform(new, wrong), run_time=0.8)
        self.play(Create(ring), cells['647'].animate.set_opacity(1), run_time=0.8)
        status = VGroup(words('found  →  647 ÷ 5.0 = 129.4', 30, INK), words('passes the check, wrong answer', 30, REJECT, weight='BOLD')).arrange(DOWN, buff=0.12).move_to(1.2 * UP)
        self.play(FadeIn(status), run_time=0.8)

        # The point
        self.cue(6)
        point = card(stack('Grounding stops invented numbers.', 'Only labels stop wrong choices.', size=32, weight='BOLD'), FOCUS)
        point.move_to(1.25 * DOWN)
        self.play(FadeOut(table), FadeOut(ring), FadeOut(rings['b']), FadeIn(point, shift=0.1 * UP), run_time=1.0)

        # The earlier design
        self.cue(7)
        before = stack('Earlier design, character offsets: 2 of 883 FinQA questions', '(that run also used a different model)', size=24, color=MUTED)
        before.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(before), run_time=1.0)
        self.finish()


class Clip5Measure(Narrated):
    clip = 'How we measure'

    def construct(self):
        self.begin()
        self.title('How we measure')
        n_all = sum(COVERAGE[k]['n'] for k in ORDER)
        boxes = VGroup(*[card(stack(*t, size=24), MUTED) for t in (
            ('1  Coverage audit', 'no model', f'all {n_all:,} questions'),
            ('2  Block A', 'Gemini 3.5 Flash-Lite', 'O vs D vs L, 50 per dataset'),
            ('3  Block B', 'Gemini 3.1 Flash-Lite', 'executor vs direct, 40 each'))]).arrange(RIGHT, buff=0.45).move_to(2.0 * UP)
        arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.06, color=MUTED, stroke_width=3) for a, b in zip(boxes, boxes[1:])])
        self.play(LaggedStart(*[FadeIn(b) for b in boxes], lag_ratio=0.3), FadeIn(arrows), run_time=1.6)

        # Coverage: is every needed number still there?
        self.cue(1)
        self.play(boxes[0][0].animate.set_stroke(FOCUS, 5), boxes[1].animate.set_opacity(0.35), boxes[2].animate.set_opacity(0.35),
                  arrows.animate.set_opacity(0.35), run_time=0.6)
        program = words('gold program:  divide(637, const_5)', 30, INK).move_to(0.4 * UP)
        self.play(FadeIn(program), run_time=0.8)

        # For the Visa question only 637 must survive
        self.cue(2)
        need = VGroup(words('637  must be in the packed evidence', 28, INK), words('const_5  is a constant, always available', 28, MUTED)).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        need.next_to(program, DOWN, buff=0.45)
        self.play(FadeIn(need, shift=0.1 * DOWN), run_time=1.0)

        # Every question, every budget, every method
        self.cue(3)
        count = words(f'{n_all:,} questions  ×  5 budgets  ×  3 methods  =  {n_all * 15:,} packings', 30, INK, weight='BOLD').move_to(0.4 * DOWN)
        self.play(FadeOut(program), FadeOut(need), FadeIn(count), run_time=1.0)

        # One dot per HybridQA question
        self.cue(4)
        dots = EX['hybridqa_dots']
        side, step, cols = 0.06, 0.074, 59
        grid = VGroup(*[Square(side, stroke_width=0).set_fill(PALE, 1) for _ in range(dots['n'])])
        grid.arrange_in_grid(cols=cols, buff=step - side).move_to([-3.6, -1.6, 0])
        caption = words(f'HybridQA, {dots["n"]:,} questions, budget 1,500', 24, MUTED).next_to(grid, UP, buff=0.15)
        self.play(FadeOut(count), FadeIn(grid), FadeIn(caption), run_time=1.0)
        order = list(range(dots['n']))
        random.Random(0).shuffle(order)  # positions are arbitrary; counts are exact
        groups = {}
        start = 0
        for name in ('both', 'neither', 'dep_only', 'ord_only'):
            groups[name] = VGroup(*[grid[i] for i in order[start:start + dots[name]]])
            start += dots[name]

        # Kept by both, or lost by both
        self.cue(5)
        legend = VGroup()
        for name, color, text in (('both', '#9AA0A6', 'kept by both'), ('neither', RULE, 'lost by both')):
            legend.add(VGroup(Square(0.25, stroke_width=0).set_fill(color, 1), words(f'{dots[name]:,}  {text}', 26, INK)).arrange(RIGHT, buff=0.2))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([3.2, 0.3, 0])
        self.play(groups['both'].animate.set_fill('#9AA0A6', 1), groups['neither'].animate.set_fill(RULE, 1), FadeIn(legend), run_time=1.4)

        # Only one method keeps them
        self.cue(6)
        piles = VGroup()
        for name, color, text in (('dep_only', DEP, 'kept only by dependency'), ('ord_only', ORD, 'kept only by ordinary')):
            target = VGroup(*[Square(0.11, stroke_width=0).set_fill(color, 1) for _ in range(dots[name])]).arrange_in_grid(cols=24, buff=0.03)
            piles.add(VGroup(target, words(f'{dots[name]}  {text}', 26, color, weight='BOLD')))
        piles[0].arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(legend, DOWN, aligned_edge=LEFT, buff=0.45)
        piles[1].arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(piles[0], DOWN, aligned_edge=LEFT, buff=0.3)
        self.play(groups['dep_only'].animate.set_fill(DEP, 1), groups['ord_only'].animate.set_fill(ORD, 1), run_time=0.8)
        self.play(*[ReplacementTransform(groups[k].copy(), piles[i][0]) for i, k in enumerate(('dep_only', 'ord_only'))],
                  FadeIn(piles[0][1]), FadeIn(piles[1][1]), run_time=1.8)

        # Block A, then Block B
        for i in (1, 2):
            self.cue(6 + i)
            self.play(boxes[i - 1][0].animate.set_stroke(MUTED, 2.5), boxes[i - 1].animate.set_opacity(0.35 if i == 2 else 1),
                      boxes[i].animate.set_opacity(1), run_time=0.4)
            self.play(boxes[i][0].animate.set_stroke(FOCUS, 5), arrows[i - 1].animate.set_opacity(1), run_time=0.6)
        self.finish()


class Clip6Results(Narrated):
    clip = 'Results'

    def construct(self):
        self.begin()
        self.title('Results')
        caps = [200, 400, 800, 1500, 4000]
        panels = VGroup()
        for key in ['hybridqa', 'multihiertt', 'tatqa', 'tathqa', 'finqa', 'convfinqa']:
            axes = Axes(x_range=[0, 4, 1], y_range=[0, 100, 50], x_length=3.2, y_length=1.6, tips=False,
                        axis_config={'color': MUTED, 'stroke_width': 1.5})
            data = COVERAGE[key]['coverage']
            curves = VGroup()
            for method, color in (('length_matched', LEN), ('ordinary', ORD), ('dependency', DEP)):
                pts = [axes.c2p(i, 100 * data[str(c)][method]) for i, c in enumerate(caps)]
                curves.add(VMobject(stroke_color=color, stroke_width=4 if method == 'dependency' else 3).set_points_as_corners(pts))
            chosen = DashedLine(axes.c2p(caps.index(CAP[key]), 0), axes.c2p(caps.index(CAP[key]), 100), color=FOCUS, stroke_width=2.5)
            ticks = VGroup(*[words(t, 20, MUTED).next_to(axes.c2p(i, 0), DOWN, buff=0.08) for i, t in enumerate(('200', '400', '800', '1.5k', '4k'))],
                           words('100', 20, MUTED).next_to(axes.c2p(0, 100), LEFT, buff=0.08), words('0', 20, MUTED).next_to(axes.c2p(0, 0), LEFT, buff=0.08))
            name = words(NAME[key], 24, INK, weight='BOLD').next_to(axes, UP, buff=0.12)
            panels.add(VGroup(axes, ticks, name, curves, chosen))
        panels.arrange_in_grid(rows=2, cols=3, buff=(0.75, 0.75)).move_to(0.25 * DOWN)
        key = VGroup(*[VGroup(Line(LEFT * 0.2, RIGHT * 0.2, color=c, stroke_width=5), words(t, 24, INK)).arrange(RIGHT, buff=0.12)
                       for c, t in ((DEP, 'Dependency'), (ORD, 'Ordinary'), (LEN, 'Length-matched'))],
                     VGroup(DashedLine(LEFT * 0.2, RIGHT * 0.2, color=FOCUS, stroke_width=3), words('chosen budget', 24, INK)).arrange(RIGHT, buff=0.12))
        key.arrange(RIGHT, buff=0.5).to_edge(DOWN, buff=0.3)
        axis_note = words('gold evidence kept (%) against budget (tokens, not to scale)', 22, MUTED).next_to(panels, UP, buff=0.12).align_to(panels, LEFT)
        self.play(LaggedStart(*[FadeIn(p[:3]) for p in panels], lag_ratio=0.1), FadeIn(key), FadeIn(axis_note), run_time=1.4)
        self.play(*[Create(p[3]) for p in panels], run_time=2.0)

        # On top at the chosen budgets; curves meet as budgets grow
        self.cue(1)
        self.play(*[Create(p[4]) for p in panels], run_time=1.0)

        # D - O at each chosen budget
        self.cue(2)
        self.play(FadeOut(panels), FadeOut(key), FadeOut(axis_note), run_time=0.8)
        row_y = [1.5 - 0.62 * i for i in range(6)]
        zero_x, right_x = -0.9, 4.6

        def diff(k, cap):
            cov = COVERAGE[k]['coverage'][str(cap)]
            return 100 * (cov['dependency'] - cov['ordinary'])

        unit = (right_x - zero_x) / max(diff(k, c) for k in ORDER for c in (CAP[k], 200, 4000))

        def row(k, cap, y):
            d = round(diff(k, cap), 1)
            color = DEP if d > 0 else ORD if d < 0 else MUTED
            bar = Rectangle(width=max(abs(d) * unit, 0.04), height=0.4, stroke_width=0).set_fill(color, 0.9).move_to([zero_x + d * unit / 2, y, 0])
            value = words('0.0' if d == 0 else f'{d:+.1f}', 26, color, weight='BOLD').move_to([6.0, y, 0], aligned_edge=RIGHT)
            tag = words(f'{cap:,}', 24, MUTED).move_to([-2.65, y, 0], aligned_edge=RIGHT)
            return bar, value, tag

        heading = words('Dependency minus Ordinary, gold evidence kept (points)', 28, INK, weight='BOLD').move_to(2.6 * UP)
        state = words("at each dataset's chosen budget", 26, MUTED).next_to(heading, DOWN, buff=0.15)
        names = VGroup(*[words(NAME[k], 26, INK).move_to([-3.85, y, 0], aligned_edge=RIGHT) for k, y in zip(ORDER, row_y)])
        axis = Line([zero_x, row_y[0] + 0.4, 0], [zero_x, row_y[-1] - 0.4, 0], color=MUTED, stroke_width=2)
        parts = [row(k, CAP[k], y) for k, y in zip(ORDER, row_y)]
        bars, values, tags = (VGroup(*p) for p in zip(*parts))
        self.play(FadeIn(heading), FadeIn(state), FadeIn(names), Create(axis), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(VGroup(*p), shift=0.1 * RIGHT) for p in parts], lag_ratio=0.12), run_time=1.6)

        # Largest where documents dwarf the budget; smallest where documents are prose
        self.cue(3)
        big = SurroundingRectangle(VGroup(names[0], names[1], values[0], values[1]), color=FOCUS, buff=0.08, stroke_width=4)
        self.play(Create(big), run_time=0.8)
        self.cue(3, 0.55)
        small = SurroundingRectangle(VGroup(names[4], names[5], values[4], values[5]), color=MUTED, buff=0.08, stroke_width=3)
        self.play(ReplacementTransform(big, small), run_time=0.8)

        def move(cap, text):
            nonlocal state
            new = [row(k, cap, y) for k, y in zip(ORDER, row_y)]
            label = words(text, 26, MUTED).move_to(state)
            self.play(FadeTransform(state, label), *[b.animate.become(nb) for b, (nb, _, _) in zip(bars, new)],
                      *[FadeTransform(v, nv) for v, (_, nv, _) in zip(values, new)],
                      *[FadeTransform(t, nt) for t, (_, _, nt) in zip(tags, new)], run_time=1.5)
            state = label
            for i, (_, nv, nt) in enumerate(new):
                values.submobjects[i], tags.submobjects[i] = nv, nt

        # 200 tokens: the fixed cost loses on two datasets
        self.cue(4)
        self.play(FadeOut(small), run_time=0.3)
        move(200, 'at 200 tokens, the smallest budget')
        losers = VGroup(*[SurroundingRectangle(VGroup(names[i], values[i]), color=FOCUS, buff=0.08, stroke_width=3)
                          for i, k in enumerate(ORDER) if diff(k, 200) < 0])
        self.play(Create(losers), run_time=0.6)

        # 4,000 tokens: the gap closes
        self.cue(5)
        self.play(FadeOut(losers), run_time=0.3)
        move(4000, 'at 4,000 tokens')

        # Answers: Block A, D - O with 95% intervals
        self.cue(6)
        self.play(*[FadeOut(m) for m in self.mobjects if m not in ()], run_time=0.8)
        self.title('Answers follow: Block A, Dependency minus Ordinary')
        a = NUMBERS['a']
        ys = [1.8 - 0.66 * i for i in range(6)]
        axis = NumberLine(x_range=[-10, 25, 5], length=6.0, color=MUTED, include_numbers=False).move_to([0.0, ys[-1] - 0.6, 0])
        nums = VGroup(*[words(f'{v:+d}' if v else '0', 22, MUTED).next_to(axis.n2p(v), DOWN, buff=0.12) for v in range(-10, 26, 5)])
        zero = DashedLine(axis.n2p(0) + UP * (ys[0] - ys[-1] + 1.1), axis.n2p(0), color=MUTED, stroke_width=2)
        label = words('answer score difference, points, with 95% interval (n = 50; ConvFinQA 45)', 22, MUTED).next_to(nums, DOWN, buff=0.2)
        rows = VGroup()
        for k, y in zip(ORDER, ys):
            r = a[k]
            lo, hi, d = 100 * r['ci'][0], 100 * r['ci'][1], 100 * r['diff']
            clear = lo > 0
            color = DEP if clear else MUTED
            p = lambda v: [axis.n2p(v)[0], y, 0]
            rows.add(VGroup(words(NAME[k], 26, INK, weight='BOLD' if clear else 'NORMAL').move_to([-3.4, y, 0], aligned_edge=RIGHT),
                            Line(p(lo), p(hi), color=color, stroke_width=4), Dot(p(d), radius=0.1, color=color),
                            words(f'{d:+.1f}  [{lo:+.1f}, {hi:+.1f}]', 24, color).move_to([6.9, y, 0], aligned_edge=RIGHT)))
        self.play(Create(axis), FadeIn(nums), Create(zero), FadeIn(label), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(r, shift=0.1 * RIGHT) for r in rows], lag_ratio=0.12), run_time=1.8)
        self.finish()


class Clip7Replay(Narrated):
    clip = 'A real question, replayed'
    scale, paragraph_width = 0.2, 2.0

    def lane(self, facts, y, x=-4.4):
        """Paragraphs as one broken block, then each other fact at scale; returns (group, cell blocks)."""
        paragraphs = sum(f['cost'] for f in facts if f['kind'] == 'text')
        block = Rectangle(width=self.paragraph_width, height=0.55, stroke_width=0).set_fill(PALE, 1)
        block.move_to([x + self.paragraph_width / 2, y, 0])
        zig = VMobject(stroke_color=PAPER, stroke_width=6).set_points_as_corners(
            [block.get_top() + 0.25 * RIGHT + d for d in (ORIGIN, 0.12 * DOWN + 0.1 * LEFT, 0.25 * DOWN + 0.1 * RIGHT, 0.4 * DOWN + 0.1 * LEFT, 0.55 * DOWN)])
        para = VGroup(block, zig, words(f'paragraphs {paragraphs}', 22, MUTED).next_to(block, UP, buff=0.1))
        cells, x = VGroup(), x + self.paragraph_width + 0.04
        last_right = -10.0
        for f in facts:
            if f['kind'] == 'text':
                continue
            w = f['cost'] * self.scale
            if f['kind'] == 'cell' and ' | ' in f['raw']:          # ordinary: labels inline, value last
                *labels, value = f['raw'].split(' | ')
                label_tokens, value_tokens = split(f['cost'], [' | '.join(labels) + ' | ', value + ' | '])
                parts = [(label_tokens, FOCUS), (value_tokens, INK)]
            else:
                value = f['raw']
                parts = [(f['cost'], INK if f['kind'] == 'cell' else PALE)]
            blocks = VGroup()
            for tokens, color in parts:
                blocks.add(Rectangle(width=tokens * self.scale, height=0.55, stroke_width=0).set_fill(color, 0.9))
            blocks.arrange(RIGHT, buff=0).move_to([x + w / 2, y, 0])
            frame = Rectangle(width=w, height=0.55, color=PAPER, stroke_width=2).move_to(blocks)
            cell = VGroup(blocks, frame)
            if f['kind'] == 'cell':
                label = words(value.strip(), 24, INK).next_to(blocks, UP, buff=0.1)
                if label.get_left()[0] < last_right + 0.08:
                    label.next_to(blocks, DOWN, buff=0.1)
                else:
                    last_right = label.get_right()[0]
                cell.add(label)
            cells.add(cell)
            x += w
        return para, cells

    def construct(self):
        self.begin()
        self.title('A real question, replayed')
        r = EX['replay']
        o_y, d_y = 0.75, -1.4
        x_end = -4.4 + self.paragraph_width + 0.04 + (r['ordinary']['cap'] - sum(f['cost'] for f in r['ordinary']['facts'] if f['kind'] == 'text')) * self.scale
        names = VGroup(words('Ordinary', 26, ORD, weight='BOLD').move_to([-5.6, o_y, 0]), words('Dependency', 26, DEP, weight='BOLD').move_to([-5.6, d_y, 0]))
        cap_lines = VGroup(*[DashedLine([x_end, y + 0.55, 0], [x_end, y - 0.4, 0], color=INK, stroke_width=3) for y in (o_y, d_y)])
        cap_tag = words(f'budget {r["ordinary"]["cap"]}', 24, INK).move_to([x_end - 0.1, (o_y + d_y) / 2 + 0.05, 0], aligned_edge=RIGHT)
        source = words('TAT-QA dev set · Block A · gemini-3.5-flash-lite · blocks to scale, paragraphs shortened', 22, MUTED).to_edge(DOWN, buff=0.25)
        self.play(FadeIn(names), Create(cap_lines), FadeIn(cap_tag), FadeIn(source), run_time=1.0)

        # The question
        self.cue(1)
        question = words(f'"{r["question"]}"', 26, INK).move_to(2.65 * UP)
        self.play(FadeIn(question), run_time=0.8)

        # Same paragraphs in both lanes
        self.cue(2)
        o_para, o_cells = self.lane(r['ordinary']['facts'], o_y)
        d_para, d_cells = self.lane(r['dependency']['facts'], d_y)
        self.play(FadeIn(o_para), FadeIn(d_para), run_time=1.0)

        # Ordinary: three labelled cells, 398 tokens
        self.cue(3)
        o_used = words(f'{r["ordinary"]["used"]} tokens', 24, ORD, weight='BOLD').next_to(names[0], DOWN, buff=0.12)
        self.play(LaggedStart(*[FadeIn(c, shift=0.1 * RIGHT) for c in o_cells], lag_ratio=0.3), FadeIn(o_used), run_time=1.8)

        # 358 does not fit
        self.cue(4)
        need = r['missing_cell_ordinary_cost']
        left = r['ordinary']['cap'] - r['ordinary']['used']
        ghost = VGroup(Rectangle(width=need * self.scale, height=0.55, color=REJECT, stroke_width=3), words('358', 24, REJECT))
        ghost[1].move_to(ghost[0])
        ghost.move_to([x_end - ghost.width / 2, o_y + 1.0, 0])
        why = words(f'needs {need}, {left} left', 24, REJECT).next_to(ghost, LEFT, buff=0.2)
        self.play(FadeIn(ghost, shift=0.2 * DOWN), FadeIn(why), run_time=0.8)
        self.play(ghost.animate.shift(0.3 * DOWN), rate_func=there_and_back, run_time=0.6)

        # The model abstains
        self.cue(5)
        reply = card(stack('"The evidence does not contain data', 'for accrued compensation in 2018"  →  abstained, score 0', size=24), RULE, pad=0.12)
        reply.move_to([0.1, o_y - 0.98, 0])
        self.play(FadeIn(reply), run_time=0.8)

        # Dependency: labels once, 3 tokens per cell; 358 fits
        self.cue(6)
        d_used = words(f'{r["dependency"]["used"]} tokens', 24, DEP, weight='BOLD').next_to(names[1], DOWN, buff=0.12)
        self.play(LaggedStart(*[FadeIn(c, shift=0.1 * RIGHT) for c in d_cells], lag_ratio=0.15), FadeIn(d_used), run_time=2.0)
        labels = sum(f['cost'] for f in r['dependency']['facts'] if f['kind'] == 'header')
        note = words(f'labels, once: {labels} tokens   ·   cells: 3 tokens each', 24, MUTED).next_to(VGroup(d_para, d_cells), DOWN, buff=0.2)
        self.play(FadeIn(note), run_time=0.8)

        # The right answer
        self.cue(7)
        step = r['dependency']['steps'][0]
        answer = float(r['dependency']['answer'])
        result = card(words(f'divide("{step["a"]}", "{step["b"]}") = {answer:.2f}   ·   gold {r["gold"]}', 26, INK, weight='BOLD'), DEP, pad=0.15)
        result.next_to(note, DOWN, buff=0.2)
        self.play(FadeIn(result, shift=0.1 * UP), run_time=0.8)
        self.finish()


class Clip8Withdrawn(Narrated):
    clip = 'A result we withdrew'

    def bars(self, values, y0=-1.6, height=3.4):
        out = VGroup()
        for i, (name, color, v) in enumerate(values):
            bar = Rectangle(width=1.4, height=height * v, stroke_width=0).set_fill(color, 0.9)
            bar.move_to([-4.4 + 2.0 * i, y0 + height * v / 2, 0])
            out.add(VGroup(bar, words(f'{100 * v:.1f}', 28, color, weight='BOLD').next_to(bar, UP, buff=0.1),
                           words(name, 26, INK).next_to([bar.get_x(), y0, 0], DOWN, buff=0.15)))
        return out

    def construct(self):
        self.begin()
        self.title('A result we withdrew')
        w = EX['withdrawn']
        base = Line([-5.4, -1.6, 0], [-1.4, -1.6, 0], color=MUTED, stroke_width=2)
        official = self.bars([('executor', EXEC, w['official']['executor']), ('direct', DIRECT, w['official']['direct'])])
        gap = words(f'+{100 * (w["official"]["executor"] - w["official"]["direct"]):.1f}', 36, EXEC, weight='BOLD').move_to([-3.4, 2.3, 0])
        tag = words('MultiHiertt, Block B, official F1', 24, MUTED).next_to(base, DOWN, buff=0.75)
        self.play(Create(base), FadeIn(official), FadeIn(tag), run_time=1.2)
        self.play(FadeIn(gap), run_time=0.6)

        # Same value, two forms
        self.cue(1)
        gold = card(stack('gold answer', '-0.2992', size=30), MUTED).move_to([1.6, 1.5, 0])
        direct = card(stack('direct answer', '-29.92', size=30), DIRECT).next_to(gold, RIGHT, buff=0.5)
        same = words('same value, as a percentage', 24, MUTED).next_to(VGroup(gold, direct), DOWN, buff=0.2)
        self.play(FadeIn(gold), FadeIn(direct), FadeIn(same), run_time=1.0)

        # Text comparison marks it wrong
        self.cue(2)
        verdict = VGroup(words('compared as text  →  marked wrong', 26, REJECT),
                         words('executor programs: another path', 26, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        verdict.next_to(same, DOWN, buff=0.45).align_to(gold, LEFT)
        self.play(FadeIn(verdict[0]), run_time=0.8)
        self.play(FadeIn(verdict[1]), run_time=0.6)

        # One rule for both sides
        self.cue(3)
        relaxed = self.bars([('executor', EXEC, w['relaxed_numeric']['executor']), ('direct', DIRECT, w['relaxed_numeric']['direct'])])
        d, (lo, hi) = 100 * w['relaxed_diff'], (100 * w['relaxed_ci'][0], 100 * w['relaxed_ci'][1])
        new_gap = words(f'+{d:.1f}', 36, EXEC, weight='BOLD').move_to(gap)
        new_tag = words('MultiHiertt, Block B, one numeric rule for both', 24, MUTED).move_to(tag)
        self.play(*[Transform(a, b) for a, b in zip(official, relaxed)], Transform(gap, new_gap), Transform(tag, new_tag), run_time=1.5)
        line = NumberLine(x_range=[-10, 25, 5], length=4.6, color=MUTED).move_to([3.5, -2.1, 0])
        nums = VGroup(*[words(f'{v:+d}' if v else '0', 22, MUTED).next_to(line.n2p(v), DOWN, buff=0.1) for v in (-10, 0, 10, 20)])
        ci = VGroup(Line(line.n2p(lo) + 0.35 * UP, line.n2p(hi) + 0.35 * UP, color=EXEC, stroke_width=5),
                    Dot(line.n2p(d) + 0.35 * UP, radius=0.1, color=EXEC))
        zero = DashedLine(line.n2p(0) + 0.8 * UP, line.n2p(0), color=INK, stroke_width=2)
        ci_label = words(f'95% interval [{lo:+.1f}, {hi:+.1f}] includes 0', 24, INK).next_to(ci, UP, buff=0.2)
        self.play(Create(line), FadeIn(nums), Create(zero), Create(ci), FadeIn(ci_label), run_time=1.5)

        # Withdrawn
        self.cue(4)
        stamp = card(words('claim withdrawn', 36, REJECT, weight='BOLD'), REJECT, pad=0.2).rotate(0.12).move_to([-3.4, 0.2, 0])
        self.play(FadeIn(stamp, scale=1.3), run_time=0.6)
        self.finish()


class Clip0Reference(Narrated):
    """The reference study (Arun et al. 2023, arXiv:2312.14870); every number is quoted from that paper."""
    clip = 'The reference pipeline'

    def construct(self):
        self.begin()
        # The paper
        paper = VGroup(words('Numerical Reasoning for Financial Reports', 40, INK, weight='BOLD'),
                      words('Arun, Dhiman, Soni and Hu  ·  Georgia Tech  ·  2023', 28, INK),
                      words('arXiv:2312.14870', 24, MUTED)).arrange(DOWN, buff=0.3)
        self.play(FadeIn(paper, shift=0.15 * UP), run_time=1.0)

        # Five steps
        self.cue(1)
        self.play(FadeOut(paper), run_time=0.6)
        self.title('The reference study: five steps')
        names = [('Table', 'extraction'), ('Table-to-text', 'serialization'), ('Chunks +', 'FAISS search'),
                 ('Fine-tuned', 'T5 / Llama 2'), ('Regex', 'parsing')]
        stages = VGroup(*[card(stack(*n, size=24, buff=0.08), MUTED, pad=0.18) for n in names]).arrange(RIGHT, buff=0.42)
        stages.move_to(2.05 * UP)
        arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.05, color=MUTED, stroke_width=3) for a, b in zip(stages, stages[1:])])
        stages.set_opacity(0.3), arrows.set_opacity(0.3)
        figure = ImageMobject(str(ROOT / 'report/figures/reference_pipeline.png')).scale_to_fit_width(11.5).move_to(0.2 * DOWN)
        credit = words('their Figure 4, reproduced from Arun et al. (2023)', 22, MUTED).next_to(figure, DOWN, buff=0.25)
        self.play(FadeIn(figure), FadeIn(credit), run_time=1.0)
        self.cue(1, 0.9)
        self.play(FadeOut(figure), FadeOut(credit), FadeIn(stages), FadeIn(arrows), run_time=0.8)

        def light(i):
            return [stages[i].animate.set_opacity(1)] + ([arrows[i - 1].animate.set_opacity(1)] if i else [])

        # 1. Extract tables from the PDF
        self.cue(2)
        pages = VGroup(*[Rectangle(width=1.1, height=1.45, color=MUTED, stroke_width=2).set_fill(PAPER, 1) for _ in range(3)])
        for i, page in enumerate(pages):
            page.shift(0.12 * i * (RIGHT + DOWN))
            page.add(*[Line(LEFT * 0.38, RIGHT * 0.38, color=RULE, stroke_width=2).move_to(page).shift((0.45 - 0.18 * k) * UP) for k in range(6)])
        pages.move_to([-3.2, -0.9, 0])
        grid = VGroup(*[Rectangle(width=0.5, height=0.3, color=MUTED, stroke_width=1.5).set_fill(PAPER, 1) for _ in range(9)]).arrange_in_grid(3, 3, buff=0)
        grid.move_to([1.0, -0.9, 0])
        pdf = words('annual report PDF', 24, MUTED).next_to(pages, DOWN, buff=0.25)
        tab = words('tables (Tabula)', 24, MUTED).next_to(grid, DOWN, buff=0.25)
        pull = Arrow(pages.get_right(), grid.get_left(), buff=0.3, color=MUTED, stroke_width=3)
        self.play(*light(0), FadeIn(pages), FadeIn(pdf), run_time=0.8)
        self.play(GrowArrow(pull), FadeIn(grid), FadeIn(tab), run_time=1.0)

        # 2. Serialize each table into sentences (their Figure 6)
        self.cue(3)
        self.play(FadeOut(VGroup(pages, pdf, pull, grid, tab)), *light(1), run_time=0.6)
        rows = [['', '2019', '2020'], ['revenue', '100', '200'], ['cost', '50', '60']]
        table = VGroup(*[VGroup(*[VGroup(Rectangle(width=1.5, height=0.55, color=RULE, stroke_width=1.5).set_fill(PAPER, 1),
                                         words(v, 24, MUTED if r == 0 or c == 0 else INK)) for c, v in enumerate(row)]).arrange(RIGHT, buff=0)
                         for r, row in enumerate(rows)]).arrange(DOWN, buff=0)
        for row in table:
            for cell in row:
                cell[1].move_to(cell[0])
        table.move_to([-4.0, -0.9, 0])
        ROW_TEXT = '#9A6F00'
        sentences = VGroup()
        for r in (1, 2):
            for c in (1, 2):
                line = VGroup(words('the', 26, MUTED), words(rows[r][0], 26, ROW_TEXT, weight='BOLD'), words('of', 26, MUTED),
                              words(rows[0][c], 26, MUTED, weight='BOLD'), words('is', 26, MUTED), words(rows[r][c], 26, INK, weight='BOLD'))
                sentences.add(line.arrange(RIGHT, buff=0.14, aligned_edge=DOWN))
        sentences.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([2.6, -0.9, 0])
        arrow = Arrow(table.get_right(), sentences.get_left(), buff=0.3, color=MUTED, stroke_width=3)
        self.play(FadeIn(table), run_time=0.6)
        self.play(GrowArrow(arrow), LaggedStart(*[FadeIn(s, shift=0.1 * RIGHT) for s in sentences], lag_ratio=0.3), run_time=1.6)
        repeat = words('every number carries its row and column label', 24, ROW_TEXT).next_to(sentences, DOWN, buff=0.35)
        self.play(FadeIn(repeat), *[Indicate(s[1], color=FOCUS) for s in sentences], run_time=1.0)
        source = words('their Figure 6', 22, MUTED).next_to(table, DOWN, buff=0.2)
        self.play(FadeIn(source), run_time=0.4)

        # 3. Chunk and keep the closest chunk
        self.cue(4)
        self.play(FadeOut(VGroup(table, sentences, arrow, repeat, source)), *light(2), run_time=0.6)
        chunks = VGroup(*[Rectangle(width=1.4, height=1.6, color=MUTED, stroke_width=2).set_fill(PAPER, 1) for _ in range(6)]).arrange(RIGHT, buff=0.3)
        for ch in chunks:
            ch.add(*[Line(LEFT * 0.5, RIGHT * 0.5, color=RULE, stroke_width=2).move_to(ch).shift((0.5 - 0.2 * k) * UP) for k in range(6)])
        chunks.move_to([0, -0.8, 0])
        query = words('question', 24, INK).next_to(chunks, UP, buff=0.3)
        self.play(FadeIn(chunks), FadeIn(query), run_time=0.8)
        best = chunks[3]
        ring = SurroundingRectangle(best, color=FOCUS, buff=0.06, stroke_width=5)
        self.play(*[c.animate.set_opacity(0.25) for c in chunks if c is not best], Create(ring), run_time=1.0)
        kept = words('one chunk reaches the model', 24, INK).next_to(chunks, DOWN, buff=0.3)
        self.play(FadeIn(kept), run_time=0.6)

        # 4-5. The model writes steps; regex parses them (their Figure 8)
        self.cue(5)
        self.play(FadeOut(VGroup(chunks, query, ring, kept)), *light(3), run_time=0.6)
        output = words('Step 1: Divide 16944 by 181612. This gives the result: 9.49%', 26, INK).move_to([0, -0.2, 0])
        self.play(Write(output), run_time=1.4)
        self.cue(5, 0.55)
        parsed = VGroup(*[card(words(t, 26, c), RULE, pad=0.12) for t, c in (('divide', INK), ('16944', INK), ('181612', INK), ('9.49%', REJECT))]).arrange(RIGHT, buff=0.7)
        parsed.next_to(output, DOWN, buff=0.5)
        heads = VGroup(*[words(t, 22, MUTED).next_to(p, DOWN, buff=0.1) for t, p in zip(('operator', 'argument 1', 'argument 2', 'result'), parsed)])
        self.play(*light(4), FadeIn(parsed, shift=0.1 * DOWN), FadeIn(heads), run_time=1.0)
        truth = words('a calculator gives 16944 ÷ 181612 = 9.33%   (their Figure 8)', 24, MUTED).next_to(heads, DOWN, buff=0.35)
        self.play(FadeIn(truth), run_time=0.6)

        # The crux: their Table 4
        self.cue(6)
        self.play(FadeOut(VGroup(output, parsed, heads, truth)), run_time=0.6)
        crux = words('The crux: what fine-tuned T5 gets right (their Table 4, FinQA)', 28, INK, weight='BOLD').move_to(0.85 * UP)
        self.play(FadeIn(crux), run_time=0.6)
        self.cue(7)
        metrics = [('operator', 94.9), ('argument 1', 63.9), ('argument 2', 70.4), ('result, its own arithmetic', 11.8)]
        x0, unit = -1.0, 0.065
        bars = VGroup()
        for i, (name, v) in enumerate(metrics):
            y = 0.1 - 0.62 * i
            color = REJECT if i == 3 else INK
            bar = Rectangle(width=v * unit, height=0.4, stroke_width=0).set_fill(color, 0.85).move_to([x0 + v * unit / 2, y, 0])
            bars.add(VGroup(words(name, 26, INK).move_to([x0 - 0.3, y, 0], aligned_edge=RIGHT), bar,
                            words(f'{v:.1f}%', 26, color, weight='BOLD').next_to(bar, RIGHT, buff=0.15)))
        self.play(LaggedStart(*[FadeIn(b, shift=0.1 * RIGHT) for b in bars], lag_ratio=0.25), run_time=2.0)

        # A calculator fixes the arithmetic
        self.cue(8)
        y = bars[3][1].get_y()
        fixed = Rectangle(width=62.3 * unit, height=0.4, stroke_width=0).set_fill(INK, 0.85).move_to([x0 + 62.3 * unit / 2, y, 0])
        new_name = words('result, with a calculator', 26, INK).move_to([x0 - 0.3, y, 0], aligned_edge=RIGHT)
        new_value = words('62.3%', 26, INK, weight='BOLD').next_to(fixed, RIGHT, buff=0.15)
        self.play(Transform(bars[3][1], fixed), Transform(bars[3][0], new_name), Transform(bars[3][2], new_value), run_time=1.5)
        note = words('answers with the right number of steps; a result within 10% counts as right', 22, MUTED).next_to(bars, DOWN, buff=0.35)
        self.play(FadeIn(note), run_time=0.6)

        # Where our project starts
        self.cue(9)
        self.play(FadeOut(VGroup(crux, bars, note)), stages.animate.set_opacity(0.3), arrows.animate.set_opacity(0.3), run_time=0.8)
        heading = words('their choice', 26, MUTED).move_to([-0.9, 0.85, 0], aligned_edge=RIGHT)
        ours = words('in our project', 26, MUTED).move_to([0.9, 0.85, 0], aligned_edge=LEFT)
        self.play(FadeIn(heading), FadeIn(ours), run_time=0.6)
        pairs = [(1, 'labels repeated in every sentence', 'Ordinary packing, our baseline', ORD),
                 (2, 'one chunk reaches the model', 'a fixed evidence budget', INK),
                 (4, 'a calculator does the arithmetic', 'copy, check, then execute', INK)]
        for k, (stage, theirs, mine, color) in enumerate(pairs):
            self.cue(10 + k)
            y = 0.1 - 1.0 * k
            left = words(theirs, 28, INK).move_to([-0.9, y, 0], aligned_edge=RIGHT)
            right = words(mine, 28, color, weight='BOLD').move_to([0.9, y, 0], aligned_edge=LEFT)
            link = Arrow(left.get_right(), right.get_left(), buff=0.25, color=MUTED, stroke_width=3)
            self.play(stages[stage].animate.set_opacity(1), FadeIn(left), run_time=0.6)
            self.play(GrowArrow(link), FadeIn(right, shift=0.1 * RIGHT), run_time=0.8)
        self.finish()


class ClipGraph(Narrated):
    """Our idea on the Visa row: cells become facts, labels become shared nodes, packing walks the arrows."""
    clip = 'Our idea: a graph of labels'

    def node(self, text, color=INK, fill=PAPER, size=24):
        label = stack(*text.split('\n'), size=size, color=color, buff=0.04)
        box = RoundedRectangle(corner_radius=0.1, width=label.width + 0.3, height=label.height + 0.25,
                               color=MUTED, stroke_width=2).set_fill(fill, 1)
        return VGroup(box, label.move_to(box))

    def construct(self):
        self.begin()
        self.title('Our idea: a graph of labels')
        visa = EX['visa']
        table = visa_table(rows=[3]).scale(0.85).move_to(2.1 * UP)
        self.play(FadeIn(table), run_time=1.0)

        # Cells and labels become facts
        self.cue(1)
        short = {'payments volume ( billions )': 'payments\nvolume', 'total volume ( billions )': 'total\nvolume',
                 'total transactions ( billions )': 'total\ntransactions', 'cards ( millions )': 'cards'}
        values = ['637', '647', '5.0', '86']
        xs = [-5.4, -3.6, -1.8, -0.1]
        headers = VGroup(*[self.node(short[visa['headers'][v][0]], MUTED, '#EEF0F2').move_to([x, 1.0, 0]) for v, x in zip(values, xs)])
        facts = VGroup(*[self.node(v, INK, size=28).move_to([x, -0.45, 0]) for v, x in zip(values, xs)])
        row = self.node('american express', INK, '#F6E7B8').move_to([-2.75, -1.95, 0])
        self.play(*[ReplacementTransform(table[0][c + 1].copy(), headers[c]) for c in range(4)],
                  *[ReplacementTransform(table[1][c + 1].copy(), facts[c]) for c in range(4)],
                  ReplacementTransform(table[1][0].copy(), row), FadeOut(table), run_time=1.8)

        # Arrows to the labels each number needs
        self.cue(2)
        up = VGroup(*[Arrow(f.get_top(), h.get_bottom(), buff=0.06, color=MUTED, stroke_width=3) for f, h in zip(facts, headers)])
        down = VGroup(*[Arrow(f.get_bottom(), row.get_top(), buff=0.06, color=MUTED, stroke_width=3) for f in facts])
        self.play(LaggedStart(*[GrowArrow(a) for a in up], lag_ratio=0.15), run_time=1.2)
        self.play(LaggedStart(*[GrowArrow(a) for a in down], lag_ratio=0.15), run_time=1.2)

        # One shared row label
        self.cue(3)
        self.play(Indicate(row, color=FOCUS, scale_factor=1.12), *[a.animate.set_color(FOCUS) for a in down], run_time=1.2)
        self.play(*[a.animate.set_color(MUTED) for a in down], run_time=0.5)

        # The panel: what gets packed, and what it costs
        self.cue(4)
        meter_title = words('packed evidence', 24, MUTED).move_to([3.9, 1.35, 0])
        meter = words('0 tokens', 30, DEP, weight='BOLD').next_to(meter_title, DOWN, buff=0.2)
        question = words('question → retriever ranks 637 first', 24, INK).move_to([3.9, 2.55 - 0.25, 0])
        self.play(FadeIn(meter_title), FadeIn(meter), FadeIn(question), run_time=0.8)
        self.play(Circumscribe(facts[0], color=FOCUS, buff=0.08), run_time=0.8)

        # Pack in rank order; each label enters once
        index = {v: i for i, v in enumerate(values)}
        bundle = {f['value']: sum(f['parts']) for f in visa['dependency']}
        totals = [sum(bundle[v] for v in visa['row_rank'][:k + 1]) for k in range(len(visa['row_rank']))]
        packed_row, log = False, VGroup()
        for k, value in enumerate(visa['row_rank']):
            self.cue(5 + min(k, 2))
            i = index[value]
            new = ['its column header'] + ([] if packed_row else ['the row label'])
            parts = [facts[i], headers[i], up[i], down[i]] + ([] if packed_row else [row])
            self.play(facts[i][0].animate.set_fill(DEP, 0.25).set_stroke(DEP, 3),
                      headers[i][0].animate.set_stroke(DEP, 3),
                      *([row[0].animate.set_stroke(DEP, 3)] if not packed_row else []),
                      up[i].animate.set_color(DEP), down[i].animate.set_color(DEP), run_time=0.7)
            line = words(f'{value} + {len(new)} new label{"s" if len(new) > 1 else ""}', 24, INK)
            cost = words(str(totals[k]), 24, DEP, weight='BOLD')
            entry = VGroup(line, cost).arrange(RIGHT, buff=0.35)
            entry.next_to(log if len(log) else meter, DOWN, buff=0.28 if len(log) else 0.4).align_to(meter_title, LEFT).shift(0.0 * RIGHT)
            log.add(entry)
            self.play(FadeIn(entry, shift=0.1 * DOWN), Transform(meter, words(f'{totals[k]} tokens', 30, DEP, weight='BOLD').move_to(meter)), run_time=0.7)
            packed_row = True

        # Each label once
        self.cue(8)
        self.play(Indicate(row, color=DEP, scale_factor=1.1), run_time=1.0)

        # Ordinary would repeat the row label
        self.cue(9)
        ordinary = VGroup(words('ordinary: american express', 24, ORD), words(f'written 4 times → {visa["cumulative"]["ordinary"][-1]} tokens', 24, ORD, weight='BOLD')).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        ordinary.next_to(log, DOWN, buff=0.45).align_to(meter_title, LEFT)
        self.play(FadeIn(ordinary), run_time=0.8)

        # What the model receives
        self.cue(10)
        received = visa_table(rows=[3]).scale(0.8).move_to(0.2 * DOWN)
        caption = words(f'{totals[-1]} tokens, every number readable', 28, DEP, weight='BOLD').next_to(received, DOWN, buff=0.4)
        graph = VGroup(headers, facts, row, up, down, log, meter, meter_title, question, ordinary)
        self.play(FadeOut(graph), run_time=0.8)
        self.play(FadeIn(received, shift=0.1 * UP), FadeIn(caption), run_time=1.0)
        self.finish()


class ClipSpark(Narrated):
    """The PySpark data layer, on real counts from artifacts/v11/report_numbers.json."""
    clip = 'Inside PySpark'

    def table_card(self, name, columns, count, color=INK):
        head = words(name, 26, color, weight='BOLD')
        cols = VGroup(*[words(c, 22, MUTED) for c in columns]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        n = words(f'{count:,} rows', 24, INK)
        body = VGroup(head, cols, n).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        return card(body, color, pad=0.2)

    def construct(self):
        self.begin()
        self.title('Inside PySpark: what happens to the data')
        sp = NUMBERS['spark']['full']

        # Six sources, six shapes
        self.cue(1)
        sources = VGroup(*[card(words(t, 24, INK), RULE, pad=0.12) for t in (
            'FinQA · JSON', 'TAT-QA · JSON', 'TAT-HQA · JSON', 'ConvFinQA · zip', 'MultiHiertt · HTML', 'HybridQA · 15,314 linked tables')])
        sources.arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([-4.35, -0.4, 0])
        self.play(LaggedStart(*[FadeIn(s, shift=0.1 * RIGHT) for s in sources], lag_ratio=0.15), run_time=1.6)

        # Three tables
        self.cue(2)
        tables = VGroup(self.table_card('documents', ['document_id', 'dataset, split', 'content_hash'], sp['documents']),
                        self.table_card('questions', ['id', 'document_id', 'question_hash'], sp['questions']),
                        self.table_card('facts', ['id, raw text', 'dependencies [ ]', 'dataset, split'], sp['facts'], DEP)).arrange(RIGHT, buff=0.35)
        tables.scale(0.9).move_to([2.95, -0.4, 0])
        readers = Arrow(sources.get_right(), tables.get_left(), buff=0.2, color=MUTED, stroke_width=3)
        tag = stack('Python', 'readers', size=22, color=MUTED, buff=0.04).next_to(readers, UP, buff=0.12)
        self.play(GrowArrow(readers), FadeIn(tag), LaggedStart(*[FadeIn(t) for t in tables], lag_ratio=0.25), run_time=1.6)

        # A fact keeps its labels as an array
        self.cue(3)
        self.play(FadeOut(VGroup(sources, readers, tag, tables[0], tables[1])), tables[2].animate.move_to([-5.4, 0.6, 0]), run_time=1.0)
        visa = EX['visa']
        deps = visa['headers']['637']
        fact_row = card(words(f'fact 637   dependencies = [ {deps[0].replace(" ( billions )", "")}, {deps[1]} ]', 22, INK), DEP, pad=0.15)
        fact_row.move_to([1.35, 0.6, 0])
        self.play(FadeIn(fact_row, shift=0.1 * LEFT), run_time=1.0)

        # DataFrames
        self.cue(4)
        df = card(words('PySpark DataFrames  ·  Spark SQL  ·  local[4]', 26, INK, weight='BOLD'), INK, pad=0.15).move_to(2.55 * UP)
        self.play(FadeIn(df), run_time=0.8)

        # explode: one row per arrow
        self.cue(5)
        rows = VGroup(*[card(words(f'637  →  {d}', 24, INK), MUTED, pad=0.12) for d in deps]).arrange(DOWN, buff=0.15)
        rows.move_to([1.35, -0.9, 0])
        explode = words('explode(dependencies)', 24, DEP, weight='BOLD').next_to(rows, LEFT, buff=0.5)
        self.play(*[TransformFromCopy(fact_row, r) for r in rows], FadeIn(explode), run_time=1.4)
        edges = words(f'{sp["edges"]:,} edge rows', 30, INK, weight='BOLD').next_to(rows, DOWN, buff=0.35)
        self.play(FadeIn(edges), run_time=0.6)

        # anti-join: every arrow must point to a real fact
        self.cue(6)
        self.play(FadeOut(VGroup(tables[2], fact_row, explode)), VGroup(rows, edges).animate.move_to([-3.6, 0.3, 0]), run_time=0.8)
        anti = VGroup(words('edges  left_anti join  facts', 26, INK), words(f'unresolved edges: {sp["unresolved"]}', 30, LEN if sp['unresolved'] == 0 else REJECT, weight='BOLD')).arrange(DOWN, buff=0.2)
        anti.move_to([3.2, 0.3, 0])
        self.play(FadeIn(anti, shift=0.1 * LEFT), run_time=1.0)

        # self-join on content hash: identical documents
        self.cue(7)
        self.play(FadeOut(VGroup(rows, edges, anti)), run_time=0.6)
        docs = VGroup(card(stack('a FinQA document', 'content_hash 7c1e…', size=24), MUTED), card(stack('a ConvFinQA document', 'content_hash 7c1e…', size=24), MUTED)).arrange(RIGHT, buff=2.2)
        docs.move_to(0.4 * UP)
        link = DoubleArrow(docs[0].get_right(), docs[1].get_left(), buff=0.1, color=FOCUS, stroke_width=4)
        same = words('self-join on content_hash', 24, INK).next_to(docs, UP, buff=0.3)
        pairs = words(f'{sp["overlap"]} pairs of identical documents  →  related datasets are never pooled', 26, INK, weight='BOLD').next_to(docs, DOWN, buff=0.5)
        hash_note = words('(hash shortened for illustration)', 20, MUTED).next_to(link, DOWN, buff=0.6)
        self.play(FadeIn(docs), run_time=0.8)
        self.play(GrowArrow(link), FadeIn(same), FadeIn(hash_note), run_time=0.8)
        self.play(FadeIn(pairs), run_time=0.8)

        # Parquet, partitioned
        self.cue(8)
        self.play(FadeOut(VGroup(docs, link, same, pairs, hash_note)), run_time=0.6)
        tree = VGroup(*[words(t, 24, INK if i == 0 else MUTED) for i, t in enumerate((
            'parquet/facts/', '  dataset=finqa/split=dev/part-….parquet', '  dataset=hybridqa/split=dev/part-….parquet', '  …  six datasets'))]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        tree.move_to([-3.0, 0.2, 0])
        unit = 3.6
        sizes = VGroup()
        for i, (name, gb, color) in enumerate((('JSON lines', sp['jsonl_gb'], MUTED), ('Parquet', sp['parquet_gb'], DEP))):
            bar = Rectangle(width=gb * unit, height=0.45, stroke_width=0).set_fill(color, 0.9)
            bar.move_to([1.6 + gb * unit / 2, 0.7 - 1.1 * i, 0])
            sizes.add(VGroup(bar, words(name, 24, INK).next_to(bar, UP, buff=0.08).align_to(bar, LEFT),
                             words(f'{gb:.2f} GB', 24, color, weight='BOLD').next_to(bar, RIGHT, buff=0.15)))
        self.play(FadeIn(tree), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(s, shift=0.1 * RIGHT) for s in sizes], lag_ratio=0.3), run_time=1.0)

        # Must equal Python
        self.cue(9)
        check = card(words('Spark result  =  independent Python result   ✓', 30, INK, weight='BOLD'), LEN, pad=0.2).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(check, shift=0.1 * UP), run_time=0.8)
        self.finish()


class ClipConclusion(Narrated):
    """Closing summary: problem, reference, our method, PySpark, results."""
    clip = 'Conclusion'

    def construct(self):
        self.begin()
        self.title('Conclusion')
        rows = [('The problem', 'large tables, a fixed context window;\nnumbers without labels mean nothing', INK),
                ('The reference study', 'kept labels by repeating them with every number:\n4 to 8 times the tokens per cell', ORD),
                ('Our method', 'each label written once, every number linked to it:\na dependency graph packed under the budget', DEP),
                ('Big Data', f'PySpark builds and verifies {NUMBERS["spark"]["full"]["facts"]:,} facts\nand {NUMBERS["spark"]["full"]["edges"]:,} label links', INK),
                ('The result', 'more needed evidence survives on all six datasets;\nGemini 3.5 Flash-Lite answers at least as well,\nclearly better on TAT-QA', DEP)]
        group = VGroup()
        for i, (head, body, color) in enumerate(rows):
            h = words(head, 28, color, weight='BOLD').move_to([-2.9, 2.2 - 1.05 * i, 0], aligned_edge=RIGHT)
            b = VGroup(*[words(t, 24, INK) for t in body.split('\n')]).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
            b.next_to(h, RIGHT, buff=0.5)
            b.align_to(h, UP).shift(0.03 * DOWN)
            group.add(VGroup(h, b))
        for i, item in enumerate(group):
            self.cue(i + 1)
            self.play(FadeIn(item, shift=0.1 * RIGHT), run_time=0.8)
        self.finish()
