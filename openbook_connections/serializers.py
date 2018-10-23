from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openbook_auth.models import User
from openbook_auth.validators import user_id_exists
from openbook_circles.validators import circle_id_exists
from django.utils.translation import ugettext_lazy as _

from openbook_connections.models import Connection
from openbook_connections.validators import connection_does_not_exist


class CreateConnectionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, validators=[user_id_exists])
    circle_id = serializers.IntegerField(required=True, validators=[circle_id_exists])

    def validate_user_id(self, user_id):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            # Check connection is not with oneself
            if user.pk == user_id:
                raise ValidationError(
                    _('A connection cannot be created with oneself.'),
                )
            else:
                # Check connection does not already exist
                target_user = User.objects.get(pk=user_id)
                connection_does_not_exist(user, target_user)
            return user_id
        else:
            raise ValidationError(
                _('A user is required.'),
            )


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = (
            'id',
            'user',
            'circle',
            'target_connection',
        )
