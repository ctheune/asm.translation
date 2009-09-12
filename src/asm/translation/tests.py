# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt

import unittest
from zope.app.testing.functional import FunctionalDocFileSuite
import asm.translation.testing


def test_suite():
    suite = unittest.TestSuite()
    t = FunctionalDocFileSuite('translation.txt', package='asm.translation')
    t.layer = asm.translation.testing.TestLayer
    suite.addTest(t)
    return suite
