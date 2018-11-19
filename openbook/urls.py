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

from openbook_circles.views import Circles, CircleItem
from openbook_common.views import Time, Health
from openbook_auth.views import Register, UsernameCheck, EmailCheck, Login, User
from openbook_connections.views import ConnectWithUser, Connections, DisconnectFromUser, UpdateConnection, \
    ConfirmConnection
from openbook_follows.views import Follows, FollowUser, UnfollowUser, UpdateFollowUser
from openbook_lists.views import Lists, ListItem
from openbook_posts.views.post.views import PostComments, PostCommentItem, PostItem, PostReactions, PostReactionItem
from openbook_posts.views.posts.views import Posts

auth_patterns = [
    path('register/', Register.as_view(), name='register-user'),
    path('login/', Login.as_view(), name='login-user'),
    path('username-check/', UsernameCheck.as_view(), name='username-check'),
    path('email-check/', EmailCheck.as_view(), name='email-check'),
    path('user/', User.as_view(), name='user'),
]

post_patterns = [
    path('', PostItem.as_view(), name='post'),
    path('comments/', PostComments.as_view(), name='post-comments'),
    path('comments/<int:post_comment_id>/', PostCommentItem.as_view(), name='post-comment'),
    path('reactions/', PostReactions.as_view(), name='post-reactions'),
    path('reactions/<int:post_reaction_id>/', PostReactionItem.as_view(), name='post-reaction'),
]

posts_patterns = [
    path('<int:post_id>/', include(post_patterns)),
    path('', Posts.as_view(), name='posts'),
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
    path('<int:circle_id>/', CircleItem.as_view(), name='circle'),
]

lists_patterns = [
    path('', Lists.as_view(), name='lists'),
    path('<int:list_id>/', ListItem.as_view(), name='list'),
]

follows_patterns = [
    path('', Follows.as_view(), name='follows'),
    path('follow/', FollowUser.as_view(), name='follow-user'),
    path('unfollow/', UnfollowUser.as_view(), name='unfollow-user'),
    path('update/', UpdateFollowUser.as_view(), name='update-follow'),
]

api_patterns = [
    path('auth/', include(auth_patterns)),
    path('posts/', include(posts_patterns)),
    path('circles/', include(circles_patterns)),
    path('connections/', include(connections_patterns)),
    path('lists/', include(lists_patterns)),
    path('follows/', include(follows_patterns)),
    url('time/', Time.as_view(), name='time'),
]

urlpatterns = [
    path('api/', include(api_patterns)),
    url('admin/', admin.site.urls),
    url('health/', Health.as_view(), name='health'),
]

# The static helper works only in debug mode
# https://docs.djangoproject.com/en/2.1/howto/static-files/#serving-files-uploaded-by-a-user-during-development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
