from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError, DatabaseError
from openbook_invitations.parsers import parse_kickstarter_csv, parse_indiegogo_csv, parse_conflicts_csv, \
    parse_indiegogo_csv_and_sanitise_usernames


class Command(BaseCommand):
    help = 'Imports backer data into UserInvite models'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Import from indiegogo typeform')

    def handle(self, *args, **options):
            if options['path']:
                filepath = options['path']
                self.handle_indiegogo(filepath)

    def handle_indiegogo(self, filepath):
        try:
            with transaction.atomic():
                parse_indiegogo_csv_and_sanitise_usernames(filepath)
        except IntegrityError as e:
            print('IntegrityError %s ' % e)
            self.stderr.write('Aborting import of file..')
            return
        except DatabaseError as e:
            print('DatabaseError %s ' % e)
            self.stderr.write('Aborting import of file..')
            return
        self.stdout.write(self.style.SUCCESS('Successfully altered data'))
