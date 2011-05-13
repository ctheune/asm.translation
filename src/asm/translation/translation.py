# Copyright (c) 2009 Assembly Organizing
# See also LICENSE.txt

import asm.cms
import asm.cms.interfaces
import asm.cmsui.base
import asm.cmsui.interfaces
import asm.translation.interfaces
import datetime
import grok
import zc.sourcefactory.basic
import zope.component
import zope.interface
import zope.schema

LANGUAGE_LABELS = {'en': 'English',
                   'de': 'German',
                   '': 'independent',
                   'fi': 'Finnish'}

default_languages = ['en', 'fi']


def tag2lang(tag):
    return tag.replace('lang:', '')


def lang2tag(lang):
    return 'lang:%s' % lang


def fallback():
    return current()[0]


def current():
    return zope.component.getUtility(
        asm.translation.interfaces.ILanguageProfile)


class LanguageSource(zc.sourcefactory.basic.BasicSourceFactory):

    def getValues(self):
        return current()

    def getTitle(self, value):
        return LANGUAGE_LABELS.get(value, value)


class LanguageLabels(grok.GlobalUtility):

    zope.interface.implements(asm.cms.interfaces.IEditionLabels)
    grok.name('lang')

    def lookup(self, tag):
        lang = tag2lang(tag)
        return LANGUAGE_LABELS.get(lang, lang)


def select_initial_language():
    return set([lang2tag(fallback())])


class Prefixes(object):

    zope.interface.implements(asm.cms.interfaces.IExtensionPrefixes)

    prefixes = set(['lang'])


class CMSEditionSelector(object):

    zope.interface.implements(asm.cms.IEditionSelector)
    zope.component.adapts(asm.cmsui.interfaces.ICMSSkin)

    def __init__(self, request):
        self.request = request

    def select(self, page):
        preferred = []
        acceptable = []
        for edition in page.editions:
            if lang2tag(fallback()) in edition.parameters:
                preferred.append(edition)
            else:
                acceptable.append(edition)
        return preferred, acceptable


class RetailEditionSelector(object):

    zope.interface.implements(asm.cms.IEditionSelector)
    zope.component.adapts(asm.cmsui.interfaces.IRetailSkin)

    def __init__(self, request):
        # XXX Need to make this more pluggable
        self.request = request
        request.response.setHeader('Vary', 'Cookie,Accept-Language')

        preferred_langs = {}

        # Prefer cookie if set
        if 'asm.translation.lang' in request.cookies:
            preferred_langs[request.cookies['asm.translation.lang']] = 1.0
        else:
            # If no cookie is set we'll prefer the browser setting
            for lang in request.headers.get('Accept-Language', '').split(','):
                lang_priority = lang.split(';')
                lang = lang_priority[0]
                lang = lang.split('-')[0]

                priority = 1.0
                if len(lang_priority) > 1:
                    priority_str = lang_priority[1][2:]
                    priority = float(priority_str)

                if preferred_langs.get(lang, 0) < priority:
                    preferred_langs[lang] = priority

        prioritized_langs = sorted(
            preferred_langs.items(),
            key=lambda x : x[1],
            reverse=True)
        preferred_langs = [lang[0] for lang in prioritized_langs]

        acceptable_langs = []
        if fallback() not in preferred_langs:
            acceptable_langs.append(fallback())
        # XXX Here's a special case: some old databases were created with an
        # empty string as the marker for 'language independent'. This feature
        # isn't used much but some editions still have it.
        acceptable_langs.append('')

        self.preferred_langs = preferred_langs
        self.acceptable_langs = acceptable_langs

    def select(self, page):
        # Select the preferred language by finding the one with the
        # highest priority that has at least one edition.
        preferred_langs = list(self.preferred_langs)
        acceptable_langs = list(self.acceptable_langs)
        page_editions = list(page.editions)
        preferred_language = None
        for language in preferred_langs:
            language_tag = lang2tag(language)
            for edition in page_editions:
                if language_tag in edition.parameters:
                    preferred_language = language
                    break
            if preferred_language is not None:
                break

        if preferred_language is not None:
            preferred_langs.remove(preferred_language)
            acceptable_langs = preferred_langs + acceptable_langs
            preferred_langs = [preferred_language]

        def get_editions(languages):
            result = []
            for language in languages:
                tag = lang2tag(language)
                for edition in page_editions:
                    if tag in edition.parameters:
                        result.append(edition)
            return result

        preferred = get_editions(preferred_langs)
        acceptable = get_editions(acceptable_langs)
        return preferred, acceptable


class ITranslation(zope.interface.Interface):

    language = zope.schema.Choice(
        title=u'Language to translate to',
        source=LanguageSource())


class TranslationMenu(grok.Viewlet):

    grok.viewletmanager(asm.cmsui.base.PageActionGroups)
    grok.context(asm.cms.IEdition)

    def current_language(self):
        for candidate in self.context.parameters:
            if candidate.startswith(lang2tag('')):
                return LANGUAGE_LABELS.get(tag2lang(candidate), candidate)

    def list_language_versions(self):
        parameters = self.context.parameters
        for lang in current():
            p = self.context.parameters.replace(
                lang2tag('*'), lang2tag(lang))
            edition = None
            try:
                # Try to find an edition in this language with exactly
                # identical other parameters
                edition = self.context.page.getEdition(p)
            except KeyError:
                # Try to find an edition in this language without caring for
                # the other parameters.
                for candidate in self.context.page.editions:
                    if lang2tag(lang) in candidate.parameters:
                        edition = candidate
                        break

            version = {}
            version['class'] = ''
            version['label'] = LANGUAGE_LABELS.get(lang, lang)
            version['hint'] = []

            if edition is not None:
                version['url'] = self.view.url(edition, '@@edit')
            else:
                version['hint'] = '(not created yet)'
                version['url'] = self.view.url(
                    self.context, '@@translate',
                    data=dict(language=lang))

            if edition is self.context:
                version['class'] = 'selected'
            if lang == fallback():
                version['hint'] = '(is fallback)'

            yield version


class Translate(grok.View):

    grok.context(asm.cms.IEdition)
    form_fields = grok.AutoFields(ITranslation)

    def update(self, language):
        page = self.context.page
        parameters = asm.cms.edition.get_initial_parameters()
        p = parameters.replace(lang2tag('*'), lang2tag(language))
        try:
            translation = page.getEdition(p)
        except KeyError:
            translation = page.addEdition(p)
            translation.copyFrom(self.context)
            self.flash(u'Translation created.')
        else:
            self.flash(u'Translation already exists.')
        self.translation = translation

    def render(self):
        self.redirect(self.url(self.translation, '@@edit'))
