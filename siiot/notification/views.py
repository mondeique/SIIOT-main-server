# Create your views here.
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notification.models import NotificationUserLog
from notification.serializers import NotificationListSerializer

from core.pagination import SiiotPagination

from datetime import datetime


class NotificationViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = NotificationUserLog.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationListSerializer

    def list(self, request, *args, **kwargs):
        """
        notification list api
        api : GET api/v1/notification/
        * header token
        """
        paginator = SiiotPagination()
        user = request.user
        queryset = self.get_queryset().filter(notification__target=user)
        # like_queryset = queryset.filter(notification__action=101)
        # other_queryset = queryset.exclude(notification__action=101)
        queryset.update(read_at=datetime.now())
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
