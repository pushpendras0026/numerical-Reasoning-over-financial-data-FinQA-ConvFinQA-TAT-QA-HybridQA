"""Explainer video: the problem, the pipeline, and the main result.

Render: /Users/mac/CourseWork/BigDataProject/.manim/bin/manim -qh explainer.py Explainer

The narration lives in ../speaker_notes.md (Part 1 table). Each scene below is timed
against it: every sentence is a cue at ~140 spoken words per minute, and each scene
ends 2 s after its last sentence. Edit the narration there, not here.
Every number on screen is read from artifacts/v11/*.json or from the FinQA table.
"""
import json
import re
from pathlib import Path

from manim import (DOWN, LEFT, ORIGIN, RIGHT, UP, UL, Arrow, Axes, Create, Cross, DashedLine,
                   Dot, FadeIn, FadeOut, FadeTransform, LaggedStart, Line, Rectangle,
                   ReplacementTransform, RoundedRectangle, Scene, SurroundingRectangle, Text,
                   VGroup, Write, config)

ROOT = Path(__file__).resolve().parents[2]
COVERAGE = json.loads((ROOT / 'artifacts/v11/coverage.json').read_text())
NUMBERS = json.loads((ROOT / 'artifacts/v11/report_numbers.json').read_text())
SIZES = json.loads((ROOT / 'artifacts/v11/document_sizes.json').read_text())
LEAK_CHECKED_PROMPTS = 443  # paper, Section 3; no artifact in the repo records this count
NOTES = ROOT / 'presentation/speaker_notes.md'

config.background_color = '#FCFCFB'
INK, MUTED, RULE, PAPER = '#1F2328', '#5E6168', '#D9D7D0', '#FFFFFF'
# Colour is meaning, fixed for the whole video.
ORD, DEP, LEN = '#2A78D6', '#EB6834', '#1BAF7A'  # the three packing methods, nothing else
FOCUS = '#E3A600'                               # what to look at now (fills and rings only)
REJECT = '#C8323C'                              # a value the checker could not find
FONT = 'Helvetica Neue'
WPM, AIR = 140, 2.0


def narration():
    """Scene name -> list of sentences, from the Part 1 table in speaker_notes.md."""
    scenes = {}
    for line in NOTES.read_text().splitlines():
        cols = [c.strip() for c in line.split('|')]
        if len(cols) == 5 and '"' in cols[3]:
            say = ' '.join(re.findall(r'"([^"]*)"', cols[3]))
            scenes[cols[1]] = re.split(r'(?<=[.?!])\s+', say)
    return scenes


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


def lines(*texts, size=28, color=INK, buff=0.18, **kw):
    return VGroup(*[words(t, size, color, **kw) for t in texts]).arrange(DOWN, buff=buff)


TABLE = [['company', 'payments vol. (bn)', 'transactions (bn)'],
         ['visa inc.', '$ 2457', '50.3'],
         ['mastercard', '1697', '27.0'],
         ['american express', '637', '5.0'],
         ['discover', '102', '1.6']]


def table():
    widths = [3.0, 3.0, 2.8]
    rows = VGroup()
    for r, row in enumerate(TABLE):
        cells = VGroup()
        for c, value in enumerate(row):
            frame = Rectangle(width=widths[c], height=0.62, color=RULE, stroke_width=1.5).set_fill(PAPER, 1)
            cells.add(VGroup(frame, words(value, 24, MUTED if r == 0 else INK).move_to(frame)))
        rows.add(cells.arrange(RIGHT, buff=0))
    return rows.arrange(DOWN, buff=0)


class Explainer(Scene):
    # Timing against the narration
    def begin(self, scene, lead=0.0):
        self.name, self.t0 = scene, self.renderer.time
        self.starts, t = [], lead
        for sentence in NARRATION[scene]:
            self.starts.append(t)
            t += spoken_seconds(sentence)
        self.starts.append(t)
        self.end_at = t + AIR

    def until(self, t):
        dt = self.t0 + t - self.renderer.time
        if dt > 1 / 30:
            self.wait(dt)
        elif dt < -0.3:
            print(f'[timing] {self.name}: cue at {t:.1f}s overran by {-dt:.1f}s', flush=True)

    def cue(self, i, frac=0.0):
        """Wait until sentence i (plus a fraction of its length) is being spoken."""
        self.until(self.starts[i] + frac * (self.starts[i + 1] - self.starts[i]))

    def finish(self, clear=True):
        self.until(self.end_at)
        print(f'[timing] {self.name}: {self.renderer.time - self.t0:.1f}s', flush=True)
        if clear:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
            self.wait(0.2)

    def title(self, text):
        heading = words(text, 32, INK, weight='BOLD').to_corner(UL).shift(0.15 * DOWN)
        self.play(FadeIn(heading, shift=0.2 * DOWN), run_time=0.8)
        return heading

    def construct(self):
        self.opening()
        self.problem()
        self.budget()
        self.pipeline()
        self.packing()
        self.grounding()
        self.results()
        self.closing()

    def opening(self):
        # Title card (silent)
        card = VGroup(lines('Dependency-Preserving Evidence Packing', 'for Numerical Question Answering',
                            size=40, weight='BOLD', buff=0.2),
                      words('Pushpendra Singh  ·  Badri Bishal Das', 30, INK),
                      words('Indian Institute of Technology Guwahati', 26, MUTED)).arrange(DOWN, buff=0.4)
        self.begin('Opening', lead=5.8)
        self.play(FadeIn(card, shift=0.15 * UP), run_time=1.0)
        self.wait(4.0)
        self.play(FadeOut(card), run_time=0.8)

        # A number means nothing on its own
        self.cue(0)
        quote = VGroup(words('A number in a financial report', 44),
                       words('means nothing on its own.', 44, weight='BOLD')).arrange(DOWN, buff=0.3)
        self.play(Write(quote[0]), run_time=1.5)
        self.play(Write(quote[1]), run_time=1.5)

        # Pose the question
        self.cue(1, 0.3)
        question = words('What happens when a model gets numbers without their labels?', 28, MUTED)
        question.next_to(quote, DOWN, buff=0.6)
        self.play(FadeIn(question, shift=0.1 * UP), run_time=1.0)
        self.finish()

    def problem(self):
        self.begin('What does 637 mean?')
        self.title('What does "637" mean?')
        grid = table().shift(0.25 * DOWN)
        self.play(LaggedStart(*[FadeIn(row, shift=0.1 * UP) for row in grid], lag_ratio=0.15), run_time=1.5)

        # The question
        self.cue(1)
        question = words('"Average payment volume per transaction for American Express?"', 24, MUTED)
        question.next_to(grid, DOWN, buff=0.4)
        self.play(FadeIn(question), run_time=1.0)

        # The two values, then the three labels that make them usable
        self.cue(2)
        target = VGroup(grid[3][1], grid[3][2])
        self.play(*[cell[0].animate.set_fill(FOCUS, 0.35) for cell in target], run_time=1.0)
        self.cue(2, 0.6)
        labels = VGroup(grid[3][0], grid[0][1], grid[0][2])
        self.play(LaggedStart(*[cell[0].animate.set_fill(FOCUS, 0.15).set_stroke(FOCUS, 3) for cell in labels],
                              lag_ratio=0.4), run_time=1.5)

        # Remove the labels
        self.cue(3)
        others = [cell for row in grid for cell in row if cell not in target]
        self.play(*[FadeOut(cell) for cell in others], FadeOut(question), run_time=1.2)
        self.play(target.animate.scale(1.25).move_to(0.6 * UP), run_time=1.0)

        # Which is which?
        self.cue(4)
        marks = VGroup(*[words('?', 40, MUTED).next_to(cell, UP, buff=0.25) for cell in target])
        lost = lines('Without its row and column labels,', 'the model cannot tell 637 from 5.0.', size=30)
        lost.next_to(target, DOWN, buff=0.8)
        self.play(FadeIn(marks, shift=0.1 * DOWN), Write(lost), run_time=1.8)
        self.finish()

    def budget(self):
        self.begin('Reading budget')
        self.title('The model can only read part of the document')
        facts = VGroup(*[RoundedRectangle(corner_radius=0.05, width=0.5, height=0.3, color=RULE, stroke_width=1)
                         .set_fill(PAPER, 1) for _ in range(96)])
        facts.arrange_in_grid(rows=8, cols=12, buff=0.08).move_to(2.1 * LEFT + 0.25 * DOWN)
        self.play(LaggedStart(*[FadeIn(f) for f in facts], lag_ratio=0.01), run_time=1.5)

        # Document size against the budget, drawn to scale
        self.cue(1)
        median = round(SIZES['hybridqa']['median_tokens'], -2)  # 8,928 -> 8,900
        doc_label = words(f'HybridQA: median document ≈ {median:,.0f} tokens', 24, MUTED).next_to(facts, UP, buff=0.3)
        scale_note = words('each square ≈ 90 tokens', 24, MUTED).next_to(facts, DOWN, buff=0.3)
        self.play(FadeIn(doc_label), FadeIn(scale_note), run_time=1.0)
        self.cue(1, 0.6)
        window = RoundedRectangle(corner_radius=0.12, width=2.9, height=2.2, color=INK, stroke_width=4)
        window.next_to(facts, RIGHT, buff=1.0)
        budget = words('budget: 1,500 tokens', 24, INK).next_to(window, UP, buff=0.3)
        self.play(Create(window), FadeIn(budget), run_time=1.2)

        # Some facts go in (1,500 / 8,900 of 96 squares is 16)
        self.cue(2)
        chosen = VGroup(*[facts[i] for i in (2, 9, 14, 21, 27, 33, 40, 46, 52, 57, 63, 70, 75, 81, 88, 93)])
        copies = chosen.copy()
        self.play(chosen.animate.set_fill(FOCUS, 0.2),
                  copies.animate.arrange_in_grid(rows=4, cols=4, buff=0.12).move_to(window).set_fill(FOCUS, 0.5),
                  run_time=1.8)

        # The question
        self.cue(3)
        point = words('Which facts go in, and do their labels come with them?', 30, INK).to_edge(DOWN, buff=0.45)
        self.play(Write(point), run_time=1.5)
        self.finish()

    def pipeline(self):
        self.begin('Pipeline')
        self.title('One pipeline for six datasets')
        names = ['Reader', 'BM25', 'Packing', 'Model', 'Grounding', 'Executor', 'Scorer']
        stages = VGroup()
        for name in names:
            label = words(name, 24, INK)
            frame = RoundedRectangle(corner_radius=0.12, width=label.width + 0.4, height=0.85, color=MUTED, stroke_width=2.5)
            stages.add(VGroup(frame.set_fill(PAPER, 1), label.move_to(frame)))
        stages.arrange(RIGHT, buff=0.38).move_to(0.6 * UP)
        if stages.width > 13.0:
            stages.scale_to_fit_width(13.0)
        arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.04, color=MUTED, stroke_width=3,
                                max_tip_length_to_length_ratio=0.4) for a, b in zip(stages, stages[1:])])
        for stage in stages:
            stage.set_opacity(0.25)
        arrows.set_opacity(0.25)
        self.play(FadeIn(stages), FadeIn(arrows), run_time=1.0)

        def light(*indices):
            return [stages[i].animate.set_opacity(1) for i in indices] + \
                   [arrows[i - 1].animate.set_opacity(1) for i in indices if i > 0]

        # The reader: facts that remember what explains them
        self.cue(1)
        caption = words('each fact stores the IDs of the facts that explain it', 26, MUTED)
        caption.next_to(stages, DOWN, buff=0.6)
        self.play(*light(0), FadeIn(caption), run_time=0.8)

        # Retrieval, packing, one model call, checks, official scorer
        for frac, indices in ((0.0, (1,)), (0.2, (2,)), (0.4, (3,)), (0.65, (4, 5)), (0.9, (6,))):
            self.cue(2, frac)
            self.play(*light(*indices), *([FadeOut(caption)] if indices == (1,) else []), run_time=0.6)

        # The one thing that changes
        self.cue(3)
        tag = words('the only thing we change', 26, INK).next_to(stages[2], UP, buff=0.35)
        self.play(stages[2][0].animate.set_stroke(FOCUS, 5), FadeIn(tag, shift=0.1 * DOWN), run_time=1.0)

        # Gold answers stay out until scoring
        self.cue(4)
        gold = VGroup(RoundedRectangle(corner_radius=0.12, width=2.6, height=0.8, color=MUTED, stroke_width=2.5)
                      .set_fill(PAPER, 1), words('Gold answers', 24, INK))
        gold[1].move_to(gold[0])
        gold.next_to(stages[0], DOWN, buff=1.4).align_to(stages[0], LEFT)
        corner = [stages[6].get_bottom()[0], gold.get_right()[1], 0]
        path = VGroup(DashedLine(gold.get_right(), corner, color=MUTED),
                      Arrow(corner, stages[6].get_bottom(), buff=0, color=MUTED, stroke_width=3))
        self.play(FadeIn(gold), Create(path), run_time=1.5)
        note = words(f'Checked: 0 of {LEAK_CHECKED_PROMPTS} saved prompts contain a gold label field.', 24, MUTED)
        note.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note), run_time=1.0)
        self.finish()

    def packing(self):
        self.begin('Three packing methods')
        self.title('Same budget, three ways to fill it')
        specs = [('Ordinary', ORD, ['amex | volume | 637', 'amex | count | 5.0'], 'labels in every cell'),
                 ('Dependency', DEP, ['company | volume | count', 'amex | 637 | 5.0'], 'labels once, structured'),
                 ('Length-matched', LEN, ['637   5.0', '1697   27.0   102   1.6'], 'neighbours, same length')]
        columns = VGroup()
        for name, color, content, caption in specs:
            frame = RoundedRectangle(corner_radius=0.12, width=4.2, height=2.2, color=RULE, stroke_width=3)
            body = VGroup(*[words(t, 24, INK) for t in content]).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            columns.add(VGroup(words(name, 30, color, weight='BOLD'), VGroup(frame, body.move_to(frame)),
                               words(caption, 24, MUTED)).arrange(DOWN, buff=0.3))
        columns.arrange(RIGHT, buff=0.25).shift(0.2 * DOWN)
        # Three empty boxes of the same size: the same budget
        self.play(LaggedStart(*[Create(col[1][0]) for col in columns], lag_ratio=0.2), run_time=1.2)

        for i, (col, (_, color, _, _)) in enumerate(zip(columns, specs)):
            self.cue(i + 1)
            self.play(FadeIn(col[0]), col[1][0].animate.set_stroke(color, 3), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(t, shift=0.1 * RIGHT) for t in col[1][1]], lag_ratio=0.3), run_time=1.0)
            self.play(FadeIn(col[2]), run_time=0.5)
        self.finish()

    def grounding(self):
        self.begin('Literal grounding')
        self.title('The model copies values; code checks them')
        plan = words('divide("637", "5.0")', 40, INK).move_to(2.25 * UP)
        literal_a, literal_b = plan[8:11], plan[14:17]
        grid = table().move_to(0.95 * DOWN)
        self.play(Write(plan), run_time=1.2)
        self.play(FadeIn(grid), run_time=0.8)

        # Find each literal in the evidence
        self.cue(1)
        cell_a, cell_b = grid[3][1], grid[3][2]
        context = [c for row in grid for c in row if c not in (cell_a, cell_b)]
        self.play(*[c.animate.set_opacity(0.3) for c in context], run_time=0.6)
        rings = VGroup()
        for literal, cell in ((literal_a, cell_a), (literal_b, cell_b)):
            pair = VGroup(SurroundingRectangle(literal, color=FOCUS, buff=0.08, stroke_width=4),
                          SurroundingRectangle(cell, color=FOCUS, buff=0.02, stroke_width=4))
            flying = literal.copy()
            self.play(Create(pair[0]), run_time=0.5)
            self.play(flying.animate.move_to(cell[1]).scale(0.6).set_opacity(0), Create(pair[1]), run_time=0.9)
            self.remove(flying)
            rings.add(pair)

        # Both found: the program runs
        self.cue(2)
        status = words('both found:  637 ÷ 5.0 = 127.4', 30, INK).move_to(1.4 * UP)
        self.play(FadeIn(status, shift=0.1 * DOWN), run_time=0.8)

        # 640 is in no cell: rejected
        self.cue(3)
        new_literal = words('640', 40, INK).move_to(literal_a)
        self.play(FadeOut(status), FadeOut(rings[0]), cell_a.animate.set_opacity(0.3), run_time=0.6)
        self.play(ReplacementTransform(literal_a, new_literal), run_time=0.8)
        numeric = [grid[r][c] for r in range(1, 5) for c in (1, 2)]
        probe = SurroundingRectangle(numeric[0], color=REJECT, buff=0.02, stroke_width=4)
        self.play(Create(probe), run_time=0.3)
        for cell in numeric[1:]:
            self.play(probe.animate.move_to(cell), run_time=0.22)
        self.play(FadeOut(probe), run_time=0.3)
        cross = Cross(new_literal, stroke_color=REJECT, stroke_width=6)
        reject = words('640 is in no cell: answer rejected', 30, REJECT).move_to(1.4 * UP)
        self.play(Create(cross), FadeIn(reject), run_time=0.8)

        # The earlier design
        self.cue(4)
        before = lines('Earlier design, character offsets: 2 of 883 FinQA questions',
                       '(that run also used a different model)', size=24, color=MUTED, buff=0.12)
        before.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(before), run_time=1.0)
        self.finish()

    def results(self):
        self.begin('Result')
        self.title('Result: dependency packing keeps more of what is needed')
        caps = [200, 400, 800, 1500, 4000]
        axes = Axes(x_range=[0, 4, 1], y_range=[20, 100, 20], x_length=7.4, y_length=3.2, tips=False,
                    axis_config={'color': MUTED, 'stroke_width': 2}).move_to(0.25 * UP + 1.0 * LEFT)
        ticks = VGroup(*[words(str(v), 22, MUTED).next_to(axes.c2p(0, v), LEFT, buff=0.15) for v in (20, 40, 60, 80, 100)],
                       *[words(f'{c:,}', 22, MUTED).next_to(axes.c2p(i, 20), DOWN, buff=0.15) for i, c in enumerate(caps)])
        x_label = words('evidence budget, tokens (not to scale)', 24, MUTED).next_to(axes, DOWN, buff=0.6)
        y_label = words('gold evidence kept (%)', 24, MUTED).rotate(1.5708).next_to(axes, LEFT, buff=0.75)
        n = COVERAGE['hybridqa']['n']
        name = words(f'HybridQA, all {n:,} development questions', 26, INK).next_to(axes, UP, buff=0.25)
        chart = VGroup(axes, ticks, x_label, y_label, name)
        self.play(Create(axes), FadeIn(ticks), FadeIn(x_label), FadeIn(y_label), FadeIn(name), run_time=1.2)

        # Three curves; dependency on top at every budget
        self.cue(1)
        data = COVERAGE['hybridqa']['coverage']
        legend = VGroup()
        for method, color, label in (('length_matched', LEN, 'Length-matched'), ('ordinary', ORD, 'Ordinary'),
                                     ('dependency', DEP, 'Dependency')):
            points = [axes.c2p(i, 100 * data[str(c)][method]) for i, c in enumerate(caps)]
            curve = VGroup(*[Line(a, b, color=color, stroke_width=5 if method == 'dependency' else 3.5)
                             for a, b in zip(points, points[1:])])
            self.play(Create(curve), run_time=1.0)
            chart.add(curve)
            legend.add(VGroup(Line(LEFT * 0.25, RIGHT * 0.25, color=color, stroke_width=5),
                              words(label, 24, INK)).arrange(RIGHT, buff=0.15))
        legend = VGroup(*reversed(legend)).arrange(DOWN, aligned_edge=LEFT, buff=0.22).next_to(axes, RIGHT, buff=0.45)
        chart.add(legend)
        self.play(FadeIn(legend), run_time=0.8)

        # Discordant questions at 1,500
        self.cue(2)
        guide = DashedLine(axes.c2p(3, 20), axes.c2p(3, 100), color=FOCUS, stroke_width=3)
        split = COVERAGE['hybridqa']['discordant']['1500']
        fact = words(f'At 1,500 tokens: {split["dep_only"]} questions kept only by Dependency, '
                     f'{split["ord_only"]} only by Ordinary.', 24, INK).next_to(x_label, DOWN, buff=0.3).set_x(0)
        chart.add(guide, fact)
        self.play(Create(guide), Write(fact), run_time=1.5)

        # All six datasets: D - O at each dataset's chosen budget, then at 200 and 4,000
        self.cue(3)
        self.play(FadeOut(chart), run_time=0.8)
        order = ['hybridqa', 'multihiertt', 'tathqa', 'tatqa', 'finqa', 'convfinqa']
        display = {'hybridqa': 'HybridQA', 'multihiertt': 'MultiHiertt', 'tathqa': 'TAT-HQA',
                   'tatqa': 'TAT-QA', 'finqa': 'FinQA', 'convfinqa': 'ConvFinQA'}
        chosen = {k: int(NUMBERS['coverage'][k]['cap']) for k in order}
        row_y = [1.3 - 0.6 * i for i in range(6)]
        zero_x, right_x = -0.9, 4.6  # bars live in [zero_x - ..., right_x]; values sit right of right_x

        def diff(key, cap):
            cov = COVERAGE[key]['coverage'][str(cap)]
            return 100 * (cov['dependency'] - cov['ordinary'])

        # One scale for all three states, set by the largest gap shown (HybridQA at 200)
        unit = (right_x - zero_x) / max(diff(k, c) for k in order for c in (chosen[k], 200, 4000))

        def row_parts(key, cap, y):
            d = round(diff(key, cap), 1)
            color = DEP if d > 0 else ORD if d < 0 else MUTED
            bar = Rectangle(width=max(abs(d) * unit, 0.04), height=0.4, stroke_width=0).set_fill(color, 0.9)
            bar.move_to([zero_x + d * unit / 2, y, 0])
            value = words('0.0' if d == 0 else f'{d:+.1f}', 24, color, weight='BOLD')
            value.move_to([5.9, y, 0], aligned_edge=RIGHT)
            tag = words(f'{cap:,}', 24, MUTED).move_to([-2.65, y, 0], aligned_edge=RIGHT)
            return bar, value, tag

        heading = words('Dependency minus Ordinary, gold evidence kept (points)', 28, INK, weight='BOLD').move_to(2.5 * UP)
        state = words("at each dataset's chosen budget", 26, MUTED).next_to(heading, DOWN, buff=0.2)
        names = VGroup(*[words(display[k], 24, INK).move_to([-3.85, y, 0], aligned_edge=RIGHT) for k, y in zip(order, row_y)])
        axis = Line([zero_x, row_y[0] + 0.4, 0], [zero_x, row_y[-1] - 0.4, 0], color=MUTED, stroke_width=2)
        key = VGroup(*[VGroup(Rectangle(width=0.4, height=0.25, stroke_width=0).set_fill(c, 0.9), words(t, 24, INK))
                       .arrange(RIGHT, buff=0.15) for c, t in ((DEP, 'Dependency ahead'), (ORD, 'Ordinary ahead'))])
        key.arrange(RIGHT, buff=0.8).to_edge(DOWN, buff=0.45)
        parts = [row_parts(k, chosen[k], y) for k, y in zip(order, row_y)]
        bars, values, tags = (VGroup(*p) for p in zip(*parts))
        self.play(FadeIn(heading), FadeIn(state), FadeIn(names), Create(axis), FadeIn(key), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(VGroup(b, v, t), shift=0.1 * RIGHT) for b, v, t in parts], lag_ratio=0.15),
                  run_time=1.8)

        def move_to_cap(cap, label):
            new = [row_parts(k, cap, y) for k, y in zip(order, row_y)]
            self.play(FadeTransform(state, label),
                      *[bar.animate.become(nb) for bar, (nb, _, _) in zip(bars, new)],
                      *[FadeTransform(v, nv) for v, (_, nv, _) in zip(values, new)],
                      *[FadeTransform(t, nt) for t, (_, _, nt) in zip(tags, new)], run_time=1.5)
            for i, (_, nv, nt) in enumerate(new):
                values.submobjects[i], tags.submobjects[i] = nv, nt
            return label

        # The smallest budget: closure overhead costs coverage on two datasets
        self.cue(4)
        state = move_to_cap(200, words('at 200 tokens, the smallest budget', 26, MUTED).move_to(state))
        losers = [i for i, k in enumerate(order) if diff(k, 200) < 0]
        rings = VGroup(*[SurroundingRectangle(VGroup(names[i], values[i]), color=FOCUS, buff=0.08, stroke_width=3)
                         for i in losers])
        self.play(Create(rings), run_time=0.8)

        # The largest budget: the gap closes
        self.cue(5)
        self.play(FadeOut(rings), run_time=0.4)
        move_to_cap(4000, words('at 4,000 tokens', 26, MUTED).move_to(state))
        self.finish()

    def closing(self):
        self.begin('Closing')
        takeaway = VGroup(words('Keep the labels with the facts,', 44, DEP, weight='BOLD'),
                          words('most of all when documents are much larger than the budget.', 30, INK),
                          words('Answer-level gains are smaller and still uncertain.', 26, MUTED)).arrange(DOWN, buff=0.4)
        self.play(Write(takeaway[0]), run_time=1.5)
        self.play(FadeIn(takeaway[1], shift=0.1 * UP), run_time=1.0)
        self.cue(1)
        self.play(FadeIn(takeaway[2]), run_time=1.0)
        self.finish(clear=False)
