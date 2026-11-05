import tempfile
import unittest
from pathlib import Path
import service

class BusinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        service.DB = Path(self.temp.name)/'test.sqlite3'
        service.initialize()
    def tearDown(self): self.temp.cleanup()
    def test_create_and_persist(self):
        identity = service.create_record(dict(title='测试记录', category=service.CONFIG['categories'][0], amount=5, note='模拟'))
        self.assertTrue(any(r['id']==identity for r in service.list_records()))
    def test_invalid_amount(self):
        for amount in [-1,True,2.5,'3']:
            with self.assertRaises(ValueError):
                service.create_record(dict(title='x',category=service.CONFIG['categories'][0],amount=amount))
    def test_unknown_category(self):
        with self.assertRaises(ValueError):service.create_record(dict(title='x',category='无效分类',amount=1))
    def test_transition_boundaries(self):
        row=service.list_records()[0]
        for _ in range(len(service.CONFIG['states'])-1):service.transition(row['id'])
        with self.assertRaises(ValueError):service.transition(row['id'])
        with self.assertRaises(ValueError):service.transition(-1)
if __name__=='__main__':unittest.main()
