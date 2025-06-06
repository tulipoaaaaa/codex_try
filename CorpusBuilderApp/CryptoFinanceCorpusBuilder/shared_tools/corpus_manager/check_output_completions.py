import json

bad = 0
bad_indices = []
total = 0
with open('outputs/v4b_val_20250506.jsonl', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        total += 1
        try:
            obj = json.loads(line)
            if not obj.get('completion') or obj.get('completion').strip() in ('', '[RAG CONTEXT]'):
                bad += 1
                bad_indices.append(idx)
        except Exception as e:
            bad += 1
            bad_indices.append(idx)
print(f'Empty or failed completions: {bad} / {total}')
if bad:
    print('Problematic line numbers:', bad_indices) 