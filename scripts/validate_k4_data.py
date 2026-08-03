import csv
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / 'data' / 'k4_ecommerce'
REQUIRED = ['doc_id', 'title', 'source_url', 'retrieved_at', 'document_version']
KEY = 'customer_role'

md_files = sorted(DATA_DIR.glob('*.md'))
rows = list(csv.DictReader(open(DATA_DIR / 'sources.csv', encoding='utf-8')))

ids = []
roles = {}
for path in md_files:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    fm = {}
    if lines and lines[0].strip() == '---':
        end = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() == '---':
                end = idx
                break
        if end is not None:
            for raw in lines[1:end]:
                line = raw.strip()
                if not line or line.startswith('#') or ':' not in line:
                    continue
                key, value = line.split(':', 1)
                value = value.split(' #', 1)[0].strip().strip('"').strip("'")
                fm[key.strip()] = value
    ids.append(fm.get('doc_id'))
    role = fm.get(KEY)
    if role:
        roles[role] = roles.get(role, 0) + 1
    ok = all(k in fm for k in REQUIRED) and KEY in fm and fm.get('doc_id') == path.stem
    print(f'{path.name:30} {"OK" if ok else "THIEU METADATA"}')

print('so file :', len(md_files), '(can 5-10)')
print('csv     :', 'khop' if sorted(r['doc_id'] for r in rows) == sorted([x for x in ids if x]) else 'LECH')
print(KEY, ':', roles)

# check exactly 5 benchmark queries in report
report_path = BASE / 'report' / 'REPORT_NHOM.md'
text = report_path.read_text(encoding='utf-8')
lines = text.splitlines()
start_idx = next((i for i, line in enumerate(lines) if '### Câu hỏi đánh giá' in line), None)
end_idx = next((i for i, line in enumerate(lines[start_idx + 1 :], start=start_idx + 1) if '### Tổng hợp chất lượng' in line), len(lines))
query_rows = [line for line in lines[start_idx + 1:end_idx] if re.match(r'^\|\s*[1-5]\s*\|', line)]
query_count = len(query_rows)
print('benchmark queries :', query_count)
