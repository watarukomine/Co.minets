# -*- coding: utf-8 -*-
import os, zipfile

base = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"
checked = 0
has_may = 0
no_may = 0
sample_last_dates = []

for f in os.listdir(base):
    if not f.endswith('.zip') or f.startswith('[ZERO'):
        continue
    fpath = os.path.join(base, f)
    try:
        with zipfile.ZipFile(fpath) as z:
            inner = z.namelist()[0]
            with z.open(inner) as zf:
                content = zf.read().decode('shift_jis', errors='replace')
        if '2026-05' in content or '2026/05' in content:
            has_may += 1
        else:
            no_may += 1
            if len(sample_last_dates) < 5:
                lines = content.strip().split('\n')
                last_line = lines[-1]
                first_field = last_line.split(',')[0].strip().strip('"')
                sample_last_dates.append((f, first_field, len(lines)))
        checked += 1
        if checked >= 30:
            break
    except Exception as e:
        print(f"Error: {f}: {e}")

print(f"Checked ZIPs: {checked}")
print(f"Has May 2026: {has_may}, No May: {no_may}")
for name, last_date, lc in sample_last_dates:
    print(f"  {name}: last_date={last_date}, lines={lc}")
