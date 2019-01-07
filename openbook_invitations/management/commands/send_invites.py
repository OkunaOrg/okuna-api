from smtplib import SMTPException

from django.core.management.base import BaseCommand
from openbook_invitations.models import UserInvite


class Command(BaseCommand):
    help = 'Sends invitation emails for populated UserInvite models'

    def handle(self, *args, **options):
        user_invites = UserInvite.objects.all()
        for user in user_invites:
            if user.email is not None:
                try:
                    user.send_invite_email()
                    user.invite_email_sent = True
                    user.save()
                except SMTPException as e:
                    self.stderr.write('Exception occurred during send_invite_email', e)
        self.stdout.write(self.style.SUCCESS('Successfully sent invitation emails'))
