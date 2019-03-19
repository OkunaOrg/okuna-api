"""openbook URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from openbook_categories.views import Categories
from openbook_circles.views import Circles, CircleItem, CircleNameCheck
from openbook_common.views import Time, Health, EmojiGroups
from openbook_auth.views import Register, UsernameCheck, EmailCheck, EmailVerify, Login, AuthenticatedUser, Users, \
    UserSettings, LinkedUsers, SearchLinkedUsers, UserItem, AuthenticatedUserNotificationsSettings, \
    AuthenticatedUserDelete, UpdateUsernameCheck, AuthenticatedUserDelete, PasswordResetRequest, PasswordResetVerify
from openbook_communities.views.communities.views import Communities, TrendingCommunities, CommunityNameCheck, \
    FavoriteCommunities, SearchCommunities, JoinedCommunities, AdministratedCommunities, ModeratedCommunities, \
    SearchJoinedCommunities
from openbook_communities.views.community.administrators.views import CommunityAdministratorItem, \
    CommunityAdministrators, SearchCommunityAdministrators
from openbook_communities.views.community.banned_users.views import BanUser, UnbanUser, CommunityBannedUsers, \
    SearchCommunityBannedUsers
from openbook_communities.views.community.members.views import CommunityMembers, JoinCommunity, \
    LeaveCommunity, InviteCommunityMember, SearchCommunityMembers, UninviteCommunityMember
from openbook_communities.views.community.moderators.views import CommunityModeratorItem, CommunityModerators, \
    SearchCommunityModerators
from openbook_communities.views.community.posts.views import CommunityPosts
from openbook_communities.views.community.views import CommunityItem, CommunityAvatar, CommunityCover, FavoriteCommunity
from openbook_connections.views import ConnectWithUser, Connections, DisconnectFromUser, UpdateConnection, \
    ConfirmConnection
from openbook_devices.views import Devices, DeviceItem
from openbook_follows.views import Follows, FollowUser, UnfollowUser, UpdateFollowUser
from openbook_lists.views import Lists, ListItem, ListNameCheck
from openbook_notifications.views import Notifications, NotificationItem, ReadAllNotifications, ReadNotification
from openbook_posts.views.post.views import PostComments, PostCommentItem, PostItem, PostReactions, PostReactionItem, \
    PostReactionsEmojiCount, PostReactionEmojiGroups, MutePost, UnmutePost
from openbook_posts.views.posts.views import Posts, TrendingPosts
from openbook_importer.views import ImportItem

auth_patterns = [
    path('register/', Register.as_view(), name='register-user'),
    path('login/', Login.as_view(), name='login-user'),
    path('username-check/', UsernameCheck.as_view(), name='username-check'),
    path('update-username-check/', UpdateUsernameCheck.as_view(), name='update-username-check'),
    path('email-check/', EmailCheck.as_view(), name='email-check'),
    path('email/verify/<str:token>/', EmailVerify.as_view(), name='email-verify'),
    path('password/reset/', PasswordResetRequest.as_view(), name='request-password-reset'),
    path('password/verify/', PasswordResetVerify.as_view(), name='verify-reset-password'),
    path('user/settings/', UserSettings.as_view(), name='user-settings'),
    path('user/', AuthenticatedUser.as_view(), name='authenticated-user'),
    path('user/delete/', AuthenticatedUserDelete.as_view(), name='authenticated-user-delete'),
    path('user/notifications-settings/', AuthenticatedUserNotificationsSettings.as_view(),
         name='authenticated-user-notifications-settings'),
    path('users/<str:user_username>/', UserItem.as_view(), name='user'),
    path('users/', Users.as_view(), name='users'),
    path('linked-users/', LinkedUsers.as_view(), name='linked-users'),
    path('linked-users/search/', SearchLinkedUsers.as_view(), name='search-linked-users'),
]

post_notifications_patters = [
    path('mute/', MutePost.as_view(), name='mute-post'),
    path('unmute/', UnmutePost.as_view(), name='unmute-post'),
]

post_patterns = [
    path('', PostItem.as_view(), name='post'),
    path('notifications/', include(post_notifications_patters)),
    path('comments/', PostComments.as_view(), name='post-comments'),
    path('comments/<int:post_comment_id>/', PostCommentItem.as_view(), name='post-comment'),
    path('reactions/', PostReactions.as_view(), name='post-reactions'),
    path('reactions/emoji-count/', PostReactionsEmojiCount.as_view(), name='post-reactions-emoji-count'),
    path('reactions/<int:post_reaction_id>/', PostReactionItem.as_view(), name='post-reaction'),
]

posts_patterns = [
    path('<uuid:post_uuid>/', include(post_patterns)),
    path('', Posts.as_view(), name='posts'),
    path('trending/', TrendingPosts.as_view(), name='trending-posts'),
    path('emojis/groups/', PostReactionEmojiGroups.as_view(), name='posts-emoji-groups'),
]

community_administrator_patterns = [
    path('', CommunityAdministratorItem.as_view(), name='community-administrator'),
]

community_administrators_patterns = [
    path('', CommunityAdministrators.as_view(), name='community-administrators'),
    path('search/', SearchCommunityAdministrators.as_view(), name='search-community-administrators'),
    path('<str:community_administrator_username>/', include(community_administrator_patterns)),
]

community_moderator_patterns = [
    path('', CommunityModeratorItem.as_view(), name='community-moderator'),
]

community_moderators_patterns = [
    path('', CommunityModerators.as_view(), name='community-moderators'),
    path('search/', SearchCommunityModerators.as_view(), name='search-community-moderators'),
    path('<str:community_moderator_username>/', include(community_moderator_patterns)),
]

community_members_patterns = [
    path('', CommunityMembers.as_view(), name='community-members'),
    path('search/', SearchCommunityMembers.as_view(), name='search-community-members'),
    path('join/', JoinCommunity.as_view(), name='community-join'),
    path('leave/', LeaveCommunity.as_view(), name='community-leave'),
    path('invite/', InviteCommunityMember.as_view(), name='community-invite'),
    path('uninvite/', UninviteCommunityMember.as_view(), name='community-uninvite'),
]

community_posts_patterns = [
    path('', CommunityPosts.as_view(), name='community-posts'),
]

community_banned_users_patterns = [
    path('', CommunityBannedUsers.as_view(), name='community-banned-users'),
    path('search/', SearchCommunityBannedUsers.as_view(), name='search-community-banned-users'),
    path('ban/', BanUser.as_view(), name='community-ban-user'),
    path('unban/', UnbanUser.as_view(), name='community-unban-user'),
]

community_patterns = [
    path('', CommunityItem.as_view(), name='community'),
    path('avatar/', CommunityAvatar.as_view(), name='community-avatar'),
    path('cover/', CommunityCover.as_view(), name='community-cover'),
    path('favorite/', FavoriteCommunity.as_view(), name='favorite-community'),
    path('members/', include(community_members_patterns)),
    path('posts/', include(community_posts_patterns)),
    path('banned-users/', include(community_banned_users_patterns)),
    path('administrators/', include(community_administrators_patterns)),
    path('moderators/', include(community_moderators_patterns)),
]

communities_patterns = [
    path('', Communities.as_view(), name='communities'),
    path('trending/', TrendingCommunities.as_view(), name='trending-communities'),
    path('joined/', JoinedCommunities.as_view(), name='joined-communities'),
    path('joined/search/', SearchJoinedCommunities.as_view(), name='search-joined-communities'),
    path('favorites/', FavoriteCommunities.as_view(), name='favorite-communities'),
    path('administrated/', AdministratedCommunities.as_view(), name='administrated-communities'),
    path('moderated/', ModeratedCommunities.as_view(), name='moderated-communities'),
    path('name-check/', CommunityNameCheck.as_view(), name='community-name-check'),
    path('search/', SearchCommunities.as_view(), name='search-communities'),
    path('<str:community_name>/', include(community_patterns)),
]

connections_patterns = [
    path('', Connections.as_view(), name='connections'),
    path('connect/', ConnectWithUser.as_view(), name='connect-with-user'),
    path('confirm/', ConfirmConnection.as_view(), name='confirm-connection'),
    path('disconnect/', DisconnectFromUser.as_view(), name='disconnect-from-user'),
    path('update/', UpdateConnection.as_view(), name='update-connection'),
]

circles_patterns = [
    path('', Circles.as_view(), name='circles'),
    path('name-check/', CircleNameCheck.as_view(), name='circle-name-check'),
    path('<int:circle_id>/', CircleItem.as_view(), name='circle'),
]

lists_patterns = [
    path('', Lists.as_view(), name='lists'),
    path('name-check/', ListNameCheck.as_view(), name='list-name-check'),
    path('<int:list_id>/', ListItem.as_view(), name='list'),
]

follows_patterns = [
    path('', Follows.as_view(), name='follows'),
    path('follow/', FollowUser.as_view(), name='follow-user'),
    path('unfollow/', UnfollowUser.as_view(), name='unfollow-user'),
    path('update/', UpdateFollowUser.as_view(), name='update-follow'),
]

importer_patterns = [
    path('upload/', ImportItem.as_view(), name='uploads')
]

categories_patterns = [
    path('', Categories.as_view(), name='categories')
]

notification_patterns = [
    path('', NotificationItem.as_view(), name='notification'),
    path('read/', ReadNotification.as_view(), name='read-notification'),
]

notifications_patterns = [
    path('', Notifications.as_view(), name='notifications'),
    path('read/', ReadAllNotifications.as_view(), name='read-notifications'),
    path('<int:notification_id>/', include(notification_patterns)),
]

devices_patterns = [
    path('', Devices.as_view(), name='devices'),
    path('<str:device_uuid>/', DeviceItem.as_view(), name='device'),
]

api_patterns = [
    path('auth/', include(auth_patterns)),
    path('posts/', include(posts_patterns)),
    path('communities/', include(communities_patterns)),
    path('categories/', include(categories_patterns)),
    path('circles/', include(circles_patterns)),
    path('connections/', include(connections_patterns)),
    path('lists/', include(lists_patterns)),
    path('follows/', include(follows_patterns)),
    path('notifications/', include(notifications_patterns)),
    path('devices/', include(devices_patterns)),
    url('time/', Time.as_view(), name='time'),
    url('emojis/groups/', EmojiGroups.as_view(), name='emoji-groups'),
]

if settings.FEATURE_IMPORTER_ENABLED:
    api_patterns.append(path('import/', include(importer_patterns))),

urlpatterns = [
    path('api/', include(api_patterns)),
    url('admin/', admin.site.urls),
    url('health/', Health.as_view(), name='health'),
]

# The static helper works only in debug mode
# https://docs.djangoproject.com/en/2.1/howto/static-files/#serving-files-uploaded-by-a-user-during-development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
