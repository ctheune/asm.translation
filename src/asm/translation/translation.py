# Copyright (c) 2009 Assembly Organizing
# See also LICENSE.txt

import asm.cms
import asm.cms.interfaces
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
    zope.component.adapts(asm.cms.IPage, asm.cms.ICMSSkin)

    def __init__(self, page, request):
        self.preferred = []
        self.acceptable = []
        for edition in page.editions:
            if lang2tag(fallback()) in edition.parameters:
                self.preferred.append(edition)
            else:
                self.acceptable.append(edition)


class RetailEditionSelector(object):

    zope.interface.implements(asm.cms.IEditionSelector)
    zope.component.adapts(asm.cms.IPage, asm.cms.IRetailSkin)

    def __init__(self, page, request):
        # XXX Need to make this more pluggable
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

        def get_editions(tags):
            result = []
            for tag in tags:
                tag = lang2tag(tag)
                for edition in page.editions:
                    if tag in edition.parameters:
                        result.append(edition)
            return result

        # Always prefer at most 1 language. However we have to make
        # sure that we have a matching edition before deciding which
        # one is the preferred. get_editions() will drop any language
        # for which no edition exists. The remaining editions that
        # could have been preferred are acceptable instead.
        self.preferred = get_editions(preferred_langs)
        self.acceptable = get_editions(acceptable_langs)
        self.acceptable[:0] = self.preferred[1:]
        del self.preferred[1:]


class ITranslation(zope.interface.Interface):

    language = zope.schema.Choice(
        title=u'Language to translate to',
        source=LanguageSource())


class TranslationMenu(grok.Viewlet):

    grok.viewletmanager(asm.cms.PageActionGroups)
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
            try:
                edition = self.context.page.getEdition(p)
            except KeyError:
                edition = None

            version = {}
            version['class'] = ''
            version['label'] = LANGUAGE_LABELS.get(lang, lang)
            version['hint'] = []
            version['changed'] = datetime.datetime.now(edition.modified.tzinfo) - edition.modified

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
        p = self.context.parameters.replace(lang2tag('*'), lang2tag(language))
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
