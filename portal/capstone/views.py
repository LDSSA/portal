from rest_framework.response import Response
from rest_framework.views import APIView


class CapstonePredictView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        return Response({'proba': .6})


class CapstoneUpdateView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        return Response({'msg': 'ok'})