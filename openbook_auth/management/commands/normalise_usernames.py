from django.core.management.base import BaseCommand
import logging
import re
import unicodedata
from openbook_common.utils.model_loaders import get_user_model

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Normalises all usernames in the user model'

    def handle(self, *args, **options):
        User = get_user_model()

        users = User.objects.all()
        for user in users:
            old_username = user.username
            # convert to ascii
            normalised_username = unicodedata.normalize('NFD', old_username).encode('ascii', 'ignore').decode('utf-8')
            normalised_username = self.sanitise_username(normalised_username)

            logger.info('Normalised username {0}  to   {1}'.format(old_username, normalised_username))

    def sanitise_username(self, username):
        chars = '[@#!±$%^&*()=|/><?,:;\~`{}]'
        return re.sub(chars, '', username).lower().replace(' ', '_').replace('+', '_').replace('-', '_').replace('\\', '')
