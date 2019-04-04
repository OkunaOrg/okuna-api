from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from openbook_common.utils.model_loaders import get_post_model
from openbook_reports.views.common.serializers import GetReportCategoriesSerializer
from openbook_reports.models import ReportCategory as ReportCategoryModel
from openbook_reports.views.report_post.serializers import PostReportSerializer


def get_post_id_for_post_uuid(post_uuid):
    Post = get_post_model()
    post = Post.objects.values('id').get(uuid=post_uuid)
    return post['id']


class ReportCategory(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        report_categories = ReportCategoryModel.objects.all()
        response_serializer = GetReportCategoriesSerializer(report_categories, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)




