"""Five-minute explainer: the problem, the pipeline, and the main result.

Render: /Users/mac/CourseWork/BigDataProject/.manim/bin/manim -qh explainer.py Explainer
Every number shown is taken from the project's measured results.
"""
import json
from pathlib import Path

from manim import (DOWN, LEFT, RIGHT, UP, UL, Arrow, Axes, Create, Cross, DashedLine, FadeIn,
                   FadeOut, Indicate, LaggedStart, Line, ReplacementTransform, RoundedRectangle,
                   Scene, SurroundingRectangle, Text, Transform, VGroup, Write, config)

config.background_color = '#FCFCFB'
INK, MUTED, RULE = '#1F2328', '#5E6168', '#D9D7D0'
ORD, DEP, LEN = '#2A78D6', '#EB6834', '#1BAF7A'
FONT = 'Helvetica Neue'
ROOT = Path(__file__).resolve().parents[2]
COVERAGE = json.loads((ROOT / 'artifacts/v11/coverage.json').read_text())


def words(text, size=28, color=INK, **kw):
    return Text(text, font=FONT, font_size=size, color=color, **kw)


def box(label, color=MUTED, width=1.9, height=0.9, size=20):
    frame = RoundedRectangle(corner_radius=0.12, width=width, height=height, color=color, stroke_width=2.5)
    frame.set_fill('#FFFFFF', 1)
    return VGroup(frame, words(label, size, INK).move_to(frame))


TABLE = [['company', 'payments vol. (bn)', 'transactions (bn)'],
         ['visa inc.', '$ 2457', '50.3'],
         ['mastercard', '1697', '27.0'],
         ['american express', '637', '5.0'],
         ['discover', '102', '1.6']]


def table(scale=1.0):
    widths = [3.2, 2.6, 2.6]
    rows = VGroup()
    for r, row in enumerate(TABLE):
        cells = VGroup()
        for c, value in enumerate(row):
            frame = RoundedRectangle(corner_radius=0.04, width=widths[c], height=0.62, color=RULE, stroke_width=1.5)
            frame.set_fill('#FFFFFF', 1)
            label = words(value, 20, MUTED if r == 0 else INK)
            cells.add(VGroup(frame, label.move_to(frame)))
        cells.arrange(RIGHT, buff=0)
        rows.add(cells)
    rows.arrange(DOWN, buff=0)
    return rows.scale(scale)


# Animations and per-scene holds are calibrated to live narration at ~140 wpm plus air.
MOTION = 1.3


class Explainer(Scene):
    def play(self, *animations, run_time=None, **kwargs):
        if run_time is not None:
            kwargs['run_time'] = run_time * MOTION
        super().play(*animations, **kwargs)

    def wait(self, duration=1.0, **kwargs):
        super().wait(duration, **kwargs)

    def title(self, text):
        heading = words(text, 32, INK, weight='BOLD').to_corner(UL).shift(0.15 * DOWN)
        self.play(FadeIn(heading, shift=0.2 * DOWN), run_time=0.8)
        return heading

    def clear(self, *keep):
        self.play(*[FadeOut(m) for m in self.mobjects if m not in keep], run_time=0.8)

    def construct(self):
        self.opening()
        self.problem()
        self.budget()
        self.pipeline()
        self.packing()
        self.grounding()
        self.results()
        self.closing()

    # 0:00 - 0:22 (Narration: Title & Opening quote)
    def opening(self):
        # 3-second title card with project title and both authors
        title = words('Dependency-Preserving Evidence Packing\nfor Numerical Question Answering', 32, INK, weight='BOLD')
        authors = words('Pushpendra Singh  &  Badri Bishal Das', 24, DEP).next_to(title, DOWN, buff=0.45)
        affil = words('Indian Institute of Technology Guwahati', 20, MUTED).next_to(authors, DOWN, buff=0.25)
        title_card = VGroup(title, authors, affil).move_to([0, 0, 0])
        self.play(FadeIn(title_card, shift=0.15 * UP), run_time=1.0)
        self.wait(3.0)
        self.play(FadeOut(title_card), run_time=0.8)

        line1 = words('A number in a financial report', 38)
        line2 = words('means nothing on its own.', 38, DEP).next_to(line1, DOWN, buff=0.3)
        quote = VGroup(line1, line2).move_to([0, 0, 0])
        self.play(Write(line1), run_time=1.2)
        self.play(Write(line2), run_time=1.2)
        self.wait(4.0)
        self.clear()

    # 0:22 - 0:54 (Narration: What does 637 mean?)
    def problem(self):
        heading = self.title('What does "637" mean?')
        grid = table(0.95).shift(0.3 * DOWN)
        self.play(LaggedStart(*[FadeIn(row, shift=0.1 * UP) for row in grid], lag_ratio=0.15), run_time=1.6)
        question = words('"Average payment volume per transaction for American Express?"', 22, MUTED)
        question.next_to(grid, DOWN, buff=0.45)
        self.play(FadeIn(question), run_time=1.0)
        target = VGroup(grid[3][1], grid[3][2])
        self.play(*[cell[0].animate.set_fill(DEP, 0.25) for cell in target], run_time=1.0)
        labels = VGroup(grid[3][0], grid[0][1], grid[0][2])
        self.play(*[Indicate(cell, color=DEP, scale_factor=1.06) for cell in labels], run_time=1.5)
        self.wait(2.0)
        others = [cell for row in grid for cell in row if cell not in target]
        self.play(*[FadeOut(cell) for cell in others], FadeOut(question), run_time=1.2)
        lost = words('Without its row and column labels,\nthe model cannot tell 637 from 5.0.', 26, INK)
        lost.next_to(target, DOWN, buff=0.7)
        self.play(Write(lost), run_time=1.8)
        self.wait(4.5)
        self.clear()

    # 0:54 - 1:26 (Narration: Reading budget)
    def budget(self):
        heading = self.title('The model can only read part of the document')
        facts = VGroup(*[RoundedRectangle(corner_radius=0.05, width=0.55, height=0.32, color=RULE, stroke_width=1)
                         .set_fill('#FFFFFF', 1) for _ in range(96)])
        facts.arrange_in_grid(rows=8, cols=12, buff=0.08).shift(0.4 * DOWN + 1.6 * LEFT)
        self.play(LaggedStart(*[FadeIn(f) for f in facts], lag_ratio=0.01), run_time=1.6)
        doc_label = words('HybridQA: median document ~8,900 tokens', 22, MUTED).next_to(facts, UP, buff=0.25)
        self.play(FadeIn(doc_label), run_time=0.8)
        window = RoundedRectangle(corner_radius=0.12, width=2.6, height=3.3, color=DEP, stroke_width=4)
        window.next_to(facts, RIGHT, buff=0.9)
        budget = words('budget\n1,500 tokens', 22, DEP).next_to(window, DOWN, buff=0.2)
        self.play(Create(window), FadeIn(budget), run_time=1.2)
        chosen = VGroup(*[facts[i] for i in (3, 15, 27, 40, 52, 61, 70, 88)])
        copies = chosen.copy()
        self.play(copies.animate.arrange_in_grid(rows=4, cols=2, buff=0.15).move_to(window), run_time=1.6)
        self.play(*[c.animate.set_fill(DEP, 0.3) for c in copies], run_time=0.6)
        point = words('Which facts go in, and do their labels come with them?', 26, INK)
        point.to_edge(DOWN, buff=0.5)
        self.play(Write(point), run_time=1.8)
        self.wait(5.0)
        self.clear()

    # 1:26 - 2:05 (Narration: Pipeline)
    def pipeline(self):
        heading = self.title('One pipeline for six datasets')
        names = ['Reader', 'BM25\nretrieval', 'Evidence\npacking', 'Model\n(one call)', 'Literal\ngrounding', 'Executor', 'Official\nscorer']
        stages = VGroup(*[box(n, DEP if i == 2 else MUTED, width=1.62, size=18) for i, n in enumerate(names)])
        stages.arrange(RIGHT, buff=0.32).shift(0.3 * UP)
        arrows = VGroup(*[Arrow(stages[i].get_right(), stages[i + 1].get_left(), buff=0.05, color=MUTED,
                                stroke_width=3, max_tip_length_to_length_ratio=0.35) for i in range(len(stages) - 1)])
        for stage, arrow in zip(stages, list(arrows) + [None]):
            self.play(FadeIn(stage, shift=0.15 * RIGHT), run_time=0.4)
            if arrow:
                self.play(Create(arrow), run_time=0.2)
        tag = words('the only thing we change', 20, DEP).next_to(stages[2], UP, buff=0.3)
        self.play(FadeIn(tag), Indicate(stages[2], color=DEP), run_time=1.2)
        gold = box('Gold labels', MUTED, width=2.2, size=18).next_to(stages[0], DOWN, buff=1.3)
        path = DashedLine(gold.get_right(), [stages[6].get_bottom()[0], gold.get_right()[1], 0], color=MUTED)
        up = Line(path.get_end(), stages[6].get_bottom(), color=MUTED)
        self.play(FadeIn(gold), Create(path), Create(up), run_time=1.2)
        note = words('Labels join only at scoring. 0 of 443 checked prompts contained one.', 22, MUTED)
        note.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(note), run_time=1.0)
        self.wait(6.0)
        self.clear()

    # 2:05 - 2:40 (Narration: Three packing methods)
    def packing(self):
        heading = self.title('Same budget, three ways to fill it')
        columns = VGroup()
        specs = [('Ordinary', ORD, ['amex | payments | 637', 'amex | transactions | 5.0'], 'labels repeated in every cell'),
                 ('Dependency', DEP, ['company | payments | txns', 'amex | 637 | 5.0'], 'labels kept once, with structure'),
                 ('Length-matched', LEN, ['637   5.0', '1697   27.0   102   1.6'], 'neighbouring text, same length')]
        for name, color, lines, caption in specs:
            label = words(name, 26, color, weight='BOLD')
            frame = RoundedRectangle(corner_radius=0.12, width=4.1, height=2.4, color=color, stroke_width=3)
            content = VGroup(*[words(l, 20, INK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
            content.move_to(frame)
            note = words(caption, 18, MUTED)
            columns.add(VGroup(label, VGroup(frame, content), note).arrange(DOWN, buff=0.22))
        columns.arrange(RIGHT, buff=0.3).shift(0.2 * DOWN)
        for column in columns:
            self.play(FadeIn(column[0]), Create(column[1][0]), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(l, shift=0.1 * RIGHT) for l in column[1][1]], lag_ratio=0.25), run_time=1.0)
            self.play(FadeIn(column[2]), run_time=0.5)
            self.wait(1.5)
        why = words('Dependency packing follows each fact to its headers, units, hierarchy and links.', 22, INK)
        why.to_edge(DOWN, buff=0.4)
        self.play(Write(why), run_time=1.6)
        self.wait(4.0)
        self.clear()

    # 2:40 - 3:20 (Narration: Literal grounding)
    def grounding(self):
        heading = self.title('The model copies values; code checks them')
        plan = words('divide("637", "5.0")', 32, INK).shift(1.9 * UP)
        self.play(Write(plan), run_time=1.2)
        grid = table(0.75).shift(0.9 * DOWN)
        self.play(FadeIn(grid), run_time=0.8)

        # Dim non-target cells to 25% opacity so focus is unmistakably on the target values
        target_cells = (grid[3][1], grid[3][2])
        non_target = [c for r in grid for c in r if c not in target_cells]
        self.play(*[c.animate.set_opacity(0.25) for c in non_target], run_time=0.6)

        ring1 = SurroundingRectangle(grid[3][1], color=DEP, buff=0.03)
        ring2 = SurroundingRectangle(grid[3][2], color=DEP, buff=0.03)
        self.play(plan[8:11].animate.set_color(DEP), Create(ring1), run_time=0.8)
        self.play(plan[14:17].animate.set_color(DEP), Create(ring2), run_time=0.8)

        ok = words('both found in evidence: answer 127.4', 22, LEN).next_to(plan, DOWN, buff=0.35)
        self.play(FadeIn(ok), run_time=0.8)
        self.wait(2.5)

        # Transform to 640; fade out ring1 so 640 does not appear matched to 637
        bad = words('divide("640", "5.0")', 32, INK).move_to(plan)
        bad[14:17].set_color(DEP)
        self.play(ReplacementTransform(plan, bad), FadeOut(ok), FadeOut(ring1), run_time=0.8)

        # Quick highlight sweep across numeric cells showing search for 640
        num_cells = [grid[r][c] for r in range(1, 5) for c in (1, 2) if grid[r][c] != grid[3][2]]
        self.play(LaggedStart(*[Indicate(c, color=DEP, scale_factor=1.04) for c in num_cells], lag_ratio=0.08), run_time=1.2)

        cross = Cross(bad[8:11], stroke_color=DEP, stroke_width=5)
        reject = words('640 appears in no cell: rejected', 22, DEP).next_to(bad, DOWN, buff=0.35)
        self.play(Create(cross), FadeIn(reject), run_time=0.8)
        self.wait(2.0)

        before = words('Earlier design (character offsets): 2 of 883 FinQA questions.', 22, MUTED).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(before), run_time=0.8)
        self.wait(5.0)
        self.clear()

    # 3:20 - 4:10 (Narration: Results)
    def results(self):
        heading = self.title('Result: dependency packing keeps more of what is needed')
        caps = [200, 400, 800, 1500, 4000]
        # Shift axes UP to avoid overlap with bottom labels
        axes = Axes(x_range=[0, 4, 1], y_range=[20, 100, 20], x_length=7.2, y_length=3.4, tips=False,
                    axis_config={'color': MUTED, 'stroke_width': 2, 'include_ticks': True},
                    ).shift(0.45 * UP + 0.9 * LEFT)
        for value in (20, 40, 60, 80, 100):
            axes.add(words(str(value), 18, MUTED).next_to(axes.c2p(0, value), LEFT, buff=0.18))
        for i, cap in enumerate(caps):
            axes.add(words(f'{cap:,}', 18, MUTED).next_to(axes.c2p(i, 20), DOWN, buff=0.18))
        x_label = words('evidence budget (tokens, not to scale)', 18, MUTED).next_to(axes, DOWN, buff=0.35)
        y_label = words('gold evidence kept (%)', 18, MUTED).rotate(1.5708).next_to(axes, LEFT, buff=0.5)
        name = words('HybridQA, all 3,466 development questions', 22, INK).next_to(axes, UP, buff=0.2)
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label), FadeIn(name), run_time=1.2)

        data = COVERAGE['hybridqa']['coverage']
        legend = VGroup()
        for method, color, label in (('ordinary', ORD, 'Ordinary'), ('dependency', DEP, 'Dependency'),
                                     ('length_matched', LEN, 'Length-matched')):
            points = [axes.c2p(i, 100 * data[str(c)][method]) for i, c in enumerate(caps)]
            curve = VGroup(*[Line(points[i], points[i + 1], color=color, stroke_width=4) for i in range(len(points) - 1)])
            self.play(Create(curve), run_time=1.0)
            legend.add(VGroup(Line(LEFT * 0.25, RIGHT * 0.25, color=color, stroke_width=5), words(label, 20, INK)).arrange(RIGHT, buff=0.15))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(axes, RIGHT, buff=0.4)
        self.play(FadeIn(legend), run_time=0.6)

        d, o = COVERAGE['hybridqa']['discordant']['1500'].values()
        fact = words(f'At 1,500 tokens: {d} questions kept only by Dependency, {o} only by Ordinary.', 20, INK)
        fact.next_to(x_label, DOWN, buff=0.3)
        self.play(Write(fact), run_time=1.5)
        self.wait(3.0)

        all_six = words('At the chosen budgets Dependency is ahead on all six datasets; the gap closes as budgets grow.', 19, MUTED)
        all_six.move_to(fact)
        self.play(Transform(fact, all_six), run_time=1.2)
        self.wait(3.5)

        # Clear HybridQA chart for the 6-8s beat backing the "all six" claim with compact bar chart
        chart_group = VGroup(axes, x_label, y_label, name, legend, fact)
        self.play(FadeOut(chart_group), run_time=0.8)

        # Compact six-row bar chart of D - O at each dataset's chosen cap, read dynamically from COVERAGE
        chosen_caps = [
            ('HybridQA', 'hybridqa', '1500'),
            ('MultiHiertt', 'multihiertt', '1500'),
            ('TAT-HQA', 'tathqa', '400'),
            ('TAT-QA', 'tatqa', '400'),
            ('FinQA', 'finqa', '800'),
            ('ConvFinQA', 'convfinqa', '800'),
        ]
        subheading = words('Evidence coverage difference at chosen budgets (D − O)', 24, INK, weight='BOLD').shift(2.4 * UP)
        self.play(FadeIn(subheading), run_time=0.6)

        bar_rows = VGroup()
        for ds_display, ds_key, cap_str in chosen_caps:
            cov = COVERAGE[ds_key]['coverage'][cap_str]
            diff = 100 * (cov['dependency'] - cov['ordinary'])
            ds_label = words(f'{ds_display} ({cap_str})', 20, INK, weight='MEDIUM')
            ds_label.set_width(3.2)
            # Bar width scaled: 4.0 points -> 4.5 units
            bar_w = max(0.2, (diff / 4.0) * 4.5)
            bar = RoundedRectangle(corner_radius=0.08, width=bar_w, height=0.38, color=DEP, stroke_width=0).set_fill(DEP, 0.9)
            val_label = words(f'+{diff:.1f} pts', 20, DEP, weight='BOLD')
            row = VGroup(ds_label, bar, val_label).arrange(RIGHT, buff=0.25)
            bar_rows.add(row)

        bar_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.22).shift(0.3 * DOWN)
        self.play(LaggedStart(*[FadeIn(row, shift=0.1 * RIGHT) for row in bar_rows], lag_ratio=0.15), run_time=1.8)
        self.wait(5.0)
        self.clear()

    # 4:10 - 4:32 (Narration: Closing takeaway)
    def closing(self):
        lines = VGroup(words('Keep the labels with the facts,', 36, INK),
                       words('especially when the budget is tight.', 36, DEP),
                       words('Answer-level gains are smaller and still uncertain.', 22, MUTED)).arrange(DOWN, buff=0.35)
        self.play(LaggedStart(*[Write(l) for l in lines], lag_ratio=0.6), run_time=2.5)
        self.wait(4.0)
