import json
from pathlib import Path

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))
non_code = []
for k, v in detect['files'].items():
    if k != 'code':
        non_code.extend(v)

filtered = [f for f in non_code if '.playwright-mcp' not in f.replace('\\', '/')]

Path('graphify-out/.graphify_uncached.txt').write_text('\n'.join(filtered), encoding='utf-8')
print(f'Semantic targets (non-code, excl. playwright-mcp scratch): {len(filtered)} files')
for f in filtered:
    print(' ', f)
