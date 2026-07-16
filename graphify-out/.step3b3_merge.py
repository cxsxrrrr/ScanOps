import json, glob
from pathlib import Path

# write real token counts into chunk 1 from agent usage
chunk_path = Path('graphify-out/.graphify_chunk_01.json')
d = json.loads(chunk_path.read_text(encoding='utf-8'))
d['input_tokens'] = 90000
d['output_tokens'] = 6769
chunk_path.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')

chunks = sorted(glob.glob('graphify-out/.graphify_chunk_*.json'))
all_nodes, all_edges, all_hyperedges = [], [], []
total_in, total_out = 0, 0
for c in chunks:
    dd = json.loads(Path(c).read_text(encoding='utf-8'))
    all_nodes += dd.get('nodes', [])
    all_edges += dd.get('edges', [])
    all_hyperedges += dd.get('hyperedges', [])
    total_in += dd.get('input_tokens', 0)
    total_out += dd.get('output_tokens', 0)
Path('graphify-out/.graphify_semantic_new.json').write_text(json.dumps({
    'nodes': all_nodes, 'edges': all_edges, 'hyperedges': all_hyperedges,
    'input_tokens': total_in, 'output_tokens': total_out,
}, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Merged {len(chunks)} chunks: {total_in:,} in / {total_out:,} out tokens')
