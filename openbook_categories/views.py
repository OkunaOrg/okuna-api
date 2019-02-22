# Create your views here.
from django.db import transaction
from django.http import QueryDict
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_categories.serializers import GetCategoriesCategorySerializer
from openbook_common.utils.model_loaders import get_category_model


class Categories(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        Category = get_category_model()
        categories = Category.objects.all().order_by('order')
        response_serializer = GetCategoriesCategorySerializer(categories, many=True,
                                                              context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
