import csv
import getopt
import sys
from django.db import DatabaseError

from openbook_common.utils.model_loaders import get_user_invite_model
from openbook_invitations.models import UserInvite


def parse_kickstarter_csv(filepath):
    try:
        with open(filepath, newline='') as csvfile:
            backer_data_reader = csv.reader(csvfile, delimiter=',')
            next(backer_data_reader)  # skip first line
            for row in backer_data_reader:
                name = row[2]
                email = row[3]
                username = row[17]
                badge_keyword = row[29]
                UserInvite = get_user_invite_model()

                invited_user = UserInvite.create_invite(name=name, email=email, username=username, badge_keyword=badge_keyword)
                invited_user.save()
    except IOError as e:
        print('Unable to read file')
        raise e


def parse_indiegogo_csv(filepath):
    try:
        with open(filepath, newline='') as csvfile:
            backer_data_reader = csv.reader(csvfile, delimiter=',')
            next(backer_data_reader)  # skip first line
            for row in backer_data_reader:
                name = row[7]
                email = row[8]
                username = row[41]
                badge_keyword = row[36]
                UserInvite = get_user_invite_model()

                if username == '0':
                    username = None
                invited_user = UserInvite.create_invite(name=name, email=email, username=username, badge_keyword=badge_keyword)
                invited_user.save()
    except IOError as e:
        print('Unable to read file')
        raise e





