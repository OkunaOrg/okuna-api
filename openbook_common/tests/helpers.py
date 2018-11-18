from faker import Faker
from django.conf import settings
from mixer.backend.django import mixer

from openbook_auth.models import User
from openbook_circles.models import Circle

fake = Faker()


def make_authentication_headers_for_user(user):
    auth_token = user.auth_token.key
    return {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}


def make_fake_post_text():
    return fake.text(max_nb_chars=settings.POST_MAX_LENGTH)


def make_fake_post_comment_text():
    return fake.text(max_nb_chars=settings.POST_COMMENT_MAX_LENGTH)


def make_user():
    return mixer.blend(User)


def make_circle(creator):
    return mixer.blend(Circle, creator=creator)
