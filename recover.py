import re
import os
import codecs

log_path = r'C:\Users\cheru\.gemini\antigravity\brain\0fb4834f-97a4-4732-8797-de5b481cae7b\.system_generated\logs\overview.txt'

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Try to find target content blocks
matches = re.finditer(r'"TargetContent":"(.*?)(?<!\\)"', text, re.DOTALL)
count = 0
for m in matches:
    raw = m.group(1)
    # decode the json escaped string
    try:
        content = codecs.decode(raw, 'unicode_escape')
    except Exception as e:
        content = raw.replace('\\n', '\n').replace('\\"', '"')
    
    # Check if this content is part of styles.css or index.html
    if ':root {' in content and '--bg-main' not in content:
        with open(r'c:\Users\cheru\OneDrive\Desktop\SECO 1.0\frontend\styles_old.css', 'w', encoding='utf-8') as out:
            out.write(content)
            print("Recovered styles chunk")
    if '<div class="dashboard-grid">' in content:
        with open(r'c:\Users\cheru\OneDrive\Desktop\SECO 1.0\frontend\index_grid.html', 'w', encoding='utf-8') as out:
            out.write(content)
            print("Recovered index grid chunk")

print("Done")
