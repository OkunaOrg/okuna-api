from django.core.management.base import BaseCommand
import logging

from openbook_auth.models import User, bootstrap_user_circles, bootstrap_user_notifications_settings, \
    bootstrap_user_profile, bootstrap_user_auth_token

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fixes missing relationships in the user model'

    def handle(self, *args, **options):
        self._fix_missing_circles()
        self._fix_missing_notifications_settings()
        self._fix_missing_profile()
        self._fix_missing_auth_token()

    def _fix_missing_circles(self):
        users = User.objects.filter(connections_circle__isnull=True).all()
        users_count = users.count()
        logger.info('Found %d users with missing circles. Attempting fix.' % users_count)

        for user in users:
            logger.info('Fixing circles of user with id %d and username %s' % (user.pk, user.username))
            for connection in user.connections.all():
                connection.delete()

            for circle in user.circles.all():
                circle.delete()
            bootstrap_user_circles(user=user)

    def _fix_missing_notifications_settings(self):
        users = User.objects.filter(notifications_settings__isnull=True).all()
        users_count = users.count()
        logger.info('Found %d users with missing notifications_settings. Attempting fix.' % users_count)

        for user in users:
            logger.info('Fixing notifications_settings of user with id %d and username %s' % (user.pk, user.username))
            bootstrap_user_notifications_settings(user=user)

    def _fix_missing_profile(self):
        users = User.objects.filter(profile__isnull=True).all()
        users_count = users.count()
        logger.info('Found %d users with missing profiles.' % users_count)

        for user in users:
            logger.info('Fixing profile of user with id %d and username %s' % (user.pk, user.username))
            bootstrap_user_profile(user=user, is_of_legal_age=True, avatar=None, name='Openbook')

    def _fix_missing_auth_token(self):
        users = User.objects.filter(auth_token__isnull=True).all()
        users_count = users.count()
        logger.info('Found %d users with missing auth_tokens.' % users_count)

        for user in users:
            logger.info('Fixing auth_token of user with id %d and username %s' % (user.pk, user.username))
            bootstrap_user_auth_token(user=user)
