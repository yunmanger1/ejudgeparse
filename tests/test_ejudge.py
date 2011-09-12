import unittest
from StringIO import StringIO

from iniparse import ini

class test_normal(unittest.TestCase):
    s1 = """
[global]    
contest_id = 1

[section]
just = "what?"
just = kidding

[section1]
help = yourself
but = alsome
"""

    s2 = """
contest_id = 1

[section]
just = "what?"
just = kidding

[section1]
help = yourself
but = alsome
"""

    s3 = """
contest_id = 1

@if host != "server"
[section]
just = "what?"
just = kidding
@else
[section]
help = yourself
but = alsome
@end

; asdasdd
"""

    def test_001(self):
        """ test simple conf """
        sio = StringIO(self.s1)
        cfg = ini.INIConfig(sio)
        print
        print cfg

    def test_002(self):
        """ test simple conf """
        sio = StringIO(self.s2)
        cfg = ini.INIConfig(sio)
        print
        print cfg

    def test_003(self):
        """ test simple conf """
        sio = StringIO(self.s3)
        cfg = ini.INIConfig(sio)
        print
        print cfg

    def test_004(self):
        """ test simple conf """
        cfg = ini.INIConfig(open('/home/german/judges/000001/conf/serve.cfg'))
        print
        print cfg
        print len(cfg.f('problem', abstract = ''))
        print cfg['problem']

class suite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self, [
                unittest.makeSuite(test_normal, 'test'),
    ])
