from smtplib import SMTPException

from django.core.management.base import BaseCommand
from django.db import transaction

from openbook_invitations.models import UserInvite


class Command(BaseCommand):
    help = 'Sends invitation emails for populated UserInvite models'

    def handle(self, *args, **options):
        user_invites = UserInvite.objects.filter(is_invite_email_sent=False)

        for user in user_invites:
            if user.email is not None:
                with transaction.atomic():
                    try:
                        user.send_invite_email()
                    except Exception as e:
                        self.stderr.write('Exception occurred during send_invite_email')
        self.stdout.write(self.style.SUCCESS('Successfully sent invitation emails'))
