# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

# XXX this import is for fixing circular cmsui import bug. Remove it
# when cmsui is removed from core. #7345
import asm.cms.edition

import asm.cms.page
import asm.cms.htmlpage
import asm.cms.interfaces
import asm.translation.interfaces
import asm.translation.translation
import unittest
import zope.component
import zope.publisher.browser
import zope.app.testing.placelesssetup

class TranslationTests(unittest.TestCase):

    def setUp(self):
        zope.app.testing.placelesssetup.setUp()
        sm = zope.component.getGlobalSiteManager()
        sm.registerUtility(
            ['fi', 'en'], asm.translation.interfaces.ILanguageProfile)
        sm.registerUtility(
            asm.cms.htmlpage.HTMLPage,
            asm.cms.interfaces.IEditionFactory,
            name='htmlpage')

        self.page = asm.cms.page.Page('htmlpage')
        self.request = zope.publisher.browser.TestRequest()

    def tearDown(self):
        zope.app.testing.placelesssetup.tearDown()

    def _get_selector(self):
        return asm.translation.translation.RetailEditionSelector(
            self.page, self.request)

    def test_select_no_preference_no_editions(self):
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_no_preference_no_fallback(self):
        self.page.addEdition(['lang:en'])
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_no_preference_with_fallback(self):
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([edition_fi], selector.acceptable)

    def test_select_no_preference_with_fallback_and_other(self):
        edition_fi = self.page.addEdition(['lang:fi'])
        edition_en = self.page.addEdition(['lang:en'])
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([edition_fi], selector.acceptable)

    def test_select_with_cookie_no_edition(self):
        self.request._cookies['asm.translation.lang'] = 'fi'
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_with_cookie_and_matching_edition(self):
        self.request._cookies['asm.translation.lang'] = 'en'
        edition_en = self.page.addEdition(['lang:en'])
        selector = self._get_selector()
        self.assertEquals([edition_en], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_with_cookie_and_fallback_edition(self):
        self.request._cookies['asm.translation.lang'] = 'en'
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([edition_fi], selector.acceptable)

    def test_select_with_cookie_and_fallback_and_matching_editions(self):
        self.request._cookies['asm.translation.lang'] = 'en'
        edition_en = self.page.addEdition(['lang:en'])
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([edition_en], selector.preferred)
        self.assertEquals([edition_fi], selector.acceptable)

    def test_select_with_cookie_fallback_preferred_and_nonmatching_edition(self):
        self.request._cookies['asm.translation.lang'] = 'fi'
        edition_en = self.page.addEdition(['lang:en'])
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_with_cookie_preferred_and_matching_edition(self):
        self.request._cookies['asm.translation.lang'] = 'fi'
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([edition_fi], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_with_cookie_fallback_preferred_and_matching_editions(self):
        self.request._cookies['asm.translation.lang'] = 'fi'
        edition_en = self.page.addEdition(['lang:en'])
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([edition_fi], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_cookie_overrides_accept_language(self):
        self.request._cookies['asm.translation.lang'] = 'fi'
        self.request._environ['ACCEPT_LANGUAGE'] = 'en'
        edition_en = self.page.addEdition(['lang:en'])
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([edition_fi], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_unknown_accept_language_with_fallback(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'none'
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([edition_fi], selector.acceptable)

    def test_select_unknown_accept_language_without_fallback(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'none'
        edition = self.page.addEdition(['lang:en'])
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_unknown_accept_language_with_fallback_and_nonmatching_editions(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'none'
        edition_en = self.page.addEdition(['lang:en'])
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([], selector.preferred)
        self.assertEquals([edition_fi], selector.acceptable)

    def test_select_fi_higher_priority_than_en_with_fi_edition(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'fi,en;q=0.8'
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([edition_fi], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_fi_higher_priority_than_en_with_en_edition(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'fi,en;q=0.8'
        edition = self.page.addEdition(['lang:en'])
        selector = self._get_selector()
        self.assertEquals([edition], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_fi_higher_priority_than_en_with_en_and_fi_editions(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'fi,en;q=0.8'
        edition_en = self.page.addEdition(['lang:en'])
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([edition_fi], selector.preferred)
        self.assertEquals([edition_en], selector.acceptable)

    def test_select_en_higher_priority_than_fi_with_fi_edition(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'en,fi;q=0.8'
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([edition_fi], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_en_higher_priority_than_fi_with_en_edition(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'en,fi;q=0.8'
        edition = self.page.addEdition(['lang:en'])
        selector = self._get_selector()
        self.assertEquals([edition], selector.preferred)
        self.assertEquals([], selector.acceptable)

    def test_select_en_higher_priority_than_fi_with_en_and_fi_editions(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'en,fi;q=0.8'
        edition_en = self.page.addEdition(['lang:en'])
        edition_fi = self.page.addEdition(['lang:fi'])
        selector = self._get_selector()
        self.assertEquals([edition_en], selector.preferred)
        self.assertEquals([edition_fi], selector.acceptable)

    def test_select_en_with_multiple_en_editions(self):
        self.request._environ['ACCEPT_LANGUAGE'] = 'en'
        edition_en_draft = self.page.addEdition(['lang:en', 'draft'])
        edition_en_published = self.page.addEdition(['lang:en', 'published'])
        selector = self._get_selector()
        self.assertEquals(
            [edition_en_draft, edition_en_published], selector.preferred)
        self.assertEquals([], selector.acceptable)
