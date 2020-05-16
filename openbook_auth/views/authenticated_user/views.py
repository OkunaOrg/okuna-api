from django.db import transaction
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from openbook_auth.views.auth.serializers import AuthenticatedUserNotificationsSettingsSerializer, \
    UpdateAuthenticatedUserNotificationsSettingsSerializer
from openbook_auth.views.authenticated_user.serializers import GetAuthenticatedUserSerializer, \
    UpdateAuthenticatedUserSerializer, DeleteAuthenticatedUserSerializer, UpdateAuthenticatedUserSettingsSerializer, \
    AuthenticatedUserLanguageSerializer, AuthenticatedUserAllLanguagesSerializer
from openbook_common.utils.model_loaders import get_language_model
from openbook_moderation.permissions import IsNotSuspended, check_user_is_not_suspended
from openbook_common.responses import ApiMessageResponse


class AuthenticatedUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user_serializer = GetAuthenticatedUserSerializer(request.user, context={"request": request})
        return Response(user_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        check_user_is_not_suspended(user=request.user)
        serializer = UpdateAuthenticatedUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user

        with transaction.atomic():
            user.update(
                username=data.get('username'),
                name=data.get('name'),
                location=data.get('location'),
                bio=data.get('bio'),
                url=data.get('url'),
                followers_count_visible=data.get('followers_count_visible'),
                community_posts_visible=data.get('community_posts_visible'),
                visibility=data.get('visibility'),
                save=False
            )

            has_avatar = 'avatar' in data
            if has_avatar:
                avatar = data.get('avatar')
                if avatar is None:
                    user.delete_profile_avatar(save=False)
                else:
                    user.update_profile_avatar(avatar, save=False)

            has_cover = 'cover' in data
            if has_cover:
                cover = data.get('cover')
                if cover is None:
                    user.delete_profile_cover(save=False)
                else:
                    user.update_profile_cover(cover, save=False)

            user.profile.save()
            user.save()

        user_serializer = GetAuthenticatedUserSerializer(user, context={"request": request})
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class DeleteAuthenticatedUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DeleteAuthenticatedUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user

        password = data.get('password')

        with transaction.atomic():
            user.delete_with_password(password=password)

        return Response(_('Goodbye 😔'), status=status.HTTP_200_OK)


class AuthenticatedUserNotificationsSettings(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user_notifications_settings_serializer = AuthenticatedUserNotificationsSettingsSerializer(
            request.user.notifications_settings, context={'request': request})
        return Response(user_notifications_settings_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UpdateAuthenticatedUserNotificationsSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        post_comment_notifications = data.get('post_comment_notifications')
        post_reaction_notifications = data.get('post_reaction_notifications')
        follow_notifications = data.get('follow_notifications')
        follow_request_notifications = data.get('follow_request_notifications')
        follow_request_approved_notifications = data.get('follow_request_approved_notifications')
        connection_request_notifications = data.get('connection_request_notifications')
        connection_confirmed_notifications = data.get('connection_confirmed_notifications')
        community_invite_notifications = data.get('community_invite_notifications')
        community_new_post_notifications = data.get('community_new_post_notifications')
        user_new_post_notifications = data.get('user_new_post_notifications')
        post_comment_reaction_notifications = data.get('post_comment_reaction_notifications')
        post_comment_reply_notifications = data.get('post_comment_reply_notifications')
        post_comment_user_mention_notifications = data.get('post_comment_user_mention_notifications')
        post_user_mention_notifications = data.get('post_user_mention_notifications')

        user = request.user

        with transaction.atomic():
            notifications_settings = user.update_notifications_settings(
                post_comment_notifications=post_comment_notifications,
                post_reaction_notifications=post_reaction_notifications,
                follow_notifications=follow_notifications,
                follow_request_notifications=follow_request_notifications,
                follow_request_approved_notifications=follow_request_approved_notifications,
                connection_request_notifications=connection_request_notifications,
                connection_confirmed_notifications=connection_confirmed_notifications,
                community_invite_notifications=community_invite_notifications,
                community_new_post_notifications=community_new_post_notifications,
                user_new_post_notifications=user_new_post_notifications,
                post_comment_reaction_notifications=post_comment_reaction_notifications,
                post_comment_reply_notifications=post_comment_reply_notifications,
                post_comment_user_mention_notifications=post_comment_user_mention_notifications,
                post_user_mention_notifications=post_user_mention_notifications
            )

        user_notifications_settings_serializer = AuthenticatedUserNotificationsSettingsSerializer(
            notifications_settings, context={'request': request})
        return Response(user_notifications_settings_serializer.data, status=status.HTTP_200_OK)


class AuthenticatedUserSettings(APIView):
    # TODO Split into update password and update email APIs...
    permission_classes = (IsAuthenticated,)

    def patch(self, request):
        serializer = UpdateAuthenticatedUserSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user

        with transaction.atomic():
            has_password = 'new_password' in data
            if has_password:
                current_password = data.get('current_password')
                new_password = data.get('new_password')
                if user.check_password(current_password):
                    user.update_password(password=new_password)
                else:
                    raise AuthenticationFailed(detail='Password is not valid')
            has_email = 'email' in data
            if has_email:
                new_email = data.get('email')
                confirm_email_token = user.request_email_update(new_email)
                self.send_confirmation_email(user, new_email, confirm_email_token)

            if not has_email and not has_password:
                return Response(_('Please specify email or password to update'), status=status.HTTP_400_BAD_REQUEST)

        user_serializer = GetAuthenticatedUserSerializer(user, context={"request": request})
        return Response(user_serializer.data, status=status.HTTP_200_OK)

    def send_confirmation_email(self, user, new_email, confirm_email_token):
        mail_subject = _('Confirm your email for Openbook')
        text_content = render_to_string('openbook_auth/email/change_email.txt', {
            'name': user.profile.name,
            'confirmation_link': self.generate_confirmation_link(confirm_email_token)
        })

        html_content = render_to_string('openbook_auth/email/change_email.html', {
            'name': user.profile.name,
            'confirmation_link': self.generate_confirmation_link(confirm_email_token)
        })

        email = EmailMultiAlternatives(
            mail_subject, text_content, to=[new_email], from_email=settings.SERVICE_EMAIL_ADDRESS)
        email.attach_alternative(html_content, 'text/html')
        email.send()

    def generate_confirmation_link(self, token):
        return '{0}/api/auth/email/verify/{1}'.format(settings.EMAIL_HOST, token)


class AuthenticatedUserAcceptGuidelines(APIView):
    """
    The API to accept the guidelines
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user

        with transaction.atomic():
            user.accept_guidelines()

        return ApiMessageResponse(_('Guidelines successfully accepted'), status=status.HTTP_200_OK)


class AuthenticatedUserLanguage(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        Language = get_language_model()
        languages = Language.objects.all()
        all_languages_serializer = AuthenticatedUserAllLanguagesSerializer(
            languages, context={'request': request}, many=True)
        return Response(all_languages_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        request_data = request.data
        serializer = AuthenticatedUserLanguageSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = request.user

        with transaction.atomic():
            user.set_language_with_id(language_id=data.get('language_id'))

        return ApiMessageResponse(_('Language successfully set'), status=status.HTTP_200_OK)
