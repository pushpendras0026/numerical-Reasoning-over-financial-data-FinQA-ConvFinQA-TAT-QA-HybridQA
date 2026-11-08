"""Turn presentation_script.md into presenter/data.js. Rerun after editing the script."""
import json, re
from pathlib import Path
here = Path(__file__).parent
text = (here.parent / 'presentation_script.md').read_text()
steps, part = [], None
CUTS = [0, 43.57, 134.7, 213.4]   # start of each clip inside crux.mp4 (seconds)
for block in re.split(r'\n\s*\n', text):
    b = block.strip()
    slide = re.fullmatch(r'\*\*Slide (\d+)\. (.+?)\*\*', b)
    clip = re.fullmatch(r'\*([^*]+)\*', b)
    if slide:
        steps.append(dict(kind='slide', n=int(slide[1]), title=slide[2], notes=[]))
    elif b.startswith('**Video'):
        steps.append(dict(kind='video', title='Video: how the approach works', parts=[]))
    elif b.startswith('## Speaker'):
        part = b[3:]
    elif clip and steps and steps[-1]['kind'] == 'video':
        p = steps[-1]['parts']
        p.append(dict(name=clip[1], at=CUTS[len(p)], notes=[]))
    elif steps and not b.startswith('#'):
        s = steps[-1]
        (s['parts'][-1]['notes'] if s['kind'] == 'video' else s['notes']).append(b)
        s.setdefault('speaker', part)
    if steps:
        steps[-1].setdefault('speaker', part)
assert [s['n'] for s in steps if s['kind'] == 'slide'] == list(range(1, 17))
assert len([s for s in steps if s['kind'] == 'video'][0]['parts']) == 4
(here / 'data.js').write_text('const STEPS = ' + json.dumps(steps, ensure_ascii=False, indent=1) + ';\n')
print(len(steps), 'steps')
