"""Validate every download, keyword restoration and representative executable projects."""
import ast,json,re,zipfile,tempfile,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'public'
data=json.loads((p/'academy/project-homework.json').read_text(encoding='utf-8'))
seen=set(); counts={}; samples={}
for key,item in data.items():
    assert (p/item['download']).is_file(), key
    answer=json.loads((p/item['answer']).read_text(encoding='utf-8'))
    with zipfile.ZipFile(p/item['download']) as package:
        assert package.testzip() is None,key
        assert {'README.md','验收清单.md','关键词词库.md','实践记录.md'}.issubset(package.namelist()),key
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in package.namelist())
        for file in answer['files']:
            starter=package.read(file['path']).decode()
            for blank in answer['explanations']:starter=starter.replace(blank['token'],blank['answer'])
            assert starter==file['content'], (key,file['path'])
            if file['path'].endswith('.py'):ast.parse(starter)
        assert len(answer['explanations'])==3,key
    seen.add(item['type']);counts[item['stack']]=counts.get(item['stack'],0)+1
    samples.setdefault((item['stack'],item['scenario']),answer)
assert len(data)==1111 and len(seen)>=20
with tempfile.TemporaryDirectory() as temporary:
    base=Path(temporary)
    for (stack,scenario),answer in samples.items():
        dest=base/(stack+'-'+scenario);dest.mkdir()
        for file in answer['files']:(dest/file['path']).write_text(file['content'], encoding='utf-8')
        if stack=='python':
            run=subprocess.run([sys.executable,'-m','unittest','test_service.py'],cwd=dest,capture_output=True,text=True)
            assert run.returncode==0,(scenario,run.stderr)
        if stack=='web':
            for name in ['app.js','scenario.js']:
                run=subprocess.run(['node','--check',name],cwd=dest,capture_output=True,text=True)
                assert run.returncode==0,(scenario,run.stderr)
    # Java implementation is identical across scenarios; compile once and test each config.
    java=[(k,a) for k,a in samples.items() if k[0]=='java']
    dest=base/'java-check';dest.mkdir();(dest/'Main.java').write_text(java[0][1]['files'][1]['content'] if java[0][1]['files'][1]['path']=='Main.java' else next(f['content'] for f in java[0][1]['files'] if f['path']=='Main.java'), encoding='utf-8')
    run=subprocess.run(['javac','-encoding','UTF-8','Main.java'],cwd=dest,capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    for (_,scenario),answer in java:
        (dest/'scenario.properties').write_text(next(f['content'] for f in answer['files'] if f['path']=='scenario.properties'), encoding='utf-8')
        run=subprocess.run(['java','Main','--test'],cwd=dest,capture_output=True,text=True)
        assert run.returncode==0,(scenario,run.stderr)
print(f'PASS: {len(data)} downloads; {len(seen)} assignment types; {len(samples)} stack/scenario combinations; keyword restoration, Python tests, Java compile/business tests, JS syntax.')
print(counts)
