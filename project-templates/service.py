"""本地教学服务：SQLite 持久化、业务状态流转、筛选、统计与 CSV 导出。"""
import csv
from contextlib import contextmanager
import io
import json
import sqlite3
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / 'scenario.json').read_text(encoding='utf-8'))
DB = ROOT / 'records.sqlite3'

@contextmanager
def connect():
    db = sqlite3.connect(DB)
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
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>=0), status TEXT NOT NULL, note TEXT NOT NULL)')
        if db.execute('SELECT COUNT(*) FROM records').fetchone()[0] == 0:
            db.executemany('INSERT INTO records(title,category,amount,status,note) VALUES(?,?,?,?,?)', CONFIG['seed'])

def validate(data):
    title = str(data.get('title', '')).strip()
    if not title or len(title) > 80:
        raise ValueError('名称须为 1—80 字')
    category = str(data.get('category', ''))
    if category not in CONFIG['categories']:
        raise ValueError('请选择有效分类')
    amount = data.get('amount')
    if isinstance(amount, bool) or not isinstance(amount, int) or not 0 <= amount <= 100000000:
        raise ValueError('数量／金额须为规定范围内的非负整数')
    return title, category, amount, str(data.get('note', ''))[:500]

def list_records():
    with connect() as db:
        return [dict(row) for row in db.execute('SELECT * FROM records ORDER BY id DESC')]

def create_record(data):
    title, category, amount, note = validate(data)
    with connect() as db:
        row = db.execute('INSERT INTO records(title,category,amount,status,note) VALUES(?,?,?,?,?)', (title, category, amount, CONFIG['states'][0], note))
        return row.lastrowid

def transition(record_id):
    with connect() as db:
        row = db.execute('SELECT * FROM records WHERE id=?', (record_id,)).fetchone()
        if row is None:
            raise ValueError('记录不存在')
        states = CONFIG['states']
        index = states.index(row['status'])
        if index == len(states)-1:
            raise ValueError('已到最终状态，不能重复处理')
        db.execute('UPDATE records SET status=? WHERE id=?', (states[index+1], record_id))

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload, content_type='application/json; charset=utf-8'):
        raw = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == '/api/config':
            return self.reply(200, CONFIG)
        if route == '/api/records':
            return self.reply(200, list_records())
        if route == '/api/export':
            out = io.StringIO(); writer = csv.writer(out)
            writer.writerow(['id', 'title', 'category', 'amount', 'status', 'note'])
            for row in list_records():
                # 阻止电子表格公式注入。
                writer.writerow([("'"+str(v)) if str(v).startswith(('=', '+', '-', '@')) else v for v in row.values()])
            return self.reply(200, ('\ufeff'+out.getvalue()).encode(), 'text/csv; charset=utf-8')
        files = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}
        if route in files:
            content_type = {'/': 'text/html', '/app.js': 'text/javascript', '/style.css': 'text/css'}[route]
            return self.reply(200, (ROOT/files[route]).read_bytes(), content_type+'; charset=utf-8')
        self.reply(404, {'error': '路径不存在'})

    def do_POST(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                raise ValueError('请求长度无效')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError('请求须为对象')
            route = urlparse(self.path).path
            if route == '/api/records':
                return self.reply(201, {'id': create_record(data)})
            if route.startswith('/api/advance/'):
                transition(int(route.rsplit('/', 1)[-1]))
                return self.reply(200, {'ok': True})
            self.reply(404, {'error': '路径不存在'})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.reply(400, {'error': str(exc)})

if __name__ == '__main__':
    initialize()
    print('本地项目：http://127.0.0.1:8088 （Ctrl+C 停止）')
    ThreadingHTTPServer(('127.0.0.1', 8088), Handler).serve_forever()
