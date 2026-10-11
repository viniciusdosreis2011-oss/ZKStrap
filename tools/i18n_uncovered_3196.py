from pathlib import Path

pairs_path=Path('tmp/i18n_pairs_3196.txt')
audit_path=Path('tmp/i18n_audit_3196.txt')
if not pairs_path.exists() or not audit_path.exists():
    raise SystemExit('audit inputs missing')

pair_variants=set()
for raw in pairs_path.read_text(encoding='utf-8').splitlines()[3:]:
    parts=raw.split(' | ',4)
    if len(parts)==5:
        pair_variants.add(parts[3].replace('\\n','\n'))
        pair_variants.add(parts[4].replace('\\n','\n'))

rows=[]
for raw in audit_path.read_text(encoding='utf-8').splitlines()[3:]:
    parts=raw.split(' | ',3)
    if len(parts)!=4: continue
    method,kind,line,text=parts
    if text in pair_variants: continue
    rows.append((method,kind,line,text))

seen=set();unique=[]
for row in rows:
    if row[3] in seen:continue
    seen.add(row[3]);unique.append(row)

out=[f'ZKStrap uncovered hard-coded UI strings: {len(unique)}','Format: method | source | line | text','']
for row in unique:out.append(' | '.join(row))
Path('tmp/i18n_uncovered_3196.txt').write_text('\n'.join(out),encoding='utf-8')
print('uncovered',len(unique))
