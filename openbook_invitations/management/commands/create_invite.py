from django.core.management.base import BaseCommand

from openbook_common.utils.model_loaders import get_user_invite_model, get_badge_model

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates a user invite'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='The email to send the invite to')
        parser.add_argument('--username', type=str, help='The username to bind to the invite')
        parser.add_argument('--name', type=str, help='The name to bind to the invite')
        parser.add_argument('--badge', type=str, help='The keyword of the badge to bind to the invite')

    def handle(self, *args, **options):
        UserInvite = get_user_invite_model()

        name = options.get('name', None)
        email = options.get('email', None)
        username = options.get('username', None)
        badge_keyword = options.get('badge', None)

        badge = None

        if badge_keyword:
            Badge = get_badge_model()
            badge = Badge.objects.get(keyword=badge_keyword)

        user_invite = UserInvite.create_invite(name=name, email=email, username=username,
                                               badge=badge)

        logger.info('Invite created. Invite Token: ' + user_invite.token)
