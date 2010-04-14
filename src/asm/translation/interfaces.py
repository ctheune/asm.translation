# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.interface.common.sequence


class ILanguageProfile(zope.interface.common.sequence.ISequence):
    """A list of language ISO codes. The first language is the default/fallback
    language."""
    pass
