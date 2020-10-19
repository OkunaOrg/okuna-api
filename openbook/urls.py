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
from proxy.views import proxy_view

from openbook_auth.views.auth.views import Register, Login, UsernameCheck, EmailCheck, EmailVerify, \
    PasswordResetRequest, PasswordResetVerify, VerifyRegistrationToken
from openbook_auth.views.authenticated_user.views import AuthenticatedUser, AuthenticatedUserSettings, \
    DeleteAuthenticatedUser, AuthenticatedUserNotificationsSettings, AuthenticatedUserAcceptGuidelines, \
    AuthenticatedUserLanguage
from openbook_auth.views.blocked_users.views import BlockedUsers, SearchBlockedUsers
from openbook_auth.views.followers.views import Followers, SearchFollowers
from openbook_auth.views.following.views import Followings, SearchFollowings
from openbook_auth.views.linked_users.views import LinkedUsers, SearchLinkedUsers
from openbook_auth.views.proxy.views import ProxyAuth
from openbook_auth.views.users.views import SearchUsers, GetUser, BlockUser, UnblockUser, \
    SubscribeToUserNewPostNotifications, GetUserPostsCount
from openbook_categories.views import Categories
from openbook_circles.views import Circles, CircleItem, CircleNameCheck
from openbook_common.views import Time, Health, EmojiGroups, ProxyDomainCheck
from openbook_communities.views.communities.views import Communities, TrendingCommunities, CommunityNameCheck, \
    FavoriteCommunities, SearchCommunities, JoinedCommunities, AdministratedCommunities, ModeratedCommunities, \
    SearchJoinedCommunities, SuggestedCommunities, \
    SearchAdministratedCommunities, SearchModeratedCommunities, SearchFavoriteCommunities
from openbook_communities.views.community.administrators.views import CommunityAdministratorItem, \
    CommunityAdministrators, SearchCommunityAdministrators
from openbook_communities.views.community.banned_users.views import BanUser, UnbanUser, CommunityBannedUsers, \
    SearchCommunityBannedUsers
from openbook_communities.views.community.members.views import CommunityMembers, JoinCommunity, \
    LeaveCommunity, InviteCommunityMember, SearchCommunityMembers, UninviteCommunityMember
from openbook_communities.views.community.moderators.views import CommunityModeratorItem, CommunityModerators, \
    SearchCommunityModerators
from openbook_communities.views.community.posts.views import CommunityPosts, ClosedCommunityPosts, \
    GetCommunityPostsCount
from openbook_communities.views.community.views import CommunityItem, CommunityAvatar, CommunityCover, \
    FavoriteCommunity, \
    SubscribeToCommunityNewPostNotifications, LegacyExcludeTopPostsCommunity
from openbook_connections.views import ConnectWithUser, Connections, DisconnectFromUser, UpdateConnection, \
    ConfirmConnection
from openbook_hashtags.views.hashtag.views import HashtagItem, HashtagPosts
from openbook_hashtags.views.hashtags.views import SearchHashtags
from openbook_invitations.views import UserInvite, UserInvites, SearchUserInvites, SendUserInviteEmail
from openbook_devices.views import Devices, DeviceItem
from openbook_follows.views import FollowUser, UnfollowUser, UpdateFollowUser, RequestToFollowUser, \
    ApproveUserFollowRequest, RejectUserFollowRequest, ReceivedFollowRequests, CancelRequestToFollowUser
from openbook_lists.views import Lists, ListItem, ListNameCheck
from openbook_moderation.views.checks import IsNotSuspendedCheck
from openbook_moderation.views.moderated_object.views import ModeratedObjectItem, ModeratedObjectLogs, \
    ApproveModeratedObject, RejectModeratedObject, VerifyModeratedObject, UnverifyModeratedObject, \
    ModeratedObjectReports
from openbook_moderation.views.moderated_objects.views import CommunityModeratedObjects, GlobalModeratedObjects
from openbook_moderation.views.moderation_categories.views import ModerationCategories
from openbook_moderation.views.report.views import ReportUser, ReportPost, ReportCommunity, \
    ReportPostComment, ReportHashtag
from openbook_moderation.views.user.views import UserModerationPenalties, UserPendingModeratedObjectsCommunities
from openbook_notifications.views import Notifications, NotificationItem, ReadNotifications, ReadNotification, \
    UnreadNotificationsCount
from openbook_posts.views.post.views import PostItem, PostOpen, PostClose, MutePost, UnmutePost, TranslatePost, \
    PostPreviewLinkData, SearchPostParticipants, GetPostParticipants, PublishPost, PostStatus
from openbook_posts.views.post_comment.post_comment_reaction.views import PostCommentReactionItem
from openbook_posts.views.post_comment.post_comment_reactions.views import PostCommentReactions, \
    PostCommentReactionsEmojiCount
from openbook_posts.views.post_comment.post_comment_replies.views import PostCommentReplies
from openbook_posts.views.post_comment.views import PostCommentItem, MutePostComment, UnmutePostComment, \
    TranslatePostComment
from openbook_posts.views.post_comments.views import PostComments, PostCommentsDisable, PostCommentsEnable
from openbook_posts.views.post_media.views import PostMedia
from openbook_posts.views.post_reaction.views import PostReactionItem
from openbook_posts.views.post_reactions.views import PostReactions, PostReactionsEmojiCount, PostReactionEmojiGroups
from openbook_posts.views.posts.views import Posts, TrendingPosts, TopPosts, TrendingPostsNew, \
    ProfilePostsExcludedCommunities, SearchProfilePostsExcludedCommunities, TopPostsExcludedCommunities, \
    SearchTopPostsExcludedCommunities, ProfilePostsExcludedCommunity, TopPostsExcludedCommunity, PreviewLink, \
    LinkIsPreviewable
from openbook_importer.views import ImportItem

auth_auth_patterns = [
    path('register/', Register.as_view(), name='register-user'),
    path('register/verify-token/', VerifyRegistrationToken.as_view(), name='verify-register-token'),
    path('login/', Login.as_view(), name='login-user'),
    path('username-check/', UsernameCheck.as_view(), name='username-check'),
    path('email-check/', EmailCheck.as_view(), name='email-check'),
    path('email/verify/', EmailVerify.as_view(), name='email-verify'),
    path('password/reset/', PasswordResetRequest.as_view(), name='request-password-reset'),
    path('password/verify/', PasswordResetVerify.as_view(), name='verify-reset-password'),
]

auth_user_patterns = [
    path('', AuthenticatedUser.as_view(), name='authenticated-user'),
    path('settings/', AuthenticatedUserSettings.as_view(), name='authenticated-user-settings'),
    path('delete/', DeleteAuthenticatedUser.as_view(), name='delete-authenticated-user'),
    path('notifications-settings/', AuthenticatedUserNotificationsSettings.as_view(),
         name='authenticated-user-notifications-settings'),
    path('accept-guidelines/', AuthenticatedUserAcceptGuidelines.as_view(),
         name='authenticated-user-accept-guidelines'),
    path('languages/', AuthenticatedUserLanguage.as_view(), name='user-language'),
]

auth_users_user_patterns = [
    path('', GetUser.as_view(), name='get-user'),
    path('block/', BlockUser.as_view(), name='block-user'),
    path('unblock/', UnblockUser.as_view(), name='unblock-user'),
    path('report/', ReportUser.as_view(), name='report-user'),
    path('notifications/subscribe/new-post/', SubscribeToUserNewPostNotifications.as_view(),
         name='subscribe-user-new-post-notifications'),
    path('posts/count/', GetUserPostsCount.as_view(), name='user-posts-count'),
]

auth_users_patterns = [
    path('', SearchUsers.as_view(), name='search-users'),
    path('<str:user_username>/', include(auth_users_user_patterns)),
]

auth_blocked_users_patterns = [
    path('', BlockedUsers.as_view(), name='blocked-users'),
    path('search/', SearchBlockedUsers.as_view(), name='search-blocked-users'),
]

auth_linked_users_patterns = [
    path('', LinkedUsers.as_view(), name='linked-users'),
    path('search/', SearchLinkedUsers.as_view(), name='search-linked-users'),
]

auth_followers_patterns = [
    path('', Followers.as_view(), name='followers'),
    path('search/', SearchFollowers.as_view(), name='search-followers'),
]

auth_followings_patterns = [
    path('', Followings.as_view(), name='followings'),
    path('search/', SearchFollowings.as_view(), name='search-followings'),
]

auth_patterns = [
    path('', include(auth_auth_patterns)),
    path('followings/', include(auth_followings_patterns)),
    path('followers/', include(auth_followers_patterns)),
    path('linked-users/', include(auth_linked_users_patterns)),
    path('blocked-users/', include(auth_blocked_users_patterns)),
    path('users/', include(auth_users_patterns)),
    path('user/', include(auth_user_patterns)),
    path('proxy/', ProxyAuth.as_view(), name='proxy-auth'),
]

post_notifications_patterns = [
    path('mute/', MutePost.as_view(), name='mute-post'),
    path('unmute/', UnmutePost.as_view(), name='unmute-post'),
]

post_comment_reactions_patterns = [
    path('', PostCommentReactions.as_view(), name='post-comment-reactions'),
    path('emoji-count/', PostCommentReactionsEmojiCount.as_view(), name='post-comment-reactions-emoji-count'),
    path('<int:post_comment_reaction_id>/', PostCommentReactionItem.as_view(), name='post-comment-reaction'), ]

post_comment_notifications_patterns = [
    path('mute/', MutePostComment.as_view(), name='mute-post-comment'),
    path('unmute/', UnmutePostComment.as_view(), name='unmute-post-comment'),
]

post_comment_patterns = [
    path('', PostCommentItem.as_view(), name='post-comment'),
    path('translate/', TranslatePostComment.as_view(), name='translate-post-comment'),
    path('report/', ReportPostComment.as_view(), name='report-post-comment'),
    path('replies/', PostCommentReplies.as_view(), name='post-comment-replies'),
    path('reactions/', include(post_comment_reactions_patterns), name='post-comment-replies'),
    path('notifications/', include(post_comment_notifications_patterns)),
]

post_participants_patterns = [
    path('', GetPostParticipants.as_view(), name='get-post-participants'),
    path('search/', SearchPostParticipants.as_view(), name='search-post-participants'),
]

post_media_patterns = [
    path('', PostMedia.as_view(), name='post-media'),
]
post_patterns = [
    path('', PostItem.as_view(), name='post'),
    path('notifications/', include(post_notifications_patterns)),
    path('comments/', PostComments.as_view(), name='post-comments'),
    path('comments/disable/', PostCommentsDisable.as_view(), name='disable-post-comments'),
    path('comments/enable/', PostCommentsEnable.as_view(), name='enable-post-comments'),
    path('comments/<int:post_comment_id>/', include(post_comment_patterns)),
    path('reactions/', PostReactions.as_view(), name='post-reactions'),
    path('reactions/emoji-count/', PostReactionsEmojiCount.as_view(), name='post-reactions-emoji-count'),
    path('reactions/<int:post_reaction_id>/', PostReactionItem.as_view(), name='post-reaction'),
    path('close/', PostClose.as_view(), name='close-post'),
    path('open/', PostOpen.as_view(), name='open-post'),
    path('report/', ReportPost.as_view(), name='report-post'),
    path('translate/', TranslatePost.as_view(), name='translate-post'),
    path('publish/', PublishPost.as_view(), name='publish-post'),
    path('status/', PostStatus.as_view(), name='post-status'),
    path('link-preview/', PostPreviewLinkData.as_view(), name='preview-post-link'),
    path('participants/', include(post_participants_patterns)),
    path('media/', include(post_media_patterns)),
]

posts_profile_patterns = [
    path('excluded-communities/', ProfilePostsExcludedCommunities.as_view(),
         name='profile-posts-excluded-communities'),
    path('excluded-communities/search/', SearchProfilePostsExcludedCommunities.as_view(),
         name='search-profile-posts-excluded-communities'),
    path('excluded-communities/<str:community_name>/', ProfilePostsExcludedCommunity.as_view(),
         name='profile-posts-excluded-community'),
]

posts_top_patterns = [
    path('', TopPosts.as_view(), name='top-posts'),
    path('excluded-communities/', TopPostsExcludedCommunities.as_view(),
         name='top-posts-excluded-communities'),
    path('excluded-communities/search/', SearchTopPostsExcludedCommunities.as_view(),
         name='search-top-posts-excluded-communities'),
    path('excluded-communities/<str:community_name>/', TopPostsExcludedCommunity.as_view(),
         name='top-posts-excluded-community'),
]

posts_links_patterns = [
    path('preview/', PreviewLink.as_view(), name='preview-post-link'),
    path('is-previewable/', LinkIsPreviewable.as_view(), name='post-link-is-previewable'),
]

posts_patterns = [
    path('<uuid:post_uuid>/', include(post_patterns)),
    path('', Posts.as_view(), name='posts'),
    path('trending/', TrendingPosts.as_view(), name='trending-posts'),
    path('trending/new/', TrendingPostsNew.as_view(), name='trending-posts-new'),
    path('emojis/groups/', PostReactionEmojiGroups.as_view(), name='posts-emoji-groups'),
    path('profile/', include(posts_profile_patterns)),
    path('top/', include(posts_top_patterns)),
    path('links/', include(posts_links_patterns)),
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
    path('closed/', ClosedCommunityPosts.as_view(), name='closed-community-posts'),
    path('count/', GetCommunityPostsCount.as_view(), name='community-posts-count'),
]

community_banned_users_patterns = [
    path('', CommunityBannedUsers.as_view(), name='community-banned-users'),
    path('search/', SearchCommunityBannedUsers.as_view(), name='search-community-banned-users'),
    path('ban/', BanUser.as_view(), name='community-ban-user'),
    path('unban/', UnbanUser.as_view(), name='community-unban-user'),
]

community_moderated_objects_patterns = [
    path('', CommunityModeratedObjects.as_view(), name='community-moderated-objects')
]

community_patterns = [
    path('', CommunityItem.as_view(), name='community'),
    path('avatar/', CommunityAvatar.as_view(), name='community-avatar'),
    path('cover/', CommunityCover.as_view(), name='community-cover'),
    path('favorite/', FavoriteCommunity.as_view(), name='favorite-community'),
    path('notifications/subscribe/new-post/', SubscribeToCommunityNewPostNotifications.as_view(),
         name='subscribe-community-new-post-notifications'),
    path('members/', include(community_members_patterns)),
    path('posts/', include(community_posts_patterns)),
    path('banned-users/', include(community_banned_users_patterns)),
    path('administrators/', include(community_administrators_patterns)),
    path('moderators/', include(community_moderators_patterns)),
    path('moderated-objects/', include(community_moderated_objects_patterns)),
    path('report/', ReportCommunity.as_view(), name='report-community'),
    # LEGACY. Remove after 0.0.63
    path('top-posts/exclude/', LegacyExcludeTopPostsCommunity.as_view(),
         name='legacy-exclude-community-from-top-posts'),
]

communities_patterns = [
    path('', Communities.as_view(), name='communities'),
    path('suggested/', SuggestedCommunities.as_view(), name='suggested-communities'),
    path('trending/', TrendingCommunities.as_view(), name='trending-communities'),
    path('joined/', JoinedCommunities.as_view(), name='joined-communities'),
    path('joined/search/', SearchJoinedCommunities.as_view(), name='search-joined-communities'),
    path('favorites/', FavoriteCommunities.as_view(), name='favorite-communities'),
    path('favorites/search/', SearchFavoriteCommunities.as_view(), name='search-favorite-communities'),
    path('administrated/', AdministratedCommunities.as_view(), name='administrated-communities'),
    path('administrated/search/', SearchAdministratedCommunities.as_view(), name='search-administrated-communities'),
    path('moderated/', ModeratedCommunities.as_view(), name='moderated-communities'),
    path('moderated/search/', SearchModeratedCommunities.as_view(), name='search-moderated-communities'),
    path('name-check/', CommunityNameCheck.as_view(), name='community-name-check'),
    # LEGACY. Remove after 0.0.63
    path('top-posts/exclusions/', TopPostsExcludedCommunities.as_view(), name='legacy-top-posts-excluded-communities'),
    path('top-posts/exclusions/search/', SearchTopPostsExcludedCommunities.as_view(),
         name='legacy-search-top-posts-excluded-communities'),
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

follow_requests_patterns = [
    path('', RequestToFollowUser.as_view(), name='request-to-follow-user'),
    path('approve/', ApproveUserFollowRequest.as_view(), name='approve-user-follow-request'),
    path('reject/', RejectUserFollowRequest.as_view(), name='reject-user-follow-request'),
    path('cancel/', CancelRequestToFollowUser.as_view(), name='cancel-request-to-follow-user'),
    path('received/', ReceivedFollowRequests.as_view(), name='received-follow-requests'),
]

follows_patterns = [
    path('requests/', include(follow_requests_patterns)),
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
    path('read/', ReadNotifications.as_view(), name='read-notifications'),
    path('unread/count/', UnreadNotificationsCount.as_view(), name='unread-notifications-count'),
    path('<int:notification_id>/', include(notification_patterns)),
]

devices_patterns = [
    path('', Devices.as_view(), name='devices'),
    path('<str:device_uuid>/', DeviceItem.as_view(), name='device'),
]

invites_patterns = [
    path('', UserInvites.as_view(), name='invites'),
    path('search/', SearchUserInvites.as_view(), name='search-invites'),
    path('<str:invite_id>/', UserInvite.as_view(), name='invite'),
    path('<str:invite_id>/email/', SendUserInviteEmail.as_view(), name='send-invite-email'),
]

moderation_moderated_object_patterns = [
    path('', ModeratedObjectItem.as_view(), name='moderated-object'),
    path('approve/', ApproveModeratedObject.as_view(), name='approve-moderated-object'),
    path('reject/', RejectModeratedObject.as_view(), name='reject-moderated-object'),
    path('verify/', VerifyModeratedObject.as_view(), name='verify-moderated-object'),
    path('unverify/', UnverifyModeratedObject.as_view(), name='unverify-moderated-object'),
    path('logs/', ModeratedObjectLogs.as_view(), name='moderated-object-logs'),
    path('reports/', ModeratedObjectReports.as_view(), name='moderated-object-reports'),
]

moderation_moderated_objects_patterns = [
    path('<int:moderated_object_id>/', include(moderation_moderated_object_patterns)),
    path('global/', GlobalModeratedObjects.as_view(), name='global-moderated-objects')
]

moderation_patterns = [
    path('moderated-objects/', include(moderation_moderated_objects_patterns), name='moderation-moderated-objects'),
    path('categories/', ModerationCategories.as_view(), name='moderation-categories'),
    path('is-not-suspended-check/', IsNotSuspendedCheck.as_view(), name='is-not-suspended-check'),
    path('user/penalties/', UserModerationPenalties.as_view(), name='user-moderation-penalties'),
    path('user/pending-moderated-objects-communities/', UserPendingModeratedObjectsCommunities.as_view(),
         name='user-pending-moderated-objects-communities'),
]

hashtag_patterns = [
    path('', HashtagItem.as_view(), name='hashtag'),
    path('posts/', HashtagPosts.as_view(), name='hashtag-posts'),
    path('report/', ReportHashtag.as_view(), name='report-hashtag'),
]

hashtags_patterns = [
    path('search/', SearchHashtags.as_view(), name='search-hashtags'),
    path('<str:hashtag_name>/', include(hashtag_patterns)),
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
    path('invites/', include(invites_patterns)),
    path('moderation/', include(moderation_patterns)),
    path('hashtags/', include(hashtags_patterns)),
    url('time/', Time.as_view(), name='time'),
    url('emojis/groups/', EmojiGroups.as_view(), name='emoji-groups'),
    url('proxy-domain-check/', ProxyDomainCheck.as_view(),
        name='proxy-domain-check'),
]

if settings.FEATURE_IMPORTER_ENABLED:
    api_patterns.append(path('import/', include(importer_patterns))),

urlpatterns = [
    path('api/', include(api_patterns)),
    url('admin/', admin.site.urls),
    path('django-rq/', include('django_rq.urls')),
    url('health/', Health.as_view(), name='health'),
]

# The static helper works only in debug mode
# https://docs.djangoproject.com/en/2.1/howto/static-files/#serving-files-uploaded-by-a-user-during-development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Link previews proxy their urls, use local proxy API on debug/test
if settings.DEBUG or settings.TESTING:
    urlpatterns.append(url('proxy/(?P<url>.*)', proxy_view, name='proxy'), )
