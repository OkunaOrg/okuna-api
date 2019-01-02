import csv
import getopt
import sys
from django.db import IntegrityError
from openbook_invitations.models import UserInvite


def kickstarter_csv_parser(filepath):

    try:
        with open(filepath, newline='') as csvfile:
            backer_data_reader = csv.reader(csvfile, delimiter=',')
            next(backer_data_reader)  # skip first line
            for row in backer_data_reader:
                name = row[2]
                email = row[3]
                username = row[17]
                badge_keyword = row[29]
                invited_user = UserInvite(name=name, email=email, username=username, badge_keyword=badge_keyword)
                invited_user.save()
    except IOError:
        print('Unable to read file')

