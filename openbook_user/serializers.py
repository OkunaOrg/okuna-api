from rest_framework import serializers

from openbook_auth.models import User


class GetUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'profile',
        )
        depth = 1
