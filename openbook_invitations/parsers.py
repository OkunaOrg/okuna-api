import csv
import re
import secrets
from openbook_common.models import Badge
from openbook_common.utils.model_loaders import get_user_invite_model, get_user_model


def parse_kickstarter_csv(filepath):
    try:
        with open(filepath, newline='') as csvfile:
            backer_data_reader = csv.reader(csvfile, delimiter=',')
            header_row = next(backer_data_reader)
            name_col, email_col, username_col, badge_keyword_col, email_kick_col = get_column_numbers_for_kickstarter(header_row)
            for row in backer_data_reader:
                name = row[name_col]
                email = row[email_col]
                if email is None or email is '':
                    email = row[email_kick_col]
                username = sanitise_username(row[username_col])
                if username is None or username is '':
                    print('Username was empty for:', name)
                    username = get_temporary_username(email)
                    print('Using generated random username @', username)
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
                username = sanitise_username(row[username_col])
                badge_keyword = row[badge_keyword_col]
                if badge_keyword:
                    badge = Badge.objects.get(keyword=badge_keyword)
                else:
                    badge = None
                UserInvite = get_user_invite_model()

                if username is None or username == '0' or username is '':
                    print('Username was empty for:', name)
                    username = None
                invited_user = UserInvite.create_invite(name=name, email=email, username=username,
                                                        badge=badge)
                invited_user.save()
    except IOError as e:
        print('Unable to read file')
        raise e


def parse_indiegogo_csv_and_sanitise_usernames(filepath):
    try:
        with open(filepath, newline='') as csvfile:
            backer_data_reader = csv.reader(csvfile, delimiter=',')
            header_row = next(backer_data_reader)
            name_col, email_col, username_col, badge_keyword_col = get_column_numbers_for_indiegogo(header_row)
            for row in backer_data_reader:
                name = row[name_col]
                email = row[email_col]
                username = sanitise_username(row[username_col])
                badge_keyword = row[badge_keyword_col]
                if badge_keyword:
                    badge = Badge.objects.get(keyword=badge_keyword)
                else:
                    badge = None
                UserInvite = get_user_invite_model()
                if username is None or username == '0' or username is '':
                    print('Username was empty for:', name)
                    username = get_temporary_username(email)
                    print('Using generated random username @', username)
                print(username, email)
                update_invite(name=name, email=email, username=username, badge=badge)
    except IOError as e:
        print('Unable to read file')
        raise e


def update_invite(email, name=None, username=None, badge=None):
    UserInvite = get_user_invite_model()
    invites = UserInvite.objects.filter(email=email)
    if len(invites) == 2:
        invite = invites.filter(username=username).first()
        if invite is None:
            invite = invites.last()
    else:
        invite = invites.first()
    invite.username = username
    invite.save()
    print('New username is: ', invite.username)
    return invite


def parse_conflicts_csv(filepath):
    # Hack: Since username is unique, we populate name field with username during
    # parsing of this csv so we can import all records.
    # This is a one time operation before launch.
    try:
        with open(filepath, newline='') as csvfile:
            backer_data_reader = csv.reader(csvfile, delimiter=',')
            header_row = next(backer_data_reader)
            name_col, email_col = get_column_numbers_for_conflicts_csv(header_row)
            for row in backer_data_reader:
                email = row[email_col]
                username = row[name_col]
                UserInvite = get_user_invite_model()

                if username is None or username is '0' or username is '':
                    print('Username was empty for:', username)
                    continue
                invited_user = UserInvite.create_invite(name=username, email=email, username=None)
                invited_user.save()
    except IOError as e:
        print('Unable to read file')
        raise e


def sanitise_username(username):
    chars = '[@#!±$%^&*()=|/><?,:;\~`{}]'
    return re.sub(chars, '', username).lower().replace(' ', '_').replace('+', '_').replace('-', '_').replace('\\', '')


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
            email_kickstarter = index

    return name, email, username, badge_keyword, email_kickstarter


def get_column_numbers_for_conflicts_csv(first_row):
    for index, col in enumerate(first_row):
        if col == 'Chosen username':
            name = index
        elif col == 'Email':
            email = index

    return name, email


def get_temporary_username(email):
    username = email.split('@')[0]
    temp_username = sanitise_username(username) + str(secrets.randbelow(9999))
    User = get_user_model()
    while User.is_username_taken(temp_username):
        temp_username = username + str(secrets.randbelow(9999))

    return temp_username
