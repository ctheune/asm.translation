# Copyright (c) 2009 Assembly Organizing
# See also LICENSE.txt

import os.path
import zope.app.testing.functional


TestLayer = zope.app.testing.functional.ZCMLLayer(
    os.path.join(os.path.dirname(__file__), 'ftesting.zcml'),
    __name__, 'TestLayer', allow_teardown=False)
