import tempfile

from PIL import Image
from faker import Faker
from django.conf import settings
from mixer.backend.django import mixer
from openbook_auth.models import User, UserProfile
from openbook_categories.models import Category
from openbook_circles.models import Circle
from openbook_common.models import Emoji, EmojiGroup, Badge
from openbook_devices.models import Device
from openbook_notifications.models import Notification
from openbook_reports.models import ReportCategory

fake = Faker()


def make_authentication_headers_for_user(user):
    auth_token = user.auth_token.key
    return {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}


def make_fake_post_text():
    return fake.text(max_nb_chars=settings.POST_MAX_LENGTH)


def make_fake_post_comment_text():
    return fake.text(max_nb_chars=settings.POST_COMMENT_MAX_LENGTH)


def make_user(username=None):
    if username:
        user = mixer.blend(User, username=username)
    else:
        user = mixer.blend(User)

    profile = make_profile(user)
    return user


def make_superuser():
    user = mixer.blend(User, is_superuser=True)
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


def make_member_of_community_with_admin(community, admin):
    user = make_user()
    admin.invite_user_with_username_to_community_with_name(username=user.username, community_name=community.name)
    user.join_community_with_name(community.name)

    return user


def make_community(creator, type='P'):
    community = creator.create_community(name=make_community_name(), title=make_community_title(), type=type,
                                         color=fake.hex_color(), description=make_community_description(),
                                         rules=make_community_rules(), user_adjective=make_community_user_adjective(),
                                         users_adjective=make_community_users_adjective(),
                                         categories_names=[make_category().name],
                                         invites_enabled=make_community_invites_enabled())
    return community


def make_report_category():
    return ReportCategory.objects.get(pk=1)


def make_report_comment_text():
    return fake.text(max_nb_chars=settings.REPORT_COMMENT_MAX_LENGTH)



def make_notification(owner):
    return mixer.blend(Notification, owner=owner)


def make_device(owner):
    return mixer.blend(Device, owner=owner)


def make_post_report_for_public_post():
    user = make_user()
    post = user.create_public_post(text=make_fake_post_text())

    reporting_user = make_user()
    post_report = reporting_user.report_post_with_id(post_id=post.pk,
                                                     category_id=make_report_category().id,
                                                     comment=make_report_comment_text())

    return user, reporting_user, post, post_report


def make_post_report_for_community_post():
    admin = make_user()
    community = make_community(admin, type='T')
    post = admin.create_community_post(text=make_fake_post_text(), community_name=community.name)

    reporting_user = make_user()
    admin.invite_user_with_username_to_community_with_name(username=reporting_user.username, community_name=community.name)
    reporting_user.join_community_with_name(community.name)
    post_report = reporting_user.report_post_with_id(post_id=post.pk, category_id=make_report_category().id)

    return community, reporting_user, admin, post, post_report


def make_post_comment_report_for_public_post():
    user = make_user()
    post = user.create_public_post(text=make_fake_post_text())
    post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

    reporting_user = make_user()
    post_comment_report = reporting_user.report_post_comment_with_id_for_post_with_id(
        post_id=post.pk,
        post_comment_id=post_comment.pk,
        category_id=make_report_category().id,
        comment=make_report_comment_text()
    )

    return user, reporting_user, post, post_comment, post_comment_report


def make_post_comment_report_for_community_post():
    admin = make_user()
    community = make_community(admin, type='T')
    post = admin.create_community_post(text=make_fake_post_text(), community_name=community.name)
    post_comment = admin.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

    reporting_user = make_user()
    admin.invite_user_with_username_to_community_with_name(username=reporting_user.username, community_name=community.name)
    reporting_user.join_community_with_name(community.name)
    post_comment_report = reporting_user.report_post_comment_with_id_for_post_with_id(
        post_id=post.pk,
        post_comment_id=post_comment.pk,
        category_id=make_report_category().id,
        comment=make_report_comment_text()
    )

    return community, reporting_user, admin, post, post_comment, post_comment_report
