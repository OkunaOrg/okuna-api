from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError, DatabaseError
from openbook_invitations.parsers import parse_kickstarter_csv, parse_indiegogo_csv, parse_conflicts_csv


class Command(BaseCommand):
    help = 'Imports backer data into UserInvite models'

    def add_arguments(self, parser):
        parser.add_argument('--kickstarter', type=str, help='Import from kickstarter csv')
        parser.add_argument('--indiegogo', type=str, help='Import from indiegogo typeform')
        parser.add_argument('--conflicts', type=str, help='Import from conflicts csv')

    def handle(self, *args, **options):
        if options['kickstarter']:
            filepath = options['kickstarter']
            self.handle_kickstarter(filepath)

        if options['indiegogo']:
            filepath = options['indiegogo']
            self.handle_indiegogo(filepath)

        if options['conflicts']:
            filepath = options['conflicts']
            self.handle_conflicts(filepath)

    def handle_kickstarter(self, filepath):
        try:
            with transaction.atomic():
                parse_kickstarter_csv(filepath)
        except IntegrityError as e:
            print('IntegrityError %s ' % e)
            self.stderr.write('Aborting import of file..')
            return
        except DatabaseError as e:
            print('DatabaseError %s ' % e)
            self.stderr.write('Aborting import of file..')
            return
        self.stdout.write(self.style.SUCCESS('Successfully imported data'))

    def handle_indiegogo(self, filepath):
        try:
            with transaction.atomic():
                parse_indiegogo_csv(filepath)
        except IntegrityError as e:
            print('IntegrityError %s ' % e)
            self.stderr.write('Aborting import of file..')
            return
        except DatabaseError as e:
            print('DatabaseError %s ' % e)
            self.stderr.write('Aborting import of file..')
            return
        self.stdout.write(self.style.SUCCESS('Successfully imported data'))

    def handle_conflicts(self, filepath):
        try:
            with transaction.atomic():
                parse_conflicts_csv(filepath)
        except IntegrityError as e:
            print('IntegrityError %s ' % e)
            self.stderr.write('Aborting import of file..')
            return
        except DatabaseError as e:
            print('DatabaseError %s ' % e)
            self.stderr.write('Aborting import of file..')
            return
        self.stdout.write(self.style.SUCCESS('Successfully imported data'))
