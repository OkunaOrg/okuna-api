from django.apps import AppConfig


class OpenbookPostsConfig(AppConfig):
    name = 'openbook_posts'

    def ready(self):
        from . import signals
