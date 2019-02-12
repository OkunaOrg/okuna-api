from rest_framework import serializers
from openbook_categories.models import Category


class GetCategoriesCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            'id',
            'name',
            'title',
            'description',
            'avatar',
            'color'
        )
