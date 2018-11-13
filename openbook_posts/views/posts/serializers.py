from rest_framework import serializers

from django.conf import settings
from openbook_auth.models import User, UserProfile
from openbook_circles.validators import circle_id_exists
from openbook_lists.validators import list_id_exists
from openbook_posts.models import PostImage, Post


class GetPostsSerializer(serializers.Serializer):
    circle_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField(validators=[circle_id_exists]),
    )
    list_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField(validators=[list_id_exists])
    )
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class CreatePostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_MAX_LENGTH, required=False, allow_blank=False)
    image = serializers.ImageField(allow_empty_file=False, required=False)
    circle_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField(validators=[circle_id_exists]),
    )


class PostCreatorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
        )


class PostCreatorSerializer(serializers.ModelSerializer):
    profile = PostCreatorProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'profile',
            'username'
        )


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = (
            'image',
        )


class PostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    creator = PostCreatorSerializer(many=False)

    class Meta:
        model = Post
        fields = (
            'id',
            'created',
            'text',
            'image',
            'creator'
        )
