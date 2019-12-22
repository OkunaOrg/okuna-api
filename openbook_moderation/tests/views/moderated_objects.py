import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community, make_fake_post_text, make_global_moderator, make_moderation_category, \
    make_fake_post_comment_text, make_hashtag
from openbook_moderation.models import ModeratedObject

fake = Faker()


class GlobalModeratedObjectsAPITests(OpenbookAPITestCase):
    """
    GlobalModeratedObjectsAPI
    """

    def test_retrieves_post_moderated_objects(self):
        """
        should be able to retrieve all moderated objects by default and return 200
        """

        global_moderator = make_global_moderator()

        amount_of_posts = 5
        posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post = post_creator.create_public_post(text=make_fake_post_text())
            posts_ids.append(post.pk)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(posts_ids), len(response_moderated_objects))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, posts_ids)

    def test_retrieves_hashtag_moderated_objects(self):
        """
        should be able to retrieve all hashtag moderated objects and return 200
        """

        global_moderator = make_global_moderator()

        amount_of_hashtags = 5
        hashtags_ids = []

        for i in range(0, amount_of_hashtags):
            reporter_user = make_user()
            hashtag = make_hashtag()
            hashtags_ids.append(hashtag.pk)
            report_category = make_moderation_category()
            reporter_user.report_hashtag(hashtag=hashtag, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(hashtags_ids), len(response_moderated_objects))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_hashtag_id = response_moderated_object.get('object_id')
            response_hashtag_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_hashtag_moderated_object_type, ModeratedObject.OBJECT_TYPE_HASHTAG)

            self.assertIn(response_moderated_object_hashtag_id, hashtags_ids)

    def test_retrieves_post_comment_moderated_objects(self):
        """
        should be able to retrieve all moderated objects by default and return 200
        """

        global_moderator = make_global_moderator()

        amount_of_post_comments = 5
        post_comments_ids = []

        for i in range(0, amount_of_post_comments):
            reporter_user = make_user()
            post = reporter_user.create_public_post(text=make_fake_post_text())
            post_comment_creator = make_user()
            post_comment = post_comment_creator.comment_post(post=post, text=make_fake_post_comment_text())
            post_comments_ids.append(post_comment.pk)
            report_category = make_moderation_category()
            reporter_user.report_comment_for_post(post_comment=post_comment, post=post, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(post_comments_ids), len(response_moderated_objects))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_comment_id = response_moderated_object.get('object_id')
            response_post_comment_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_comment_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST_COMMENT)

            self.assertIn(response_moderated_object_post_comment_id, post_comments_ids)

    def test_retrieves_user_moderated_objects(self):
        """
        should be able to retrieve all moderated objects by default and return 200
        """

        global_moderator = make_global_moderator()

        amount_of_users = 5
        users_ids = []

        for i in range(0, amount_of_users):
            reporter_user = make_user()
            user = make_user()
            users_ids.append(user.pk)
            report_category = make_moderation_category()
            reporter_user.report_user(user=user, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(users_ids), len(response_moderated_objects))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_user_id = response_moderated_object.get('object_id')
            response_user_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_user_moderated_object_type, ModeratedObject.OBJECT_TYPE_USER)

            self.assertIn(response_moderated_object_user_id, users_ids)

    def test_retrieves_community_moderated_objects(self):
        """
        should be able to retrieve all moderated objects by default and return 200
        """

        global_moderator = make_global_moderator()

        amount_of_communities = 5
        communities_ids = []

        for i in range(0, amount_of_communities):
            reporter_community = make_user()
            community_creator = make_user()
            community = make_community(creator=community_creator)
            communities_ids.append(community.pk)
            report_category = make_moderation_category()
            reporter_community.report_community(community=community, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(communities_ids), len(response_moderated_objects))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_community_id = response_moderated_object.get('object_id')
            response_community_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_community_moderated_object_type, ModeratedObject.OBJECT_TYPE_COMMUNITY)

            self.assertIn(response_moderated_object_community_id, communities_ids)

    def test_can_filter_approved_moderated_objects(self):
        """
        should be able to filter on approved moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        amount_of_posts = 5
        amount_of_approved_post_moderated_objects = 2

        approved_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post = post_creator.create_public_post(text=make_fake_post_text())
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_approved_post_moderated_objects:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                global_moderator.approve_moderated_object(moderated_object=moderated_object)
                approved_moderated_objects_posts_ids.append(post.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'statuses': ModeratedObject.STATUS_APPROVED}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(approved_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, approved_moderated_objects_posts_ids)

    def test_can_filter_pending_moderated_objects(self):
        """
        should be able to filter on pending moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        amount_of_posts = 5
        amount_of_pending_post_moderated_objects = 2

        pending_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post = post_creator.create_public_post(text=make_fake_post_text())
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_pending_post_moderated_objects:
                pending_moderated_objects_posts_ids.append(post.pk)
            else:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'statuses': ModeratedObject.STATUS_PENDING}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(pending_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, pending_moderated_objects_posts_ids)

    def test_can_filter_rejected_moderated_objects(self):
        """
        should be able to filter rejected moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        amount_of_posts = 5
        amount_of_rejected_post_moderated_objects = 2

        rejected_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post = post_creator.create_public_post(text=make_fake_post_text())
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_rejected_post_moderated_objects:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                global_moderator.reject_moderated_object(moderated_object=moderated_object)
                rejected_moderated_objects_posts_ids.append(post.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'statuses': ModeratedObject.STATUS_REJECTED}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(rejected_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, rejected_moderated_objects_posts_ids)

    def test_can_filter_verified_moderated_objects(self):
        """
        should be able to filter on verified moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        amount_of_posts = 5
        amount_of_verified_post_moderated_objects = 2

        verified_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post = post_creator.create_public_post(text=make_fake_post_text())
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_verified_post_moderated_objects:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                global_moderator.approve_moderated_object(moderated_object=moderated_object)
                global_moderator.verify_moderated_object(moderated_object=moderated_object)
                verified_moderated_objects_posts_ids.append(post.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'verified': True}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(verified_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, verified_moderated_objects_posts_ids)

    def test_can_filter_unverified_moderated_objects(self):
        """
        should be able to filter on unverified moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        amount_of_posts = 5
        amount_of_unverified_post_moderated_objects = 2

        unverified_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post = post_creator.create_public_post(text=make_fake_post_text())
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_unverified_post_moderated_objects:
                unverified_moderated_objects_posts_ids.append(post.pk)
            else:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                global_moderator.approve_moderated_object(moderated_object=moderated_object)
                global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'verified': False}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(unverified_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, unverified_moderated_objects_posts_ids)

    def test_can_filter_post_moderated_objects(self):
        """
        should be able to filter post moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        # Noise to be able to filter
        report_category = make_moderation_category()
        reported_user = make_user()
        reporter_user.report_user(user=reported_user, category_id=report_category.pk)

        # Item to filter for
        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())
        reporter_user.report_post(post=post, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'types': ModeratedObject.OBJECT_TYPE_POST}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(1, len(response_moderated_objects))

        response_moderated_object = response_moderated_objects[0]

        response_moderated_object_post_id = response_moderated_object.get('object_id')
        response_post_moderated_object_type = response_moderated_object.get('object_type')
        self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

        self.assertEqual(response_moderated_object_post_id, post.pk)

    def test_can_filter_post_comment_moderated_objects(self):
        """
        should be able to filter post_comment moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        # Noise to be able to filter
        report_category = make_moderation_category()
        reported_user = make_user()
        reporter_user.report_user(user=reported_user, category_id=report_category.pk)

        # Item to filter for
        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())
        post_comment = post_creator.comment_post(post=post, text=make_fake_post_text())
        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'types': ModeratedObject.OBJECT_TYPE_POST_COMMENT}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(1, len(response_moderated_objects))

        response_moderated_object = response_moderated_objects[0]

        response_moderated_object_id = response_moderated_object.get('object_id')
        response_post_moderated_object_type = response_moderated_object.get('object_type')
        self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST_COMMENT)

        self.assertEqual(response_moderated_object_id, post.pk)

    def test_can_filter_user_moderated_objects(self):
        """
        should be able to filter user moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        # Noise to be able to filter
        report_category = make_moderation_category()
        community_creator = make_user()
        reported_community = make_community(creator=community_creator)
        reporter_user.report_community(community=reported_community, category_id=report_category.pk)

        # Item to filter for
        user = make_user()
        reporter_user.report_user(user=user, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'types': ModeratedObject.OBJECT_TYPE_USER}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(1, len(response_moderated_objects))

        response_moderated_object = response_moderated_objects[0]

        response_moderated_object_id = response_moderated_object.get('object_id')
        response_user_moderated_object_type = response_moderated_object.get('object_type')
        self.assertEqual(response_user_moderated_object_type, ModeratedObject.OBJECT_TYPE_USER)

        self.assertEqual(response_moderated_object_id, user.pk)

    def test_can_filter_community_moderated_objects(self):
        """
        should be able to filter community moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        # Noise to be able to filter
        report_category = make_moderation_category()
        reported_user = make_user()
        reporter_user.report_user(user=reported_user, category_id=report_category.pk)

        # Item to filter for
        community_creator = make_user()
        community = make_community(creator=community_creator)
        reporter_user.report_community(community=community, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.get(url, {'types': ModeratedObject.OBJECT_TYPE_COMMUNITY}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(1, len(response_moderated_objects))

        response_moderated_object = response_moderated_objects[0]

        response_moderated_object_id = response_moderated_object.get('object_id')
        response_community_moderated_object_type = response_moderated_object.get('object_type')
        self.assertEqual(response_community_moderated_object_type, ModeratedObject.OBJECT_TYPE_COMMUNITY)

        self.assertEqual(response_moderated_object_id, community.pk)

    def test_cant_retrieve_moderated_objects_if_regular_user(self):
        """
        should not be able to retrieve all moderated objects if regular user and return 400
        """
        regular_user = make_user()

        amount_of_posts = 5
        posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post = post_creator.create_public_post(text=make_fake_post_text())
            posts_ids.append(post.pk)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_retrieve_moderated_objects_if_community_moderator(self):
        """
        should not be able to retrieve all moderated objects if community moderator and return 400
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username)

        amount_of_posts = 5
        posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post_creator.join_community_with_name(community_name=community.name)
            post = post_creator.create_public_post(text=make_fake_post_text())
            posts_ids.append(post.pk)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _get_url(self):
        return reverse('global-moderated-objects')


class CommunityModeratedObjectsAPITests(OpenbookAPITestCase):
    """
    CommunityModeratedObjectsAPI
    """

    def test_retrieves_community_post_moderated_objects_if_moderator(self):
        """
        should be able to retrieve all community post moderated objects if moderator and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_posts = 5
        posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post_creator.join_community_with_name(community_name=community.name)
            post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
            posts_ids.append(post.pk)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(posts_ids), len(response_moderated_objects))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, posts_ids)

    def test_retrieves_community_post_comment_moderated_objects_if_moderator(self):
        """
        should be able to retrieve all community post comment moderated objects if moderator and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_post_comments = 5
        post_comments_ids = []

        for i in range(0, amount_of_post_comments):
            reporter_user = make_user()
            post_comment_creator = make_user()
            post_comment_creator.join_community_with_name(community_name=community.name)
            post = post_comment_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
            post_comment = post_comment_creator.comment_post(post=post, text=make_fake_post_comment_text(), )
            post_comments_ids.append(post_comment.pk)
            report_category = make_moderation_category()
            reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(post_comments_ids), len(response_moderated_objects))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_comment_id = response_moderated_object.get('object_id')
            response_post_comment_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_comment_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST_COMMENT)

            self.assertIn(response_moderated_object_post_comment_id, post_comments_ids)

    def test_cannot_retrieve_user_moderated_objects_if_moderator(self):
        """
        should not be able to retrieve user moderated objects if moderator and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_user = 5

        for i in range(0, amount_of_user):
            reporter_user = make_user()
            reporter_user.join_community_with_name(community_name=community.name)
            user = make_user()
            user.join_community_with_name(community_name=community.name)
            report_category = make_moderation_category()
            reporter_user.report_user(user=user, category_id=report_category.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(0, len(response_moderated_objects))

    def test_cannot_retrieve_community_moderated_objects_if_moderator(self):
        """
        should not be able to retrieve community moderated objects if moderator and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_communities = 5

        for i in range(0, amount_of_communities):
            reporter_user = make_user()
            reporter_user.join_community_with_name(community_name=community.name)
            report_category = make_moderation_category()
            reporter_user.report_community(community=community, category_id=report_category.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(0, len(response_moderated_objects))

    def test_can_filter_approved_moderated_objects(self):
        """
        should be able to filter on approved moderated objects and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_posts = 5
        amount_of_approved_post_moderated_objects = 2

        approved_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post_creator.join_community_with_name(community_name=community.name)
            post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_approved_post_moderated_objects:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                community_moderator.approve_moderated_object(moderated_object=moderated_object)
                approved_moderated_objects_posts_ids.append(post.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'statuses': ModeratedObject.STATUS_APPROVED}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(approved_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, approved_moderated_objects_posts_ids)

    def test_can_filter_pending_moderated_objects(self):
        """
        should be able to filter on pending moderated objects and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_posts = 5
        amount_of_pending_post_moderated_objects = 2

        pending_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post_creator.join_community_with_name(community_name=community.name)
            post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_pending_post_moderated_objects:
                pending_moderated_objects_posts_ids.append(post.pk)
            else:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                community_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'statuses': ModeratedObject.STATUS_PENDING}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(pending_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, pending_moderated_objects_posts_ids)

    def test_can_filter_rejected_moderated_objects(self):
        """
        should be able to filter on rejected moderated objects and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_posts = 5
        amount_of_rejected_post_moderated_objects = 2

        rejected_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post_creator.join_community_with_name(community_name=community.name)
            post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_rejected_post_moderated_objects:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                community_moderator.reject_moderated_object(moderated_object=moderated_object)
                rejected_moderated_objects_posts_ids.append(post.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'statuses': ModeratedObject.STATUS_REJECTED}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(rejected_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, rejected_moderated_objects_posts_ids)

    def test_can_filter_verified_moderated_objects(self):
        """
        should be able to filter on verified moderated objects and return 200
        """
        global_moderator = make_global_moderator()
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_posts = 5
        amount_of_verified_post_moderated_objects = 2

        verified_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post_creator.join_community_with_name(community_name=community.name)
            post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_verified_post_moderated_objects:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                community_moderator.approve_moderated_object(moderated_object=moderated_object)
                global_moderator.verify_moderated_object(moderated_object=moderated_object)
                verified_moderated_objects_posts_ids.append(post.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'verified': True}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(verified_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, verified_moderated_objects_posts_ids)

    def test_can_filter_unverified_moderated_objects(self):
        """
        should be able to filter on unverified moderated objects and return 200
        """
        global_moderator = make_global_moderator()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        amount_of_posts = 5
        amount_of_unverified_post_moderated_objects = 2

        unverified_moderated_objects_posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post_creator.join_community_with_name(community_name=community.name)
            post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

            if i < amount_of_unverified_post_moderated_objects:
                unverified_moderated_objects_posts_ids.append(post.pk)
            else:
                moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                           category_id=report_category.pk)
                community_moderator.approve_moderated_object(moderated_object=moderated_object)
                global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'verified': False}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(len(response_moderated_objects), len(unverified_moderated_objects_posts_ids))

        for response_moderated_object in response_moderated_objects:
            response_moderated_object_post_id = response_moderated_object.get('object_id')
            response_post_moderated_object_type = response_moderated_object.get('object_type')
            self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

            self.assertIn(response_moderated_object_post_id, unverified_moderated_objects_posts_ids)

    def test_can_filter_post_moderated_objects(self):
        """
        should be able to filter post moderated objects and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        report_category = make_moderation_category()

        reporter_user = make_user()

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        reporter_user.report_post(post=post, category_id=report_category.pk)

        post_commenter = make_user()
        post_commenter.join_community_with_name(community_name=community.name)
        post_comment = post_commenter.comment_post(post=post, text=make_fake_post_comment_text())
        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'types': ModeratedObject.OBJECT_TYPE_POST}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(1, len(response_moderated_objects))

        response_moderated_object = response_moderated_objects[0]

        response_moderated_object_post_id = response_moderated_object.get('object_id')
        response_post_moderated_object_type = response_moderated_object.get('object_type')
        self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST)

        self.assertEqual(response_moderated_object_post_id, post.pk)

    def test_can_filter_post_comment_moderated_objects(self):
        """
        should be able to filter post_comment moderated objects and return 200
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        report_category = make_moderation_category()

        reporter_user = make_user()

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        reporter_user.report_post(post=post, category_id=report_category.pk)

        post_commenter = make_user()
        post_commenter.join_community_with_name(community_name=community.name)
        post_comment = post_commenter.comment_post(post=post, text=make_fake_post_comment_text())
        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'types': ModeratedObject.OBJECT_TYPE_POST_COMMENT}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderated_objects = json.loads(response.content)

        self.assertEqual(1, len(response_moderated_objects))

        response_moderated_object = response_moderated_objects[0]

        response_moderated_object_post_id = response_moderated_object.get('object_id')
        response_post_moderated_object_type = response_moderated_object.get('object_type')
        self.assertEqual(response_post_moderated_object_type, ModeratedObject.OBJECT_TYPE_POST_COMMENT)

        self.assertEqual(response_moderated_object_post_id, post_comment.pk)

    def test_cant_filter_user_moderated_objects(self):
        """
        should be not able to filter user moderated objects and return 400
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)
        reporter_user = make_user()

        reported_user = make_user()
        reported_user.join_community_with_name(community_name=community.name)

        reporter_user.report_user_with_username(username=reported_user.username,
                                                category_id=make_moderation_category().pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'types': ModeratedObject.OBJECT_TYPE_USER}, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_filter_community_moderated_objects(self):
        """
        should not be able to filter community moderated objects and return 400
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)
        reporter_user = make_user()
        reporter_user.report_community_with_name(community_name=community.name,
                                                 category_id=make_moderation_category().pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, {'types': ModeratedObject.OBJECT_TYPE_COMMUNITY}, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_moderated_objects_if_not_community_moderator(self):
        """
        should not be able to retrieve all moderated objects if not community moderators and return 400
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)

        amount_of_posts = 5
        posts_ids = []

        for i in range(0, amount_of_posts):
            reporter_user = make_user()
            post_creator = make_user()
            post_creator.join_community_with_name(community_name=community.name)
            post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
            posts_ids.append(post.pk)
            report_category = make_moderation_category()
            reporter_user.report_post(post=post, category_id=report_category.pk)

        url = self._get_url(community=community)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _get_url(self, community):
        return reverse('community-moderated-objects', kwargs={
            'community_name': community.name
        })
