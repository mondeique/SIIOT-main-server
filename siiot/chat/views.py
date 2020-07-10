from datetime import datetime, timedelta
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, mixins
from rest_framework.decorators import authentication_classes, action
from rest_framework import status, viewsets
from rest_framework import exceptions

from chat.models import ChatRoom
from chat.serializers import ChatRoomSerializer


class ChatRoomViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = ChatRoom.objects.all()
    permission_classes = [AllowAny, ]
    serializer_class = ChatRoomSerializer

    def list(self, request, *args, **kwargs):
        user = request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_204_NO_CONTENT)

        seller_chat_rooms = user.seller_chat_rooms.all()
        buyer_chat_rooms = user.buyer_chat_rooms.all()

        total_rooms = seller_chat_rooms|buyer_chat_rooms
        serializer = self.get_serializer(total_rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
