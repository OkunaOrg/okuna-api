import jwt
from django.conf import settings
from django.db import models

# Create your models here.
from django.utils import timezone
from django.db.models import Q
from django.db.models import Count

from openbook.settings import COLOR_ATTR_MAX_LENGTH
from openbook_auth.models import User
from openbook_circles.models import Circle
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_community_invite_model, \
    get_community_moderator_user_action_log_model
from openbook_common.validators import hex_color_validator
from openbook_communities.validators import community_name_characters_validator


class Community(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_communities', null=False,
                                blank=False)
    name = models.CharField(_('name'), max_length=settings.COMMUNITY_NAME_MAX_LENGTH, blank=False, null=False,
                            unique=True, validators=(community_name_characters_validator,))
    title = models.CharField(_('title'), max_length=settings.COMMUNITY_TITLE_MAX_LENGTH, blank=False, null=False, )
    description = models.CharField(_('description'), max_length=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH, blank=False,
                                   null=True, )
    rules = models.CharField(_('rules'), max_length=settings.COMMUNITY_RULES_MAX_LENGTH, blank=False,
                             null=True)
    circle = models.OneToOneField(Circle, on_delete=models.CASCADE, null=False, blank=False)
    avatar = models.ImageField(_('avatar'), blank=False, null=True)
    cover = models.ImageField(_('cover'), blank=False, null=True)
    created = models.DateTimeField(editable=False)
    members = models.ManyToManyField(User, related_name='communities')
    moderators = models.ManyToManyField(User, related_name='moderated_communities')
    administrators = models.ManyToManyField(User, related_name='administrated_communities')
    banned_users = models.ManyToManyField(User, related_name='banned_of_communities')
    COMMUNITY_TYPES = (
        ('P', 'Public'),
        ('T', 'Private'),
    )
    type = models.CharField(editable=False, blank=False, null=False, choices=COMMUNITY_TYPES, default='P', max_length=2)
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    user_adjective = models.CharField(_('user adjective'), max_length=settings.COMMUNITY_USER_ADJECTIVE_MAX_LENGTH,
                                      blank=False, null=True, )
    users_adjective = models.CharField(_('users adjective'), max_length=settings.COMMUNITY_USERS_ADJECTIVE_MAX_LENGTH,
                                       blank=False, null=True, )

    class Meta:
        verbose_name_plural = 'communities'

    @classmethod
    def is_user_with_username_invited_to_community_with_name(cls, username, community_name):
        CommunityInvite = get_community_invite_model()
        return CommunityInvite.is_user_with_username_invited_to_community_with_name(username=username,
                                                                                    community_name=community_name)

    @classmethod
    def is_user_with_username_member_of_community_with_name(cls, username, community_name):
        return cls.objects.filter(name=community_name, members__username=username).exists()

    @classmethod
    def is_user_with_username_administrator_of_community_with_name(cls, username, community_name):
        return cls.objects.filter(name=community_name, administrators__username=username).exists()

    @classmethod
    def is_user_with_username_moderator_of_community_with_name(cls, username, community_name):
        return cls.objects.filter(name=community_name, moderators__username=username).exists()

    @classmethod
    def is_user_with_username_banned_from_community_with_name(cls, username, community_name):
        return cls.objects.filter(name=community_name, banned_users__username=username).exists()

    @classmethod
    def get_communities_with_query(cls, query):
        communities_query = Q(name__icontains=query)
        communities_query.add(Q(title__icontains=query), Q.OR)
        return cls.objects.filter(communities_query)

    @classmethod
    def get_trending_communities(cls):
        return cls.objects.annotate(Count('members')).all().order_by(
            '-members__count', '-created')

    @classmethod
    def is_community_with_name_private(cls, community_name):
        return cls.objects.filter(name=community_name, type='T').exists()

    @classmethod
    def create_community(cls, name, title, creator, color, type=None, user_adjective=None, users_adjective=None,
                         avatar=None, cover=None, description=None, rules=None):
        community_circle = Circle.create_circle(name=name, color=color)
        community = cls.objects.create(title=title, name=name, creator=creator, avatar=avatar, cover=cover, color=color,
                                       user_adjective=user_adjective, users_adjective=users_adjective,
                                       description=description, type=type, rules=rules, circle=community_circle)

        community.administrators.add(creator)
        community.members.add(creator)
        community.save()
        return community

    @classmethod
    def is_name_taken(cls, name):
        return cls.objects.filter(name=name).exists()

    @classmethod
    def get_community_with_name_members(cls, community_name, members_max_id):
        community = Community.objects.get(name=community_name)
        community_members_query = Q()

        if members_max_id:
            community_members_query.add(Q(id__lt=members_max_id), Q.AND)

        return community.members.filter(community_members_query)

    @classmethod
    def get_community_with_name_banned_users(cls, community_name, users_max_id):
        community = Community.objects.get(name=community_name)
        community_members_query = Q()

        if users_max_id:
            community_members_query.add(Q(id__lt=users_max_id), Q.AND)

        return community.banned_users.filter(community_members_query)

    @property
    def members_count(self):
        return self.members.all().count()

    def create_invite(self, creator, invited_user):
        CommunityInvite = get_community_invite_model()
        return CommunityInvite.create_community_invite(creator=creator, invited_user=invited_user, community=self)

    def create_moderator_user_ban_log(self, moderator, target_user):
        return self._create_moderator_user_action_log(action_type='B',
                                                      moderator=moderator,
                                                      target_user=target_user)

    def create_moderator_user_unban_log(self, moderator, target_user):
        return self._create_moderator_user_action_log(action_type='U',
                                                      moderator=moderator,
                                                      target_user=target_user)

    def _create_moderator_user_action_log(self, action_type, moderator, target_user):
        CommunityModeratorUserActionLog = get_community_moderator_user_action_log_model()
        return CommunityModeratorUserActionLog.create_community_moderator_user_action_log(community=self,
                                                                                          target_user=target_user,
                                                                                          action_type=action_type,
                                                                                          moderator=moderator)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Community, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class CommunityModeratorUserActionLog(models.Model):
    """
    A log for community moderators user actions such as banning/unbanning
    """
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+', null=False,
                                  blank=False)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='+', null=True,
                                    blank=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='moderators_user_actions_logs',
                                  null=False,
                                  blank=False)
    created = models.DateTimeField(editable=False)
    ACTION_TYPES = (
        ('B', 'Ban'),
        ('U', 'Unban'),
    )
    action_type = models.CharField(editable=False, blank=False, null=False, choices=ACTION_TYPES, max_length=2)

    @classmethod
    def create_community_moderator_user_action_log(cls, community, action_type, moderator, target_user):
        return cls.objects.create(community=community, action_type=action_type, moderator=moderator,
                                  target_user=target_user)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(CommunityModeratorUserActionLog, self).save(*args, **kwargs)


class CommunityInvite(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_communities_invites', null=False,
                                blank=False)
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='communities_invites', null=False,
                                     blank=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='invites', null=False,
                                  blank=False)

    class Meta:
        unique_together = (('invited_user', 'community', 'creator'),)

    @classmethod
    def create_community_invite(cls, creator, invited_user, community):
        return cls.objects.create(creator=creator, invited_user=invited_user, community=community)

    @classmethod
    def is_user_with_username_invited_to_community_with_name(cls, username, community_name):
        return cls.objects.filter(community__name=community_name, invited_user__username=username).exists()
