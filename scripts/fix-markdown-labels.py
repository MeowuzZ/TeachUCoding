import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'public';changed=[]
def fix(text):
 # Keep fenced source code intact. Punctuation belongs outside the emphasis span.
 parts=re.split(r'(^```[^\n]*\n.*?^```[^\n]*$)',text,flags=re.M|re.S)
 for i in range(0,len(parts),2):parts[i]=re.sub(r'\*\*([^*\n]+?)([：:])\*\*(?=\S)',r'**\1**\2',parts[i])
 return ''.join(parts)
for file in (p/'engineering').glob('*.json'):
 d=json.loads(file.read_text(encoding='utf-8'))
 if 'body' not in d:continue
 before=d['body'];d['body']=fix(before)
 if d['body']!=before:file.write_text(json.dumps(d,ensure_ascii=False,indent=2), encoding='utf-8');changed.append(file.name)
f=root/'scripts/rewrite-engineering-lessons.py';s=f.read_text(encoding='utf-8').replace('**动手观察：**','**动手观察**：').replace('**容易忽略的边界：**','**容易忽略的边界**：');f.write_text(s, encoding='utf-8')
(root/'qa/markdown').mkdir(parents=True,exist_ok=True)
(root/'qa/markdown/修复清单.json').write_text(json.dumps({'count':len(changed),'files':changed},ensure_ascii=False,indent=2), encoding='utf-8')
print('Fixed emphasis punctuation in',len(changed),'lesson bodies; source generator updated.')
