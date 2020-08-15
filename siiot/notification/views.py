# Create your views here.
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notification.models import NotificationUserLog
from notification.serializers import NotificationListSerializer


class NotificationViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = NotificationUserLog.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationListSerializer

    def list(self, request, *args, **kwargs):
        """
        notification list api
        api : GET api/v1/notification/
        * header token
        """
        user = request.user
        queryset = self.get_queryset().filter(notification__target=user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
