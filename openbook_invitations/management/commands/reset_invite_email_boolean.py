from django.core.management.base import BaseCommand
from django.db import transaction
from openbook_invitations.models import UserInvite
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Resets is_invite_email_sent boolean for un-used UserInvite' \
           ' models created going back X no of days provided in argument'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=str, help='Invites going back these many days will have their boolean'
                                                     ' reset if no user is created')

    def handle(self, *args, **options):
        if options['days']:
            no_of_days = options['days']
            self.reset_unused_invites(int(no_of_days))

    def reset_unused_invites(self, no_of_days):
        user_invites = UserInvite.objects.filter(
            is_invite_email_sent=True,
            created_user__isnull=True,
            created__gte=timezone.now() - timedelta(days=no_of_days)
        )

        total_count = user_invites.count()

        with transaction.atomic():
            for invite in user_invites.iterator():
                invite.is_invite_email_sent = False
                invite.save()

        self.stdout.write(self.style.SUCCESS('Successfully reset email boolean for %s invites' % total_count))
