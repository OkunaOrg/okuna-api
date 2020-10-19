import tempfile

from PIL import Image
from faker import Faker
from django.conf import settings
from mixer.backend.django import mixer
from openbook_auth.models import User, UserProfile
from openbook_categories.models import Category
from openbook_circles.models import Circle
from openbook_common.models import Emoji, EmojiGroup, Badge, Language
from openbook_common.utils.helpers import get_random_pastel_color
from openbook_communities.models import Community
from openbook_devices.models import Device
from openbook_hashtags.models import Hashtag
from openbook_lists.models import List
from openbook_moderation.models import ModerationCategory, ModeratedObjectLog, ModeratedObject, ModerationReport, \
    ModerationPenalty
from openbook_notifications.models import Notification
from openbook_common.models import ProxyBlacklistedDomain

fake = Faker()


def make_authentication_headers_for_user(user):
    auth_token = user.auth_token.key
    return {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}


def make_fake_post_text():
    return fake.text(max_nb_chars=settings.POST_MAX_LENGTH)


def make_fake_post_comment_text():
    return fake.text(max_nb_chars=settings.POST_COMMENT_MAX_LENGTH)


def make_user(username=None, invite_count=None, name=None, visibility=User.VISIBILITY_TYPE_OKUNA):
    if username and invite_count:
        user = mixer.blend(User, username=username, invite_count=invite_count, visibility=visibility)
    elif username:
        user = mixer.blend(User, username=username, visibility=visibility)
    elif invite_count:
        user = mixer.blend(User, invite_count=invite_count, visibility=visibility)
    else:
        user = mixer.blend(User, visibility=visibility)

    profile = make_profile(user, name=name)
    return user


def make_global_moderator():
    moderator = make_user()
    make_moderators_community(creator=moderator)
    return moderator


def make_badge():
    return mixer.blend(Badge)


def make_users(amount):
    users = mixer.cycle(amount).blend(User)
    for user in users:
        make_profile(user=user)
    return users


def make_profile(user=None, name=None):
    if name:
        return mixer.blend(UserProfile, user=user, name=name)

    return mixer.blend(UserProfile, user=user)


def make_emoji(group=None):
    return mixer.blend(Emoji, group=group)


def make_hashtag(name=None):
    hashtag_name = name if name else make_hashtag_name()
    return mixer.blend(Hashtag, name=hashtag_name, color=get_random_pastel_color())


def make_hashtag_name():
    return fake.word().lower()


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


def make_category():
    return mixer.blend(Category)


def make_user_cover():
    image = Image.new('RGB', (100, 100))
    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    image.save(tmp_file)
    tmp_file.seek(0)
    return tmp_file


def make_post_image():
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
    return fake.word().title()


def make_community_users_adjective():
    return fake.word().title()


def make_community_name():
    return fake.user_name().lower()


def make_community_title():
    return fake.user_name()


def make_category():
    return mixer.blend(Category)


def make_community_invites_enabled():
    return fake.boolean()


def make_community(creator=None, type=Community.COMMUNITY_TYPE_PUBLIC, name=None, title=None):
    if not creator:
        creator = make_user()

    if not name:
        name = make_community_name()

    if not title:
        title = make_community_title()

    community = creator.create_community(name=name, title=title, type=type,
                                         color=fake.hex_color(), description=make_community_description(),
                                         rules=make_community_rules(), user_adjective=make_community_user_adjective(),
                                         users_adjective=make_community_users_adjective(),
                                         categories_names=[make_category().name],
                                         invites_enabled=make_community_invites_enabled())
    return community


def make_moderators_community(creator, ):
    return make_community(name=settings.MODERATORS_COMMUNITY_NAME, creator=creator,
                          type=Community.COMMUNITY_TYPE_PRIVATE)


def make_private_community(creator):
    return make_community(creator=creator, type=Community.COMMUNITY_TYPE_PRIVATE)


def make_notification(owner, notification_type=None):
    if notification_type:
        return mixer.blend(Notification, owner=owner, notification_type=notification_type)
    else:
        return mixer.blend(Notification, owner=owner)


def make_device(owner):
    return mixer.blend(Device, owner=owner)


def make_moderation_category(severity=ModerationCategory.SEVERITY_MEDIUM):
    return mixer.blend(ModerationCategory, severity=severity)


def make_moderation_report_description():
    return fake.text(max_nb_chars=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH)


def make_moderated_object_description():
    return fake.text(max_nb_chars=settings.MODERATED_OBJECT_DESCRIPTION_MAX_LENGTH)


def make_list(creator):
    return mixer.blend(List, creator=creator)


def make_moderated_object(community=None, ):
    return mixer.blend(ModeratedObject, community=community)


def make_moderated_object_log(moderated_object=None):
    return mixer.blend(ModeratedObjectLog, moderated_object=moderated_object)


def make_moderated_object_report(moderated_object=None):
    return mixer.blend(ModerationReport, moderated_object=moderated_object)


def make_moderation_penalty(user):
    return mixer.blend(ModerationPenalty, user=user)


def make_random_language():
    return mixer.blend(Language)


def make_proxy_blacklisted_domain(domain):
    return mixer.blend(ProxyBlacklistedDomain, domain=domain)


def get_test_usernames():
    return [
        'j_oel',
        'j.o.e.l',
        'j03l',
        'j'
    ]


def get_test_valid_hashtags():
    return [
        '1337test',
        'hello',
        'thisisasomewhatmoderateword',
        'thisisatest123',
        'hello_123',
        '_heythere',
        'osmaodmoasmdoasodasdasdasdsassaa'
    ]


def get_test_invalid_hashtags():
    return [
        '1337',
        '',
        '!@#!@a',
        '.',
    ]


def get_test_videos():
    return [
        {
            'path': 'openbook_common/tests/files/test_video.mp4',
            'duration': 5.312,
            'width': 1280,
            'height': 720
        },
        {
            'path': 'openbook_common/tests/files/test_video.3gp',
            'duration': 40.667,
            'width': 176,
            'height': 144
        },
        {
            'path': 'openbook_common/tests/files/test_gif_medium.gif',
            'duration': 1.5,
            'width': 312,
            'height': 312
        },
        {
            'path': 'openbook_common/tests/files/test_gif_tiny.gif',
            'duration': 0.771,
            'width': 256,
            'height': 256
        }
    ]


def get_test_images():
    return [
        {
            'path': 'openbook_common/tests/files/test_image_tiny.png',
            'width': 272,
            'height': 170
        },
        {
            'path': 'openbook_common/tests/files/test_image_small.png',
            'width': 912,
            'height': 513
        },
        {
            'path': 'openbook_common/tests/files/test_image_medium.png',
            'width': 5891,
            'height': 2271
        },
        {
            'path': 'openbook_common/tests/files/test_image_tiny.jpg',
            'width': 300,
            'height': 300
        },
        {
            'path': 'openbook_common/tests/files/test_image_small.jpg',
            'width': 2192,
            'height': 2921
        },
        {
            'path': 'openbook_common/tests/files/test_image_medium.jpg',
            'width': 10751,
            'height': 4287
        },
    ]


def get_test_image():
    return get_test_images()[0]


def get_test_video():
    return get_test_videos()[0]


def get_post_links():
    return [
        'https://www.okuna.io/',
        'www.techcrunch.com/',
        'https://bbc.co.uk/',
        'google.com?filter=evil/',
        'www.blablacar.com/i/rest/results/',
        'https://longwebsite.social/?url=https%3A%2F%2Ftest.com%3Fyes%3Dtrue'
    ]
