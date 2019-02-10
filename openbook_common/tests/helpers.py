import tempfile

from PIL import Image
from faker import Faker
from django.conf import settings
from mixer.backend.django import mixer
from openbook_auth.models import User, UserProfile
from openbook_categories.models import Category
from openbook_circles.models import Circle
from openbook_common.models import Emoji, EmojiGroup, Badge

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


def make_badge():
    return mixer.blend(Badge)


def make_users(amount):
    users = mixer.cycle(amount).blend(User)
    for user in users:
        make_profile(user=user)
    return users


def make_profile(user=None):
    return mixer.blend(UserProfile, user=user)


def make_emoji(group=None):
    return mixer.blend(Emoji, group=group)


def make_emoji_group(is_reaction_group=False):
    return mixer.blend(EmojiGroup, is_reaction_group=is_reaction_group)


def make_reactions_emoji_group():
    return mixer.blend(EmojiGroup, is_reaction_group=True)


def make_circle(creator):
    return mixer.blend(Circle, creator=creator)


def make_user_bio():
    return fake.text(max_nb_chars=settings.PROFILE_BIO_MAX_LENGTH)


def make_user_location():
    return fake.text(max_nb_chars=settings.PROFILE_LOCATION_MAX_LENGTH)


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


def make_fake_list_name():
    return fake.text(max_nb_chars=settings.LIST_MAX_LENGTH)


def make_fake_circle_name():
    return fake.text(max_nb_chars=settings.CIRCLE_MAX_LENGTH)


def make_community_avatar():
    community_avatar = Image.new('RGB', (100, 100))
    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    community_avatar.save(tmp_file)
    tmp_file.seek(0)
    return tmp_file


def make_community_cover():
    community_cover = Image.new('RGB', (100, 100))
    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    community_cover.save(tmp_file)
    tmp_file.seek(0)
    return tmp_file


def make_community_description():
    return fake.text(max_nb_chars=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH)


def make_community_rules():
    return fake.text(max_nb_chars=settings.COMMUNITY_RULES_MAX_LENGTH)


def make_community_user_adjective():
    return fake.word()


def make_community_users_adjective():
    return fake.word()


def make_community_name():
    return fake.user_name().lower()


def make_community_title():
    return fake.user_name()


def make_category():
    return mixer.blend(Category)


def make_community_invites_enabled():
    return fake.boolean()


def make_community(creator, type='P'):
    community = creator.create_community(name=make_community_name(), title=make_community_title(), type=type,
                                         color=fake.hex_color(), description=make_community_description(),
                                         rules=make_community_rules(), user_adjective=make_community_user_adjective(),
                                         users_adjective=make_community_users_adjective(),
                                         categories_names=[make_category().name],
                                         invites_enabled=make_community_invites_enabled())
    return community
