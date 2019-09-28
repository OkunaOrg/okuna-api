"""
Translation framework.

The app defines a base strategy abstract class for translation of text
that has a simple API.

This can be extended depending on the translation framework one wants to use
and configured accordingly in the settings.py

"""

from django.conf import settings
from django.utils.module_loading import import_string
from openbook_translation.strategies.base import InvalidTranslationStrategyError

DEFAULT_STRATEGY_ALIAS = 'default'


class TranslationStrategyManager:

    def __init__(self, config_name=DEFAULT_STRATEGY_ALIAS):
        if config_name not in settings.OS_TRANSLATION_CONFIG:
            raise InvalidTranslationStrategyError(
                "Could not find config for '%s' in settings.OS_TRANSLATION_CONFIG" % config_name
            )
        self.strategy_instance = self._create_translation_strategy(config_name)

    def _create_translation_strategy(self, name, **kwargs):
        try:
            # Try to get the OS_TRANSLATION_CONFIG entry for the given name first
            conf = settings.OS_TRANSLATION_CONFIG[name]
            params = {**conf, **kwargs}
            strategy = params.pop('STRATEGY')
            strategy_cls = import_string(strategy)
        except ImportError as e:
            raise InvalidTranslationStrategyError(
                "Could not find strategy '%s': %s" % (strategy, e))

        return strategy_cls(params)

    def get_instance(self):
        return self.strategy_instance


translation_strategy = TranslationStrategyManager(settings.OS_TRANSLATION_STRATEGY_NAME).get_instance()
