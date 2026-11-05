"""TeachUCoding: standard-library HTTP server with optional account synchronization."""
import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import sqlite3
import tarfile
import time
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'public'
DATA = Path(os.environ.get('TEACHU_DATA_DIR', str(ROOT / 'data'))).resolve()
DB = DATA / 'teachucoding.sqlite3'
MAX_BODY = 8_000_000


def prepare():
    """Expand versioned teaching assets; reject paths outside the public directory."""
    archive = ROOT / 'course-assets.tar.gz'
    expected = (ROOT / 'course-assets.sha256').read_text(encoding='utf-8').split()[0]
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        parts = sorted((ROOT / 'assets').glob('course-assets.tar.gz.part*'))
        raw = b''.join(part.read_bytes() for part in parts)
        if not parts or not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), expected):
            raise ValueError('Course archive checksum mismatch; check assets/ parts')
        temporary = archive.with_suffix('.tmp')
        temporary.write_bytes(raw)
        temporary.replace(archive)
    signature = expected
    marker = PUBLIC / '.assets-version'
    if marker.exists() and marker.read_text(encoding='utf-8') == signature:
        return
    with tarfile.open(archive, 'r:gz') as bundle:
        for member in bundle.getmembers():
            target = (PUBLIC / member.name).resolve()
            if not target.is_relative_to(PUBLIC.resolve()) or member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError('Unsafe asset archive entry')
        bundle.extractall(PUBLIC)
    marker.write_text(signature, encoding='utf-8')


@contextmanager
def connect():
    db = sqlite3.connect(DB, timeout=20)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize():
    DATA.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,salt TEXT NOT NULL,password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS learning(user_id TEXT PRIMARY KEY,payload TEXT NOT NULL,revision INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(address TEXT PRIMARY KEY,failures INTEGER NOT NULL,reset_at INTEGER NOT NULL);
        ''')


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310_000).hex()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def reply(self, code, value, cookie=None):
        raw = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(raw)

    def user(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get('Cookie', ''))
            token = cookies.get('teach_session')
        except Exception:
            return None
        if not token:
            return None
        digest = hashlib.sha256(token.value.encode()).hexdigest()
        with connect() as db:
            row = db.execute('SELECT u.id,u.email,u.name FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token=? AND s.expires>?', (digest, int(time.time()))).fetchone()
        return dict(row) if row else None

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/account':
            return self.reply(200, {'user': self.user()})
        if path == '/api/learning':
            user = self.user()
            if not user:
                return self.reply(401, {'error': '请先登录'})
            with connect() as db:
                row = db.execute('SELECT payload,revision FROM learning WHERE user_id=?', (user['id'],)).fetchone()
            return self.reply(200, {'state': json.loads(row['payload']) if row else None, 'revision': row['revision'] if row else 0})
        if path.startswith('/api/'):
            return self.reply(404, {'error': '接口不存在'})
        target = Path(self.translate_path(path)).resolve()
        if not target.is_relative_to(PUBLIC.resolve()) or any(part.startswith('.') for part in target.relative_to(PUBLIC.resolve()).parts) or target.is_dir() and path != '/':
            return self.reply(404, {'error': '文件不存在'})
        super().do_GET()

    def do_HEAD(self):
        path = urlsplit(self.path).path
        target = Path(self.translate_path(path)).resolve()
        if not target.is_relative_to(PUBLIC.resolve()) or any(p.startswith('.') for p in target.relative_to(PUBLIC.resolve()).parts) or target.is_dir() and path != '/':
            self.send_error(404)
            return
        super().do_HEAD()

    def body(self):
        origin = self.headers.get('Origin')
        allowed = os.environ.get('TEACHU_PUBLIC_ORIGIN')
        if origin and origin != (allowed or ('http://' + self.headers.get('Host', ''))):
            raise PermissionError('请求来源无效')
        size = int(self.headers.get('Content-Length', '0'))
        if not 0 <= size <= MAX_BODY:
            raise ValueError('请求过大')
        value = json.loads(self.rfile.read(size)) if size else {}
        if not isinstance(value, dict):
            raise ValueError('请求格式无效')
        return value

    def session_cookie(self, token, age=604800):
        secure = '; Secure' if os.environ.get('TEACHU_SECURE_COOKIE') == '1' else ''
        return f'teach_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={age}{secure}'

    def do_POST(self):
        try:
            data = self.body()
            path = urlsplit(self.path).path
            if path == '/api/account':
                user = self.user()
                return self.reply(200 if user else 401, {'user': user})
            if path == '/api/auth/logout':
                cookie = SimpleCookie(self.headers.get('Cookie', ''))
                if cookie.get('teach_session'):
                    with connect() as db:
                        db.execute('DELETE FROM sessions WHERE token=?', (hashlib.sha256(cookie['teach_session'].value.encode()).hexdigest(),))
                return self.reply(200, {'ok': True}, self.session_cookie('', 0))
            if path not in ['/api/auth/login', '/api/auth/register']:
                return self.reply(404, {'error': '接口不存在'})
            email = str(data.get('email', '')).strip().lower()
            password = str(data.get('password', ''))
            if not 3 <= len(email) <= 254 or '@' not in email or not 10 <= len(password) <= 256:
                raise ValueError('请填写有效邮箱和至少 10 位密码')
            now = int(time.time())
            address = self.client_address[0]
            with connect() as db:
                attempt = db.execute('SELECT * FROM attempts WHERE address=?', (address,)).fetchone()
                if attempt and attempt['reset_at'] > now and attempt['failures'] >= 20:
                    return self.reply(429, {'error': '尝试次数较多，请十分钟后再试'})
                row = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
                if path.endswith('register'):
                    if row:
                        raise ValueError('该邮箱已注册，请使用登录入口')
                    identity = secrets.token_hex(16)
                    name = str(data.get('name', '')).strip()[:30] or email.split('@')[0][:30]
                    salt = secrets.token_hex(16)
                    db.execute('INSERT INTO users VALUES(?,?,?,?,?)', (identity, email, name, salt, password_hash(password, salt)))
                else:
                    salt = row['salt'] if row else '00' * 16
                    candidate = password_hash(password, salt)
                    if not row or not hmac.compare_digest(candidate, row['password']):
                        failures = attempt['failures'] + 1 if attempt and attempt['reset_at'] > now else 1
                        db.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)', (address, failures, now + 600))
                        db.commit()
                        return self.reply(401, {'error': '邮箱或密码不正确'})
                    identity = row['id']
                db.execute('DELETE FROM attempts WHERE address=?', (address,))
                db.execute('DELETE FROM sessions WHERE expires<=?', (now,))
                token = secrets.token_urlsafe(32)
                db.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), identity, now + 604800))
            return self.reply(200, {'ok': True}, self.session_cookie(token))
        except PermissionError as error:
            self.reply(403, {'error': str(error)})
        except (ValueError, TypeError, sqlite3.IntegrityError) as error:
            self.reply(400, {'error': str(error)})

    def do_PUT(self):
        try:
            data = self.body()
            if urlsplit(self.path).path != '/api/learning':
                return self.reply(404, {'error': '接口不存在'})
            user = self.user()
            if not user:
                return self.reply(401, {'error': '请先登录'})
            state, revision = data.get('state'), data.get('revision')
            if not isinstance(state, dict) or state.get('schema') != 2 or not isinstance(state.get('records'), dict) or type(revision) is not int or revision < 0:
                raise ValueError('学习记录格式无效')
            with connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT payload,revision FROM learning WHERE user_id=?', (user['id'],)).fetchone()
                if revision != (row['revision'] if row else 0):
                    return self.reply(409, {'state': json.loads(row['payload']) if row else None, 'revision': row['revision'] if row else 0})
                db.execute('INSERT OR REPLACE INTO learning VALUES(?,?,?)', (user['id'], json.dumps(state, ensure_ascii=False), revision + 1))
            self.reply(200, {'revision': revision + 1})
        except PermissionError as error:
            self.reply(403, {'error': str(error)})
        except (ValueError, TypeError) as error:
            self.reply(400, {'error': str(error)})


def main():
    parser = argparse.ArgumentParser(description='TeachUCoding course server')
    parser.add_argument('--host', default=os.environ.get('HOST', '127.0.0.1'))
    parser.add_argument('--port', default=int(os.environ.get('PORT', '8876')), type=int)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    prepare()
    if args.prepare_only:
        print('Course assets ready: public/')
        return
    initialize()
    mimetypes.add_type('text/javascript', '.js')
    print(f'TeachUCoding: http://{args.host}:{args.port}', flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
