# Copyright (c) 2009 Assembly Organizing
# See also LICENSE.txt

import asm.cms
import grok
import zope.interface
import zope.schema


def select_initial_language():
    return set(['lang:en'])


@zope.component.adapter(asm.cms.IRetailSkin)
def select_retail_edition(request):
    for lang in request.headers.get('Accept-Language', '').split(','):
        lang = lang.split(';')[0]
        lang = lang.split('-')[0]
        lang = 'lang:%s' % lang
        return set([lang])
    return set(['lang:en'])


class ITranslation(zope.interface.Interface):

    # XXX Turn this static list into a contextual source which will not offer
    # languages that already exist.
    language = zope.schema.Choice(title=u'Language to translate to',
                                  values=['fi', 'en'])


class TranslationMenu(grok.Viewlet):

    grok.viewletmanager(asm.cms.Actions)
    grok.context(asm.cms.IEdition)


class Translate(asm.cms.Form):

    grok.context(asm.cms.IEdition)
    form_fields = grok.AutoFields(ITranslation)

    @grok.action(u'Translate')
    def translate(self, language):
        page = self.context.page
        translation = self.context.parameters.replace(
            'lang:*', 'lang:%s' % language)
        try:
            translation = page.getEdition(translation)
        except KeyError:
            translation = page.addEdition(translation)
            translation.copyFrom(self.context)
            self.flash(u'Translation created.')
        else:
            self.flash(u'Translation already exists.')
        self.redirect(self.url(translation, '@@edit'))
