import csv
import re

from openbook_common.models import Badge
from openbook_common.utils.model_loaders import get_user_invite_model


def parse_kickstarter_csv(filepath):
    try:
        with open(filepath, newline='') as csvfile:
            backer_data_reader = csv.reader(csvfile, delimiter=',')
            header_row = next(backer_data_reader)
            name_col, email_col, username_col, badge_keyword_col = get_column_numbers_for_kickstarter(header_row)
            for row in backer_data_reader:
                name = row[name_col]
                email = row[email_col]
                username = sanitise_username(row[username_col])
                if username is None or username is '':
                    print('Username was empty for:', name)
                    continue
                badge_keyword = row[badge_keyword_col]
                badge = Badge.objects.get(keyword=badge_keyword)
                UserInvite = get_user_invite_model()
                UserInvite.create_invite(name=name, email=email, username=username,
                                         badge=badge)
    except IOError as e:
        print('Unable to read file')
        raise e


def parse_indiegogo_csv(filepath):
    try:
        with open(filepath, newline='') as csvfile:
            backer_data_reader = csv.reader(csvfile, delimiter=',')
            header_row = next(backer_data_reader)
            name_col, email_col, username_col, badge_keyword_col = get_column_numbers_for_indiegogo(header_row)
            for row in backer_data_reader:
                name = row[name_col]
                email = row[email_col]
                username = row[username_col]
                badge_keyword = row[badge_keyword_col]
                badge = Badge.objects.get(keyword=badge_keyword)
                UserInvite = get_user_invite_model()

                if username is None or username is '0' or username is '':
                    print('Username was empty for:', name)
                    continue
                invited_user = UserInvite.create_invite(name=name, email=email, username=username,
                                                        badge_keyword=badge_keyword, badge=badge)
                invited_user.save()
    except IOError as e:
        print('Unable to read file')
        raise e


def sanitise_username(username):
    chars = '[@#!±$%^&*()=|/><?,:;\~`{}]'
    return re.sub(chars, '', username).lower().replace(' ', '_').replace('+', '_').replace('-', '_')


def get_column_numbers_for_indiegogo(first_row):
    for index, col in enumerate(first_row):
        if col == 'Name':
            name = index
        elif col == 'Username':
            username = index
        elif col == 'Badge Keyword':
            badge_keyword = index
        elif col == 'Email':
            email = index

    return name, email, username, badge_keyword


def get_column_numbers_for_kickstarter(first_row):
    for index, col in enumerate(first_row):
        if col == 'Backer Name':
            name = index
        elif col == 'To What Email Should We Send Your Early Access To? ' \
                    '(Please Provide A Valid Address. We Won\'t Be Able To Reach Out To You If You Don\'t.)':
            email = index
        elif col == 'What @Username Would You Like To Claim/Reseve? ' \
                    '(2 32 Characters, Letters, Numbers, Periods And Underscores)':
            username = index
        elif col == 'Badge Keyword':
            badge_keyword = index
        elif col == 'Email':
            email = index

    return name, email, username, badge_keyword
