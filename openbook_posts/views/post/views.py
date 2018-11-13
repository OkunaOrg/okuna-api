from rest_framework.views import APIView


class PostItem(APIView):
    def get(self, request, post_id):
        pass


class PostItemComments(APIView):
    def put(self, request, post_id):
        pass
