# Create your tests here.
from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_emoji, make_reactions_emoji_group, \
    make_community
from openbook_notifications.models import PostReactionNotification, Notification
from openbook_posts.models import PostReaction

logger = logging.getLogger(__name__)
fake = Faker()


class PostReactionItemAPITests(OpenbookAPITestCase):
    """
    PostReactionItemAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_delete_foreign_reaction_in_own_post(self):
        """
          should be able to delete a foreign reaction in own post and return 200
        """
        user = make_user()

        reactor = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = reactor.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id, )
        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_can_delete_own_reaction_in_foreign_public_post(self):
        """
          should be able to delete own reaction in foreign public post and return 200
        """
        user = make_user()

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                   )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_cannot_delete_foreign_reaction_in_foreign_public_post(self):
        """
          should NOT be able to delete foreign reaction in foreign public post and return 400
        """
        user = make_user()

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_cannot_delete_reaction_in_closed_community_post_when_not_creator(self):
        """
          should NOT be able to delete reaction in closed community post if not creator
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        community_post = post_creator.create_community_post(community_name=community.name,
                                                            text=make_fake_post_comment_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(community_post.pk, emoji_id=post_reaction_emoji_id,
                                                   )
        # now close the post
        community_post.is_closed = True
        community_post.save()

        url = self._get_url(post_reaction=post_reaction, post=community_post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_can_delete_reaction_in_closed_community_post_if_creator(self):
        """
          should be able to delete reaction in closed community post if creator
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        community_post = post_creator.create_community_post(community_name=community.name,
                                                            text=make_fake_post_comment_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(community_post.pk, emoji_id=post_reaction_emoji_id,
                                                   )
        # now close the post
        community_post.is_closed = True
        community_post.save()

        url = self._get_url(post_reaction=post_reaction, post=community_post)

        headers = make_authentication_headers_for_user(post_creator)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_can_delete_own_reaction_in_connected_user_public_post(self):
        """
          should be able to delete own reaction in a connected user public post and return 200
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        post = user_to_connect.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                   )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_cannot_delete_foreign_reaction_in_connected_user_public_post(self):
        """
          should not be able to delete foreign reaction in a connected user public post and return 400
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        foreign_user = make_user()

        post = user_to_connect.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_can_delete_own_reaction_in_connected_user_encircled_post_part_of(self):
        """
           should be able to delete own reaction in a connected user encircled post it's part of and return 200
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                   )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_cannot_delete_foreign_reaction_in_connected_user_encircled_post_part_of(self):
        """
           should NOT be able to delete foreign reaction in a connected user encircled post it's part of and return 400
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_cannot_delete_foreign_reaction_in_connected_user_encircled_post_not_part_of(self):
        """
           should NOT be able to delete foreign reaction in a connected user encircled post NOT part of and return 400
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_can_delete_own_reaction_in_followed_user_public_post(self):
        """
           should be able to delete own reaction in a followed user public post and return 200
         """
        user = make_user()

        user_to_follow = make_user()

        user.follow_user_with_id(user_to_follow.pk)

        post = user_to_follow.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                   )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_cannot_delete_foreign_reaction_in_followed_user_public_post(self):
        """
           should not be able to delete foreign reaction in a followed user public post and return 400
         """
        user = make_user()

        user_to_follow = make_user()

        user.follow_user_with_id(user_to_follow.pk)

        foreign_user = make_user()

        post = user_to_follow.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_cannot_delete_foreign_reaction_in_folowed_user_encircled_post(self):
        """
             should not be able to delete foreign reaction in a followed user encircled post and return 400
        """
        user = make_user()

        user_to_follow = make_user()
        circle = make_circle(creator=user_to_follow)

        user.follow_user_with_id(user_to_follow.pk)

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_follow.pk)
        user_to_follow.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_follow.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           )

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_post_reaction_notification_is_deleted_when_deleting_reaction(self):
        """
        should delete the post reaction notification when a post reaction is deleted
        """
        user = make_user()

        reactor = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = reactor.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                         )

        post_reaction_notification = PostReactionNotification.objects.get(post_reaction=post_reaction,
                                                                          notification__owner=user)
        notification = Notification.objects.get(notification_type=Notification.POST_REACTION,
                                                object_id=post_reaction_notification.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        self.client.delete(url, **headers)

        self.assertFalse(PostReactionNotification.objects.filter(pk=post_reaction_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def _get_url(self, post, post_reaction):
        return reverse('post-reaction', kwargs={
            'post_uuid': post.uuid,
            'post_reaction_id': post_reaction.pk
        })
