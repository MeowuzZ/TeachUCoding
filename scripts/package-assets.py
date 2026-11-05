"""Package generated teaching data for versioned deployment."""
from pathlib import Path
import hashlib
import tarfile
root = Path(__file__).resolve().parents[1]
archive = root / 'course-assets.tar.gz'
required = [root / 'public' / name for name in ['engineering', 'homework', 'academy', 'search-index.json']]
if not all(path.exists() for path in required):
    raise SystemExit('Run python server.py --prepare-only before packaging.')
with tarfile.open(archive, 'w:gz', compresslevel=9) as bundle:
    for path in required:
        files = sorted(path.rglob('*')) if path.is_dir() else [path]
        for file in files:
            if file.is_file():
                bundle.add(file, arcname=str(file.relative_to(root / 'public')))
(root / 'course-assets.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + '  course-assets.tar.gz\n')
print('Updated course-assets.tar.gz and course-assets.sha256')

parts = root / 'assets'
parts.mkdir(exist_ok=True)
for old in parts.glob('course-assets.tar.gz.part*'):
    old.unlink()
raw = archive.read_bytes()
for index, start in enumerate(range(0, len(raw), 512 * 1024)):
    (parts / f'course-assets.tar.gz.part{index:03d}').write_bytes(raw[start:start+512*1024])
print('Updated deployable archive parts in assets/')
