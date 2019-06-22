# Create your tests here.
import json
import random
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_community, make_private_community
from openbook_notifications.models import PostCommentNotification, Notification, PostCommentReplyNotification
from openbook_posts.models import PostComment

logger = logging.getLogger(__name__)
fake = Faker()


class PostCommentReactionsAPITests(APITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]
