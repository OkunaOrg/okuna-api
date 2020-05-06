from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

# Create your models here.
from django.utils import timezone
from django.db.models import Q
from django.db.models import Count
from pilkit.processors import ResizeToFill, ResizeToFit

from openbook.settings import COLOR_ATTR_MAX_LENGTH
from openbook_auth.models import User
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_community_invite_model, \
    get_community_log_model, get_category_model, get_user_model, get_moderated_object_model, \
    get_community_notifications_subscription_model, get_community_new_post_notification_model, \
    get_community_invite_notification_model
from openbook_common.validators import hex_color_validator
from openbook_communities.helpers import upload_to_community_avatar_directory, upload_to_community_cover_directory
from openbook_communities.queries import make_search_communities_query_for_user, \
    make_search_joined_communities_query_for_user, make_get_joined_communities_query_for_user
from openbook_communities.validators import community_name_characters_validator
from openbook_moderation.models import ModeratedObject, ModerationCategory
from openbook_posts.models import Post
from imagekit.models import ProcessedImageField


class Community(models.Model):
    moderated_object = GenericRelation(ModeratedObject, related_query_name='communities')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_communities', null=False,
                                blank=False)
    name = models.CharField(_('name'), max_length=settings.COMMUNITY_NAME_MAX_LENGTH, blank=False, null=False,
                            unique=True, validators=(community_name_characters_validator,))
    title = models.CharField(_('title'), max_length=settings.COMMUNITY_TITLE_MAX_LENGTH, blank=False, null=False, )
    description = models.CharField(_('description'), max_length=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH, blank=False,
                                   null=True, )
    rules = models.TextField(_('rules'), max_length=settings.COMMUNITY_RULES_MAX_LENGTH, blank=False,
                             null=True)
    avatar = ProcessedImageField(verbose_name=_('avatar'), blank=False, null=True, format='JPEG',
                                 options={'quality': 90}, processors=[ResizeToFill(500, 500)],
                                 upload_to=upload_to_community_avatar_directory)
    cover = ProcessedImageField(verbose_name=_('cover'), blank=False, null=True, format='JPEG',
                                options={'quality': 90},
                                upload_to=upload_to_community_cover_directory,
                                processors=[ResizeToFit(width=1024, upscale=False)])
    created = models.DateTimeField(editable=False)
    starrers = models.ManyToManyField(User, related_name='favorite_communities')
    banned_users = models.ManyToManyField(User, related_name='banned_of_communities')
    COMMUNITY_TYPE_PRIVATE = 'T'
    COMMUNITY_TYPE_PUBLIC = 'P'
    COMMUNITY_TYPES = (
        (COMMUNITY_TYPE_PUBLIC, 'Public'),
        (COMMUNITY_TYPE_PRIVATE, 'Private'),
    )
    type = models.CharField(editable=False, blank=False, null=False, choices=COMMUNITY_TYPES, default='P', max_length=2)
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    user_adjective = models.CharField(_('user adjective'), max_length=settings.COMMUNITY_USER_ADJECTIVE_MAX_LENGTH,
                                      blank=False, null=True)
    users_adjective = models.CharField(_('users adjective'), max_length=settings.COMMUNITY_USERS_ADJECTIVE_MAX_LENGTH,
                                       blank=False, null=True)
    invites_enabled = models.BooleanField(_('invites enabled'), default=True)
    # This only happens if the community was reported and found with critical severity content
    is_deleted = models.BooleanField(
        _('is deleted'),
        default=False,
    )

    class Meta:
        verbose_name_plural = 'communities'

    @classmethod
    def is_user_with_username_invited_to_community_with_name(cls, username, community_name):
        CommunityInvite = get_community_invite_model()
        return CommunityInvite.is_user_with_username_invited_to_community_with_name(username=username,
                                                                                    community_name=community_name)

    @classmethod
    def is_user_with_username_subscribed_to_notifications_for_community_with_name(cls, username, community_name):
        CommunityNotificationsSubscription = get_community_notifications_subscription_model()
        return CommunityNotificationsSubscription.are_new_post_notifications_enabled_for_user_with_username_and_community_with_name(
            username=username,
            community_name=community_name)

    @classmethod
    def is_user_with_username_member_of_community_with_name(cls, username, community_name):
        return cls.objects.filter(name=community_name, memberships__user__username=username).exists()

    @classmethod
    def is_user_with_username_administrator_of_community_with_name(cls, username, community_name):
        return cls.objects.filter(name=community_name, memberships__user__username=username,
                                  memberships__is_administrator=True).exists()

    @classmethod
    def is_user_with_username_moderator_of_community_with_name(cls, username, community_name):
        return cls.objects.filter(name=community_name, memberships__user__username=username,
                                  memberships__is_moderator=True).exists()

    @classmethod
    def is_user_with_username_banned_from_community_with_name(cls, username, community_name):
        return cls.objects.filter(name=community_name, banned_users__username=username).exists()

    @classmethod
    def is_community_with_name_invites_enabled(cls, community_name):
        return cls.objects.filter(name=community_name, invites_enabled=True).exists()

    @classmethod
    def is_community_with_name_private(cls, community_name):
        return cls.objects.filter(name=community_name, type='T').exists()

    @classmethod
    def community_with_name_exists(cls, community_name):
        query = Q(name=community_name, is_deleted=False)
        return cls.objects.filter(query).exists()

    @classmethod
    def get_community_with_name_for_user_with_id(cls, community_name, user_id):
        query = Q(name=community_name, is_deleted=False)
        query.add(~Q(banned_users__id=user_id), Q.AND)
        return cls.objects.get(query)

    @classmethod
    def search_communities_with_query_for_user(cls, query, user, excluded_from_profile_posts=True):
        query = make_search_communities_query_for_user(query=query, user=user,
                                                       excluded_from_profile_posts=excluded_from_profile_posts)
        return cls.objects.filter(query)

    @classmethod
    def search_joined_communities_with_query_for_user(cls, query, user, excluded_from_profile_posts=True):
        query = make_search_joined_communities_query_for_user(query=query, user=user,
                                                              excluded_from_profile_posts=excluded_from_profile_posts)
        return cls.objects.filter(query)

    @classmethod
    def get_joined_communities_for_user(cls, user, excluded_from_profile_posts=True):
        query = make_get_joined_communities_query_for_user(user=user,
                                                           excluded_from_profile_posts=excluded_from_profile_posts)
        return cls.objects.filter(query)

    @classmethod
    def get_new_user_suggested_communities(cls):
        community_ids = [int(community_id) for community_id in settings.NEW_USER_SUGGESTED_COMMUNITIES.split(',')]
        return cls.objects.filter(id__in=community_ids, type=cls.COMMUNITY_TYPE_PUBLIC)

    @classmethod
    def get_trending_communities_for_user_with_id(cls, user_id, category_name=None):
        trending_communities_query = cls._make_trending_communities_query(category_name=category_name)
        trending_communities_query.add(~Q(banned_users__id=user_id), Q.AND)
        return cls._get_trending_communities_with_query(query=trending_communities_query)

    @classmethod
    def get_trending_communities(cls, category_name=None):
        trending_communities_query = cls._make_trending_communities_query(category_name=category_name)
        return cls._get_trending_communities_with_query(query=trending_communities_query)

    @classmethod
    def _get_trending_communities_with_query(cls, query):
        return cls.objects.annotate(Count('memberships')).filter(query).order_by(
            '-memberships__count', '-created')

    @classmethod
    def _make_trending_communities_query(cls, category_name=None):
        trending_communities_query = Q(type=cls.COMMUNITY_TYPE_PUBLIC, is_deleted=False)

        if category_name:
            trending_communities_query.add(Q(categories__name=category_name), Q.AND)

        return trending_communities_query

    @classmethod
    def create_community(cls, name, title, creator, color, type=None, user_adjective=None, users_adjective=None,
                         avatar=None, cover=None, description=None, rules=None, categories_names=None,
                         invites_enabled=None):
        # If its a private community and no invites_enabled
        if type is Community.COMMUNITY_TYPE_PRIVATE and invites_enabled is None:
            invites_enabled = False
        else:
            # The default for this field is not working when passed None?
            invites_enabled = True

        community = cls.objects.create(title=title, name=name, creator=creator, avatar=avatar, cover=cover, color=color,
                                       user_adjective=user_adjective, users_adjective=users_adjective,
                                       description=description, type=type, rules=rules,
                                       invites_enabled=invites_enabled)

        CommunityMembership.create_membership(user=creator, is_administrator=True, is_moderator=False,
                                              community=community)

        if categories_names:
            community.set_categories_with_names(categories_names=categories_names)

        community.save()
        return community

    @classmethod
    def is_name_taken(cls, name):
        return cls.objects.filter(name__iexact=name).exists()

    EXCLUDE_COMMUNITY_ADMINISTRATORS_KEYWORD = 'administrators'
    EXCLUDE_COMMUNITY_MODERATORS_KEYWORD = 'moderators'

    @classmethod
    def get_community_with_name_members(cls, community_name, members_max_id=None, exclude_keywords=None):
        community_members_query = Q(communities_memberships__community__name=community_name)

        if members_max_id:
            community_members_query.add(Q(id__lt=members_max_id), Q.AND)

        if exclude_keywords:
            community_members_query.add(
                cls._get_exclude_members_query_for_keywords(exclude_keywords=exclude_keywords),
                Q.AND)

        return User.objects.filter(community_members_query)

    @classmethod
    def search_community_with_name_members(cls, community_name, query, exclude_keywords=None):
        db_query = Q(communities_memberships__community__name=community_name)

        community_members_query = Q(communities_memberships__user__username__icontains=query)
        community_members_query.add(Q(communities_memberships__user__profile__name__icontains=query), Q.OR)

        db_query.add(community_members_query, Q.AND)

        if exclude_keywords:
            db_query.add(
                cls._get_exclude_members_query_for_keywords(exclude_keywords=exclude_keywords),
                Q.AND)

        return User.objects.filter(db_query)

    @classmethod
    def _get_exclude_members_query_for_keywords(cls, exclude_keywords):
        query = Q()

        if cls.EXCLUDE_COMMUNITY_ADMINISTRATORS_KEYWORD in exclude_keywords:
            query.add(Q(communities_memberships__is_administrator=False), Q.AND)

        if cls.EXCLUDE_COMMUNITY_MODERATORS_KEYWORD in exclude_keywords:
            query.add(Q(communities_memberships__is_moderator=False), Q.AND)

        return query

    @classmethod
    def get_community_with_name_administrators(cls, community_name, administrators_max_id=None):
        community_administrators_query = Q(communities_memberships__community__name=community_name,
                                           communities_memberships__is_administrator=True)

        if administrators_max_id:
            community_administrators_query.add(Q(communities_memberships__user__id__lt=administrators_max_id), Q.AND)

        return User.objects.filter(community_administrators_query)

    @classmethod
    def search_community_with_name_administrators(cls, community_name, query):
        db_query = Q(communities_memberships__community__name=community_name,
                     communities_memberships__is_administrator=True)

        community_members_query = Q(communities_memberships__user__username__icontains=query)
        community_members_query.add(Q(communities_memberships__user__profile__name__icontains=query), Q.OR)

        db_query.add(community_members_query, Q.AND)

        return User.objects.filter(db_query)

    @classmethod
    def get_community_with_name_moderators(cls, community_name, moderators_max_id=None):
        community_moderators_query = Q(communities_memberships__community__name=community_name,
                                       communities_memberships__is_moderator=True)

        if moderators_max_id:
            community_moderators_query.add(Q(communities_memberships__user__id__lt=moderators_max_id), Q.AND)

        return User.objects.filter(community_moderators_query)

    @classmethod
    def search_community_with_name_moderators(cls, community_name, query):
        db_query = Q(communities_memberships__community__name=community_name,
                     communities_memberships__is_moderator=True)

        community_members_query = Q(communities_memberships__user__username__icontains=query)
        community_members_query.add(Q(communities_memberships__user__profile__name__icontains=query), Q.OR)

        db_query.add(community_members_query, Q.AND)

        return User.objects.filter(db_query)

    @classmethod
    def get_community_with_name_banned_users(cls, community_name, users_max_id):
        community = Community.objects.get(name=community_name)
        community_members_query = Q()

        if users_max_id:
            community_members_query.add(Q(id__lt=users_max_id), Q.AND)

        return community.banned_users.filter(community_members_query)

    @classmethod
    def search_community_with_name_banned_users(cls, community_name, query):
        community = Community.objects.get(name=community_name)
        community_banned_users_query = Q(username__icontains=query)
        community_banned_users_query.add(Q(profile__name__icontains=query), Q.OR)
        return community.banned_users.filter(community_banned_users_query)

    @property
    def members_count(self):
        return self.memberships.all().count()

    def get_staff_members(self):
        User = get_user_model()
        staff_members_query = Q(communities_memberships__community_id=self.pk)
        staff_members_query.add(
            Q(communities_memberships__is_administrator=True) | Q(communities_memberships__is_moderator=True), Q.AND)
        return User.objects.filter(staff_members_query)

    def is_private(self):
        return self.type is self.COMMUNITY_TYPE_PRIVATE

    def update(self, title=None, name=None, description=None, color=None, type=None,
               user_adjective=None,
               users_adjective=None, rules=None, categories_names=None, invites_enabled=None):

        if name:
            self.name = name.lower()

        if title:
            self.title = title

        if type:
            self.type = type

        if color:
            self.color = color

        if description is not None:
            self.description = description

        if rules is not None:
            self.rules = rules

        if user_adjective is not None:
            self.user_adjective = user_adjective

        if users_adjective is not None:
            self.users_adjective = users_adjective

        if invites_enabled is not None:
            self.invites_enabled = invites_enabled

        if categories_names is not None:
            self.set_categories_with_names(categories_names=categories_names)

        self.save()

    def add_moderator(self, user):
        user_membership = self.memberships.get(user=user)
        user_membership.is_moderator = True
        user_membership.save()
        return user_membership

    def remove_moderator(self, user):
        user_membership = self.memberships.get(user=user)
        user_membership.is_moderator = False
        user_membership.save()
        return user_membership

    def add_administrator(self, user):
        user_membership = self.memberships.get(user=user)
        user_membership.is_administrator = True
        user_membership.save()
        return user_membership

    def remove_administrator(self, user):
        user_membership = self.memberships.get(user=user)
        user_membership.is_administrator = False
        user_membership.save()
        return user_membership

    def add_member(self, user):
        user_membership = CommunityMembership.create_membership(user=user, community=self)
        return user_membership

    def remove_member(self, user):
        user_membership = self.memberships.get(user=user)
        user_membership.delete()

    def set_categories_with_names(self, categories_names):
        self.clear_categories()
        Category = get_category_model()
        categories = Category.objects.filter(name__in=categories_names)
        self.categories.set(categories)

    def clear_categories(self):
        self.categories.clear()

    def create_invite(self, creator, invited_user):
        CommunityInvite = get_community_invite_model()
        return CommunityInvite.create_community_invite(creator=creator, invited_user=invited_user, community=self)

    def create_user_ban_log(self, source_user, target_user):
        return self._create_log(action_type='B',
                                source_user=source_user,
                                target_user=target_user)

    def create_user_unban_log(self, source_user, target_user):
        return self._create_log(action_type='U',
                                source_user=source_user,
                                target_user=target_user)

    def create_add_administrator_log(self, source_user, target_user):
        return self._create_log(action_type='AA',
                                source_user=source_user,
                                target_user=target_user)

    def create_remove_administrator_log(self, source_user, target_user):
        return self._create_log(action_type='RA',
                                source_user=source_user,
                                target_user=target_user)

    def create_add_moderator_log(self, source_user, target_user):
        return self._create_log(action_type='AM',
                                source_user=source_user,
                                target_user=target_user)

    def create_remove_moderator_log(self, source_user, target_user):
        return self._create_log(action_type='RM',
                                source_user=source_user,
                                target_user=target_user)

    def create_remove_post_log(self, source_user, target_user):
        return self._create_log(action_type='RP',
                                source_user=source_user,
                                target_user=target_user)

    def create_remove_post_comment_log(self, source_user, target_user):
        return self._create_log(action_type='RPC',
                                source_user=source_user,
                                target_user=target_user)

    def create_remove_post_comment_reply_log(self, source_user, target_user):
        return self._create_log(action_type='RPCR',
                                source_user=source_user,
                                target_user=target_user)

    def create_disable_post_comments_log(self, source_user, target_user, post):
        return self._create_log(action_type='DPC',
                                post=post,
                                source_user=source_user,
                                target_user=target_user)

    def create_enable_post_comments_log(self, source_user, target_user, post):
        return self._create_log(action_type='EPC',
                                post=post,
                                source_user=source_user,
                                target_user=target_user)

    def create_open_post_log(self, source_user, target_user, post):
        return self._create_log(action_type='OP',
                                post=post,
                                source_user=source_user,
                                target_user=target_user)

    def create_close_post_log(self, source_user, target_user, post):
        return self._create_log(action_type='CP',
                                post=post,
                                source_user=source_user,
                                target_user=target_user)

    def _create_log(self, action_type, source_user, target_user, post=None):
        CommunityModeratorUserActionLog = get_community_log_model()
        return CommunityModeratorUserActionLog.create_community_log(community=self,
                                                                    post=post,
                                                                    target_user=target_user,
                                                                    action_type=action_type,
                                                                    source_user=source_user)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()

        self.name = self.name.lower()

        if self.user_adjective:
            self.user_adjective = self.user_adjective.title()

        if self.users_adjective:
            self.users_adjective = self.users_adjective.title()

        return super(Community, self).save(*args, **kwargs)

    def delete_notifications(self):
        # Remove all community new post notifications
        CommunityNewPostNotification = get_community_new_post_notification_model()
        CommunityNewPostNotification.objects.filter(community_notifications_subscription__community_id=self.pk).delete()

        # Remove all community invite notifications
        CommunityInviteNotification = get_community_invite_notification_model()
        CommunityInviteNotification.objects.filter(community_invite__community_id=self.pk).delete()

    def soft_delete(self):
        self.is_deleted = True
        for post in self.posts.all().iterator():
            post.soft_delete()
        self.save()

    def unsoft_delete(self):
        self.is_deleted = False
        for post in self.posts:
            post.unsoft_delete()
        self.save()

    def count_pending_moderated_objects(self):
        ModeratedObject = get_moderated_object_model()
        return self.moderated_objects.filter(status=ModeratedObject.STATUS_PENDING).count()

    def __str__(self):
        return self.name


class CommunityMembership(models.Model):
    """
    An object representing the membership of a user in a community
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='communities_memberships', null=False,
                             blank=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='memberships', null=False,
                                  blank=False)
    is_administrator = models.BooleanField(_('is administrator'), default=False)
    is_moderator = models.BooleanField(_('is moderator'), default=False)
    created = models.DateTimeField(editable=False)

    class Meta:
        unique_together = (('user', 'community'),)
        indexes = [
            models.Index(fields=['community', 'user']),
            models.Index(fields=['community', 'user', 'is_administrator']),
            models.Index(fields=['community', 'user', 'is_moderator']),
        ]

    @classmethod
    def create_membership(cls, user, community, is_administrator=False, is_moderator=False):
        membership = cls.objects.create(user=user, community=community, is_administrator=is_administrator,
                                        is_moderator=is_moderator)

        return membership

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(CommunityMembership, self).save(*args, **kwargs)


class CommunityLog(models.Model):
    """
    A log for community moderators user actions such as banning/unbanning
    """
    source_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+', null=False,
                                    blank=False)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='+', null=True,
                                    blank=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='logs',
                                  null=False,
                                  blank=False)
    created = models.DateTimeField(editable=False)

    ACTION_TYPES = (
        ('B', 'Ban'),
        ('U', 'Unban'),
        ('AM', 'Add Moderator'),
        ('RM', 'Remove Moderator'),
        ('AA', 'Add Administrator'),
        ('RA', 'Remove Administrator'),
        ('OP', 'Open Post'),
        ('CP', 'Close Post'),
        ('RP', 'Remove Post'),
        ('RPC', 'Remove Post Comment'),
        ('DPC', 'Disable Post Comments'),
        ('EPC', 'Enable Post Comments'),
    )
    action_type = models.CharField(editable=False, blank=False, null=False, choices=ACTION_TYPES, max_length=5)

    @classmethod
    def create_community_log(cls, community, action_type, source_user, target_user, post=None):
        return cls.objects.create(community=community, action_type=action_type, source_user=source_user,
                                  target_user=target_user, post=post)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(CommunityLog, self).save(*args, **kwargs)


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


class CommunityNotificationsSubscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_notifications_subscriptions',
                                   null=False,
                                   blank=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='notifications_subscriptions',
                                  null=False,
                                  blank=False)
    new_post_notifications = models.BooleanField(default=False, blank=False)

    class Meta:
        unique_together = ('community', 'subscriber',)

    @classmethod
    def create_community_notifications_subscription(cls, subscriber, community):
        if not cls.objects.filter(community=community, subscriber=subscriber).exists():
            return cls.objects.create(subscriber=subscriber, community=community)

        community_notifications_subscription = cls.objects.get(subscriber=subscriber, community=community)
        community_notifications_subscription.save()

        return community_notifications_subscription

    @classmethod
    def get_or_create_community_notifications_subscription(cls, subscriber, community):
        try:
            community_notifications_subscription = cls.objects.get(subscriber_id=subscriber.pk,
                                                                   community_id=community.pk)
        except cls.DoesNotExist:
            community_notifications_subscription = cls.create_community_notifications_subscription(
                subscriber=subscriber,
                community=community
            )

        return community_notifications_subscription

    @classmethod
    def delete_community_notifications_subscription(cls, subscriber, community):
        return cls.objects.filter(subscriber=subscriber, community=community).delete()

    @classmethod
    def community_notifications_subscription_exists(cls, subscriber, community):
        return cls.objects.filter(subscriber=subscriber, community=community).exists()

    @classmethod
    def are_new_post_notifications_enabled_for_user_with_username_and_community_with_name(cls, username,
                                                                                          community_name):
        return cls.objects.filter(community__name=community_name,
                                  subscriber__username=username,
                                  new_post_notifications=True).exists()
