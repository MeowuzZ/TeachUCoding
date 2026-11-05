import hashlib
import http.client
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
import server


class DeployTests(unittest.TestCase):
    def test_assets(self):
        server.prepare()
        archive = server.ROOT / 'course-assets.tar.gz'
        expected = (server.ROOT / 'course-assets.sha256').read_text(encoding='utf-8').split()[0]
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), expected)
        server.prepare()
        catalog = json.loads((server.PUBLIC / 'engineering/catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(len(catalog['lessons']), 1063)
        tasks = json.loads((server.PUBLIC / 'academy/project-homework.json').read_text(encoding='utf-8'))
        self.assertEqual(len(tasks), 1111)
        for task in tasks.values():
            self.assertTrue((server.PUBLIC / task['download']).is_file())
            self.assertTrue((server.PUBLIC / task['answer']).is_file())


class AccountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        server.DATA = Path(cls.folder.name)
        server.DB = server.DATA / 'test.sqlite3'
        server.initialize()
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.port = cls.http.server_port
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        cls.folder.cleanup()

    def request(self, method, path, payload=None, cookie=None, origin=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=8)
        headers = {'Content-Type': 'application/json'}
        if cookie:
            headers['Cookie'] = cookie
        if origin:
            headers['Origin'] = origin
        connection.request(method, path, json.dumps(payload).encode() if payload is not None else None, headers)
        response = connection.getresponse()
        raw = response.read()
        status, cookie_header = response.status, response.getheader('Set-Cookie')
        connection.close()
        return status, json.loads(raw), cookie_header

    def test_account_and_revision_flow(self):
        email = 'student@example.test'
        password = 'test-only-password-123'
        status, _, cookie = self.request('POST', '/api/auth/register', {'email': email, 'password': password, 'name': '测试学员'})
        self.assertEqual(status, 200)
        self.assertIn('HttpOnly', cookie)
        cookie = cookie.split(';')[0]
        status, value, _ = self.request('GET', '/api/account', cookie=cookie)
        self.assertEqual(value['user']['email'], email)
        self.assertEqual(self.request('POST', '/api/account', cookie=cookie)[0], 200)
        state = {'schema': 2, 'records': {'method:L01': {'learn': True}}}
        self.assertEqual(self.request('PUT', '/api/learning', {'state': state, 'revision': 0}, cookie)[0], 200)
        status, value, _ = self.request('PUT', '/api/learning', {'state': state, 'revision': 0}, cookie)
        self.assertEqual(status, 409)
        self.assertEqual(value['revision'], 1)
        self.assertEqual(self.request('GET', '/api/learning', cookie=cookie)[1]['state'], state)
        self.assertEqual(self.request('PUT', '/api/learning', {'state': state, 'revision': 1}, cookie, 'https://other.example')[0], 403)
        self.assertEqual(self.request('POST', '/api/auth/logout', cookie=cookie)[0], 200)
        self.assertIsNone(self.request('GET', '/api/account', cookie=cookie)[1]['user'])
        self.assertEqual(self.request('POST', '/api/auth/login', {'email': email, 'password': 'wrong-password'})[0], 401)
        self.assertEqual(self.request('POST', '/api/auth/login', {'email': email, 'password': password})[0], 200)
        with server.connect() as db:
            row = db.execute('SELECT password FROM users WHERE email=?', (email,)).fetchone()
            self.assertNotEqual(row['password'], password)

    def test_unauthorized_and_hidden_files(self):
        self.assertEqual(self.request('GET', '/api/learning')[0], 401)
        self.assertEqual(self.request('GET', '/.assets-version')[0], 404)
        self.assertEqual(self.request('GET', '/engineering/')[0], 404)
        self.assertEqual(self.request('GET', '/api/workspace')[0], 404)


if __name__ == '__main__':
    unittest.main()
