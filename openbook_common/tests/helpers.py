import tempfile

from PIL import Image
from faker import Faker
from django.conf import settings
from mixer.backend.django import mixer
from openbook_auth.models import User, UserProfile
from openbook_circles.models import Circle
from openbook_common.models import Emoji, EmojiGroup

fake = Faker()


def make_authentication_headers_for_user(user):
    auth_token = user.auth_token.key
    return {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}


def make_fake_post_text():
    return fake.text(max_nb_chars=settings.POST_MAX_LENGTH)


def make_fake_post_comment_text():
    return fake.text(max_nb_chars=settings.POST_COMMENT_MAX_LENGTH)


def make_user():
    user = mixer.blend(User)
    profile = make_profile(user)
    return user


def make_profile(user=None):
    return mixer.blend(UserProfile, user=user)


def make_emoji(group=None):
    return mixer.blend(Emoji, group=group)


def make_emoji_group():
    return mixer.blend(EmojiGroup)


def make_circle(creator):
    return mixer.blend(Circle, creator=creator)


def make_user_bio():
    return fake.text(max_nb_chars=settings.PROFILE_BIO_MAX_LENGTH)


def make_user_location():
    return fake.text(max_nb_chars=settings.PROFILE_LOCATION_MAX_LENGTH)


def make_user_birth_date():
    return fake.date_of_birth(minimum_age=16)


def make_user_avatar():
    image = Image.new('RGB', (100, 100))
    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    image.save(tmp_file)
    tmp_file.seek(0)
    return tmp_file


def make_user_cover():
    image = Image.new('RGB', (100, 100))
    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    image.save(tmp_file)
    tmp_file.seek(0)
    return tmp_file
