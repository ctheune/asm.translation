# Copyright (c) 2009 Assembly Organizing
# See also LICENSE.txt

import asm.cms
import grok
import zope.interface
import zope.schema


LANGUAGE_LABELS = {'lang:en': 'English',
                   'lang:': 'independent',
                   'lang:fi': 'Finnish'}


class LanguageLabels(grok.GlobalUtility):

    zope.interface.implements(asm.cms.interfaces.IEditionLabels)
    grok.name('lang')

    def lookup(self, tag):
        return LANGUAGE_LABELS[tag]


def select_initial_language():
    return set(['lang:en'])


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
            if 'lang:en' in edition.parameters:
                self.preferred.append(edition)
            else:
                self.acceptable.append(edition)


class RetailEditionSelector(object):

    zope.interface.implements(asm.cms.IEditionSelector)
    zope.component.adapts(asm.cms.IPage, asm.cms.IRetailSkin)

    def __init__(self, page, request):
        # XXX This algorithm isn't optimal in all cases. E.g. if a user has a
        # preferred language selected but it isn't available then we go
        # directly to neutral/english instead of first checking for the
        # browser setting.

        # XXX Need to make this more pluggable
        request.response.setHeader('Vary', 'Cookie,Accept-Language')

        self.preferred = []
        self.acceptable = []
        preferred_langs = set()

        # Prefer cookie if set
        if 'asm.translation.lang' in request.cookies:
            preferred_langs.add(request.cookies['asm.translation.lang'])
        else:
            # If no cookie is set we'll prefer the browser setting
            for lang in request.headers.get('Accept-Language', '').split(','):
                lang = lang.split(';')[0]
                lang = lang.split('-')[0]
                preferred_langs.add(lang)

        preferred_langs = set('lang:%s' % lang for lang in preferred_langs)
        for edition in page.editions:
            if preferred_langs.intersection(edition.parameters):
                self.preferred.append(edition)

        # Otherwise we also accept language neutral or english
        for edition in page.editions:
            if 'lang:' in edition.parameters:
                self.acceptable.append(edition)
            if 'lang:en' in edition.parameters:
                self.acceptable.append(edition)


class ITranslation(zope.interface.Interface):

    # Issue #61: Turn static list of values into source.
    language = zope.schema.Choice(title=u'Language to translate to',
                                  values=['fi', 'en'])


class TranslationMenu(grok.Viewlet):

    grok.viewletmanager(asm.cms.PageActionGroups)
    grok.context(asm.cms.IEdition)

    def current_language(self):
        for candidate in self.context.parameters:
            if candidate.startswith('lang:'):
                return LANGUAGE_LABELS[candidate]

    def list_language_versions(self):
        parameters = self.context.parameters
        for lang in ['lang:en', 'lang:fi']:
            p = self.context.parameters.replace('lang:*', lang)
            lang_code = lang.split(':')[1]
            try:
                edition = self.context.page.getEdition(p)
            except KeyError:
                edition = None

            version = {}
            version['class'] = ''
            version['label'] = LANGUAGE_LABELS[lang]
            version['hint'] = []
            if edition is not None:
                version['url'] = self.view.url(edition, '@@edit')
            else:
                version['hint'] = '(not created yet)'
                version['url'] = self.view.url(
                    self.context, '@@translate',
                    data=dict(language=lang_code))

            if edition is self.context:
                version['class'] = 'selected'
            if lang == 'lang:en':
                version['hint'] = '(is fallback)'

            yield version


class Translate(grok.View):

    grok.context(asm.cms.IEdition)
    form_fields = grok.AutoFields(ITranslation)

    def update(self, language):
        page = self.context.page
        p = self.context.parameters.replace('lang:*', 'lang:%s' % language)
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
