# Create your tests here.
import json
from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

import logging
from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_emoji, make_emoji_group, make_reactions_emoji_group, \
    make_community
from openbook_notifications.models import PostReactionNotification
from openbook_posts.models import PostReaction

logger = logging.getLogger(__name__)
fake = Faker()


class PostReactionsAPITests(OpenbookAPITestCase):
    """
    PostReactionsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_react_to_own_post(self):
        """
         should be able to reaction in own post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                                    reactor_id=user.pk).count() == 1)

    def test_cannot_react_to_foreign_post(self):
        """
         should not be able to reaction in a foreign encircled post and return 400
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()
        circle = make_circle(creator=foreign_user)
        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                                    reactor_id=user.pk).count() == 0)

    def test_cannot_react_to_foreign_post_with_non_reaction_emoji(self):
        """
         should not be able to reaction in a post with a non reaction emoji group and return 400
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                                    reactor_id=user.pk).count() == 0)

    def test_can_react_to_connected_user_public_post(self):
        """
         should be able to reaction in the public post of a connected user post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)

        connected_user_post = user_to_connect.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=connected_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 1)

    def test_can_react_to_connected_user_encircled_post_part_of(self):
        """
          should be able to reaction in the encircled post of a connected user which the user is part of and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        connected_user_post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=connected_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 1)

    def test_cannot_react_to_connected_user_encircled_post_not_part_of(self):
        """
             should NOT be able to reaction in the encircled post of a connected user which the user is NOT part of and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        # Note there is no confirmation of the connection on the other side

        connected_user_post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(
            PostReaction.objects.filter(post_id=connected_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_can_react_to_user_public_post(self):
        """
          should be able to reaction in the public post of any user and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()

        foreign_user_post = foreign_user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(foreign_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=foreign_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 1)

    def test_cannot_react_to_followed_user_encircled_post(self):
        """
          should be able to reaction in the encircled post of a followed user return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_follow = make_user()
        circle = make_circle(creator=user_to_follow)

        user.follow_user_with_id(user_to_follow.pk)

        followed_user_post = user_to_follow.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(followed_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            PostReaction.objects.filter(post_id=followed_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_cannot_react_in_post_from_community_banned_from(self):
        """
          should not be able to react in the post of a community banned from and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(
            PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_cannot_react_to_closed_community_post_if_not_creator(self):
        """
          should NOT be able to react in a closed community post if not creator
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        community_post = post_creator.create_community_post(community_name=community.name,
                                                            text=make_fake_post_comment_text())
        community_post.is_closed = True
        community_post.save()

        emoji_group = make_reactions_emoji_group()
        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(community_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            PostReaction.objects.filter(post_id=community_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_can_react_to_closed_community_post_if_creator(self):
        """
          should be able to react in a closed community post if creator
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        community_post = post_creator.create_community_post(community_name=community.name,
                                                            text=make_fake_post_comment_text())
        community_post.is_closed = True
        community_post.save()

        emoji_group = make_reactions_emoji_group()
        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        headers = make_authentication_headers_for_user(post_creator)
        url = self._get_url(community_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=community_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=post_creator.pk).count() == 1)

    def test_cannot_react_to_blocked_user_post(self):
        """
          should not be able to react to a blocked user post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user.follow_user_with_id(user_to_block.pk)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=user_to_block.pk)

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_cannot_react_to_blocking_user_post(self):
        """
          should not be able to react to a blocking user post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user.follow_user_with_id(user_to_block.pk)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_cannot_react_to_blocked_user_community_post(self):
        """
          should not be able to react to a blocked user community post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=user_to_block.pk)

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertTrue(
            PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_cannot_react_to_blocking_user_community_post(self):
        """
          should not be able to react to a blocking user community post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertTrue(
            PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_can_react_to_blocked_community_staff_member_post(self):
        """
          should be able to react to a blocked community staff member post and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=community_owner.pk)

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 1)

    def test_can_react_to_blocking_community_staff_member_post(self):
        """
          should be able to react to a blocking community staff member post and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        community_owner.block_user_with_id(user_id=user.pk)

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 1)

    def test_can_react_to_post_only_once(self):
        """
         should be able to reaction in own post only once, update the old reaction and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        new_post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(new_post_reaction_emoji_id, emoji_group.pk)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostReaction.objects.filter(post_id=post.pk, reactor_id=user.pk).count() == 1)

    def test_reacting_in_foreign_post_creates_notification(self):
        """
         should create a notification when reacting on a foreign post
         """
        user = make_user()
        reactor = make_user()

        headers = make_authentication_headers_for_user(reactor)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertTrue(PostReactionNotification.objects.filter(post_reaction__emoji__id=post_reaction_emoji_id,
                                                                notification__owner=user).exists())

    def test_reacting_in_own_post_does_not_create_notification(self):
        """
         should not create a notification when reacting on an own post
         """
        user = make_user()

        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertFalse(PostReactionNotification.objects.filter(post_reaction__emoji__id=post_reaction_emoji_id,
                                                                 notification__owner=user).exists())

    def _get_create_post_reaction_request_data(self, emoji_id, emoji_group_id):
        return {
            'emoji_id': emoji_id,
            'group_id': emoji_group_id
        }

    def _get_url(self, post):
        return reverse('post-reactions', kwargs={
            'post_uuid': post.uuid,
        })


class PostReactionsEmojiCountAPITests(OpenbookAPITestCase):
    """
    PostReactionsEmojiCountAPI
    """

    def test_can_retrieve_reactions_emoji_count(self):
        """
        should be able to retrieve a valid reactions emoji count and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        emoji_group = make_reactions_emoji_group()

        emojis_to_react_with = [
            {
                'emoji': make_emoji(group=emoji_group),
                'count': 3
            },
            {
                'emoji': make_emoji(group=emoji_group),
                'count': 7
            },
            {
                'emoji': make_emoji(group=emoji_group),
                'count': 2
            }
        ]

        reactions = {}

        for reaction in emojis_to_react_with:
            id = reaction.get('emoji').pk
            reactions[str(id)] = reaction

        for reaction in emojis_to_react_with:
            for count in range(reaction['count']):
                reactor = make_user()
                emoji = reaction.get('emoji')
                reactor.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, )

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_emojis_counts = json.loads(response.content)

        self.assertTrue(len(response_emojis_counts), len(emojis_to_react_with))

        for response_emoji_count in response_emojis_counts:
            response_emoji_id = response_emoji_count.get('emoji').get('id')
            count = response_emoji_count.get('count')
            reaction = reactions[str(response_emoji_id)]
            reaction_emoji = reaction['emoji']
            self.assertIsNotNone(reaction_emoji)
            reaction_count = reaction['count']
            self.assertEqual(count, reaction_count)

    def test_cannot_retrieve_reaction_from_blocked_user(self):
        """
         should not be able to retrieve the reaction from a blocked user
         """
        user = make_user()

        post_creator = make_user()
        blocked_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)
        blocked_user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, )

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_reactions = json.loads(response.content)

        self.assertEqual(len(response_reactions), 0)

    def test_cannot_retrieve_reactions_from_blocking_user(self):
        """
         should not be able to retrieve the reactions from a blocking user
         """
        user = make_user()

        post_creator = make_user()
        blocking_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)
        blocking_user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, )

        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_reactions = json.loads(response.content)

        self.assertEqual(len(response_reactions), 0)

    def test_cannot_retrieve_reactions_from_blocked_user_in_a_community(self):
        """
         should not be able to retrieve the reactions from a blocked user in a community
         """
        user = make_user()

        post_creator = make_user()
        community = make_community(creator=post_creator)

        blocked_user = make_user()

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)
        blocked_user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, )

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_reactions = json.loads(response.content)

        self.assertEqual(len(response_reactions), 0)

    def test_cannot_retrieve_reactions_from_blocking_user_in_a_community(self):
        """
         should not be able to retrieve the reactions from a blocking user in a community
         """
        user = make_user()

        post_creator = make_user()
        community = make_community(creator=post_creator)

        blocking_user = make_user()

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)
        blocking_user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, )

        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_reactions = json.loads(response.content)

        self.assertEqual(len(response_reactions), 0)

    def test_can_retrieve_reactions_from_blocked_user_in_a_community_if_staff(self):
        """
         should be able to retrieve the reactions from a blocked user in a community if staff member
         """
        user = make_user()
        community = make_community(creator=user)
        post_creator = make_user()
        blocked_user = make_user()

        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)
        blocked_user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, )

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_emoji_counts = json.loads(response.content)

        self.assertEqual(1, len(response_emoji_counts))

        response_emoji_count = response_emoji_counts[0]

        response_emoji_id = response_emoji_count.get('emoji').get('id')
        response_emoji_count = response_emoji_count.get('count')

        self.assertEqual(response_emoji_id, emoji.pk)
        self.assertEqual(1, response_emoji_count)

    def test_can_retrieve_reactions_from_blocking_user_in_a_community_if_staff(self):
        """
         should be able to retrieve the reactions from a blocking user in a community if staff member
         """
        user = make_user()
        community = make_community(creator=user)
        post_creator = make_user()
        blocking_user = make_user()

        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)
        blocking_user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, )

        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_emoji_counts = json.loads(response.content)

        self.assertEqual(1, len(response_emoji_counts))

        response_emoji_count = response_emoji_counts[0]

        response_emoji_id = response_emoji_count.get('emoji').get('id')
        response_emoji_count = response_emoji_count.get('count')

        self.assertEqual(response_emoji_id, emoji.pk)
        self.assertEqual(1, response_emoji_count)

    def _get_url(self, post):
        return reverse('post-reactions-emoji-count', kwargs={
            'post_uuid': post.uuid
        })


class TestPostReactionEmojiGroups(OpenbookAPITestCase):
    """
    PostReactionEmojiGroups API
    """

    def test_can_retrieve_reactions_emoji_groups(self):
        """
         should be able to retrieve post reaction emoji groups
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        group_ids = []
        amount_of_groups = 4

        for x in range(amount_of_groups):
            group = make_emoji_group(is_reaction_group=True)
            group_ids.append(group.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)
        self.assertTrue(response.status_code, status.HTTP_200_OK)

        response_groups = json.loads(response.content)
        response_groups_ids = [group['id'] for group in response_groups]

        self.assertEqual(len(response_groups), len(group_ids))

        for group_id in group_ids:
            self.assertIn(group_id, response_groups_ids)

    def test_cannot_retrieve_non_reactions_emoji_groups(self):
        """
         should not able to retrieve non post reaction emoji groups
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        group_ids = []
        amount_of_groups = 4

        for x in range(amount_of_groups):
            group = make_emoji_group(is_reaction_group=False)
            group_ids.append(group.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)
        self.assertTrue(response.status_code, status.HTTP_200_OK)

        response_groups = json.loads(response.content)

        self.assertEqual(len(response_groups), 0)

    def _get_url(self):
        return reverse('posts-emoji-groups')
