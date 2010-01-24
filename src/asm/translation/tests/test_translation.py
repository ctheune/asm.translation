# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

import os.path
import zope.app.testing.functional
import asm.cms.edition
import asm.cms.testing
import gocept.selenium.ztk


TestLayer = zope.app.testing.functional.ZCMLLayer(
    os.path.join(os.path.dirname(__file__), 'ftesting.zcml'),
    __name__, 'TestLayer', allow_teardown=False)


class TranslationTests(asm.cms.testing.SeleniumTestCase):

    layer = gocept.selenium.ztk.Layer(TestLayer)

    def test_create_finnish_translation(self):
        s = self.selenium
        s.open('http://mgr:mgrpw@%s/++skin++cms/cms' % s.server)
        s.assertNotVisible('link=*Finnish*')
        s.click('xpath=//h3[contains(text(), "Language")]')
        s.assertVisible('link=*Finnish*')
        s.clickAndWait('link=*Finnish*')
        s.assertTextPresent('Translation created.')
