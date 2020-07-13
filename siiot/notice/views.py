from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny

# Create your views here.
from rest_framework.response import Response

from notice.models import Notice
from notice.serializers import NoticeListSerializer, NoticeRetrieveSerializer


class NoticeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    """
    주소 관련 api 입니다.
    """
    queryset = Notice.objects.filter(hidden=False)
    permission_classes = [AllowAny, ]

    def get_serializer_class(self):
        if self.action == 'list':
            return NoticeListSerializer
        elif self.action == 'retrieve':
            return NoticeRetrieveSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        notice = self.get_object()
        serializer = self.get_serializer(notice)
        return Response(serializer.data, status=status.HTTP_200_OK)
