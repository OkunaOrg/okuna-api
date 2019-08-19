import json
import polib
import os, django
from django.conf import settings

MODERATION_CATEGORIES_PATH = os.path.join(settings.BASE_DIR, 'openbook_moderation/fixtures/moderation_categories.json')
PO_LOCALES_PATH = os.path.join(settings.BASE_DIR, 'locale')
FIELDS = ['title', 'description']

for language in settings.LANGUAGES:
    language_code = language[0]
    if language_code is 'en':
        continue
    print('Processing locale {0}'.format(language_code))

    po_locale = polib.pofile(os.path.join(PO_LOCALES_PATH, '{0}/LC_MESSAGES/django.po'.format(language_code)))
    po_dict = {}
    for entry in po_locale:
        po_dict[entry.msgid] = entry.msgstr

    with open(MODERATION_CATEGORIES_PATH, 'r') as f:
        categories_dict = json.load(f)

    for category in categories_dict:
        for field in FIELDS:
            field_value = category['fields']['{0}_en'.format(field)]
            try:
                field_locale_value = po_dict[field_value]
                category['fields']['{0}_{1}'.format(field, language_code)] = field_locale_value
            except KeyError:
                print('Field {0} not found in {1}/django.po'.format(field_value, language_code))

    with open(MODERATION_CATEGORIES_PATH, 'w') as json_file:
        json.dump(categories_dict, json_file, ensure_ascii=False)



