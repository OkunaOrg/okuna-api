from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.models import ModerationCategory
from openbook_moderation.views.moderation_categories.serializers import ModerationCategorySerializer


class ModerationCategories(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        moderation_categories = ModerationCategory.objects.filter(is_reaction_category=False).all().order_by('order')
        serializer = ModerationCategorySerializer(moderation_categories, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
