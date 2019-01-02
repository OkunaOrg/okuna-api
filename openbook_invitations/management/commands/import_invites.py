from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from openbook_invitations.parsers import parse_kickstarter_csv


class Command(BaseCommand):
    help = 'Imports backer data into UserInvite models'

    def add_arguments(self, parser):
        parser.add_argument('--kickstarter', type=str, help='Import from kickstarter csv')
        parser.add_argument('--indiegogo', type=str, help='Import from indiegogo typeform')

    def handle(self, *args, **options):
        if options['kickstarter']:
            filepath = options['kickstarter']
            try:
                with transaction.atomic():
                    parse_kickstarter_csv(filepath)
            except IntegrityError as e:
                print('IntegrityError %s ' % e)
            self.stdout.write(self.style.SUCCESS('Successfully imported data'))
