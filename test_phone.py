import os
import tempfile
import unittest
import base64
import hmac
import hashlib
from urllib.parse import urlencode
from xml.etree.ElementTree import fromstring

os.environ['VOXERA_DB'] = tempfile.mktemp(suffix='.db')
os.environ['VOXERA_ACCESS_CODE'] = 'test-only-not-a-live-secret'
os.environ['VOXERA_PUBLIC_URL'] = 'https://example.test'
os.environ['TWILIO_AUTH_TOKEN'] = 'test-token'
os.environ['TWILIO_ACCOUNT_SID'] = 'AC' + '1' * 32
from fastapi.testclient import TestClient
from app import app

class PhoneTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.__enter__()
    def tearDown(self):
        self.client.__exit__(None, None, None)
    def post(self, path, extra=None):
        data = {'AccountSid': os.environ['TWILIO_ACCOUNT_SID'], 'CallSid':'CA'+'2'*32}
        data.update(extra or {})
        message = 'https://example.test' + path + ''.join(k+data[k] for k in sorted(data))
        signature = base64.b64encode(hmac.new(b'test-token',message.encode(),hashlib.sha1).digest()).decode()
        return self.client.post(path, content=urlencode(data), headers={'Content-Type':'application/x-www-form-urlencoded','X-Twilio-Signature':signature})
    def test_intro(self):
        r=self.post('/api/voice/incoming');self.assertEqual(r.status_code,200)
        self.assertIn('fictional',r.text);self.assertIn('AI assistant',r.text)
        self.assertIsNotNone(fromstring(r.text).find('Gather'))
    def test_unsigned_rejected(self):
        self.assertEqual(self.client.post('/api/voice/incoming',content='x=y').status_code,403)
    def test_hangup(self):
        self.assertIsNotNone(fromstring(self.post('/api/voice/turn',{'Digits':'0'}).text).find('Hangup'))
    def test_keypad(self):
        r=self.post('/api/voice/turn',{'Digits':'1'});self.assertEqual(r.status_code,200);self.assertIn('Gather',r.text)
    def test_no_fake_transfer(self):
        self.assertIn('no live human agent',self.post('/api/voice/turn',{'Digits':'9'}).text)
    def test_silence_limit(self):
        self.assertIn('Hangup',self.post('/api/voice/turn?turn=1&empty=1').text)
    def test_turn_limit(self):
        self.assertIn('Hangup',self.post('/api/voice/turn?turn=12').text)
    def test_xml_escaped(self):
        from phone import say
        from xml.etree.ElementTree import Element,tostring
        root=Element('Response');say(root,'a < b & c');self.assertEqual(fromstring(tostring(root)).find('Say').text,'a < b & c')
    def test_wrong_account(self):
        self.assertEqual(self.post('/api/voice/incoming',{'AccountSid':'AC'+'3'*32}).status_code,403)
    def test_health(self):
        self.assertEqual(self.client.get('/api/health').status_code,200)

if __name__=='__main__': unittest.main(verbosity=2)
