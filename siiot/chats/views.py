# -*- encoding: utf-8 -*-
import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
# from chats.models import ChatRoom, ChatMessage
# from chats.serializers import ChatRoomSerializer, ChatMessageFullReadSerializer, ChatRoomResultSerializer

#
# class ChatRoomViewSet(viewsets.GenericViewSet,
#                       mixins.CreateModelMixin,
#                       mixins.RetrieveModelMixin):
#     queryset = ChatRoom.objects.all()
#     permission_classes = (IsAuthenticated,)
#     serializer_class = ChatRoomSerializer
#
#     def get_queryset(self):
#         return self.queryset.filter(owner=self.request.user)
#
#     @action(methods=['post'], detail=True, serializer_class=ChatRoomResultSerializer)
#     def result(self, request, pk=None):
#         chat_room = self.get_object()
#         if chat_room.owner != request.user:
#             return Response(status=status.HTTP_403_FORBIDDEN)
#
#         serializer = self.get_serializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save(room=chat_room)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ChatRoomView(APIView):
#     """
#     채팅 방 내용을 볼 수 프리뷰 페이지 입니다. admin page 에서 사용합니다.
#     """
#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'chats/preview.html'
#
#     def get(self, request, room_id):
#         if not request.user.is_staff:
#             raise PermissionDenied
#
#         room = ChatRoom.objects.get(id=room_id)
#         chat_message = None
#         if room:
#             queryset = ChatMessage.objects.filter(room_id=room_id, is_hidden=False, invalidated=False) \
#                 .order_by('id')
#             context = {'chat_room': room_id}
#             if queryset.exists():
#                 chat_message = ChatMessageFullReadSerializer(queryset, context=context, many=True).data
#
#         target_user_list = []
#         target_user = {
#             'id': '0',
#             'nickname': 'all'
#         }
#         target_user_list.append(target_user)
#         if chat_message:
#             for message in chat_message:
#                 target_user = message.get('target_user', None)
#                 if target_user is not None and target_user not in target_user_list:
#                     target_user_list.append(target_user)
#
#         from rest_framework.authtoken.models import Token
#         token, _ = Token.objects.get_or_create(user=request.user)
#         data = {
#             "chat_message": chat_message,
#             "chat_room": ChatRoomSerializer(room).data,
#             "target_user_list": target_user_list,
#             'token_key': token.key,
#         }
#
#         return Response(data)
from rest_framework.viewsets import ModelViewSet

from chats.models import TestChatRoom, TestChatMessage
from chats.serializers import MessageModelSerializer, MessageRetrieveSerializer


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication scheme used by DRF. DRF's SessionAuthentication uses
    Django's session framework for authentication which requires CSRF to be
    checked. In this case we are going to disable CSRF tokens for the API.
    """

    def enforce_csrf(self, request):
        return


class MessagePagination(PageNumberPagination):
    """
    Limit message prefetch to one page.
    """
    page_size = settings.MESSAGES_TO_LOAD


class TestChatRoomList(TemplateView):
    template_name = 'core/roomlist.html'
    permission_classes = (IsAuthenticated, )

    def get_context_data(self, **kwargs):
        context = super(TestChatRoomList, self).get_context_data()
        user = self.request.user
        room_qs = TestChatRoom.objects.filter(Q(buyer=user)|Q(seller=user))
        context['rooms'] = room_qs
        context['user'] = user
        return context


def room(request, room_name):
    return render(request, 'chat/room.html', {
        'room_name_json': mark_safe(json.dumps(room_name))
    })


class TestAuth(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, )
    token_model = Token

    @action(methods=['get'], detail=False)
    def get_token(self, request, *args, **kwargs):
        user = request.user
        print(user)
        token,_ = self.token_model.objects.get_or_create(user=user)
        return Response({'token': token.key})


class MessageModelViewSet(ModelViewSet):
    queryset = TestChatMessage.objects.all()
    serializer_class = MessageRetrieveSerializer
    # allowed_methods = ('GET', 'POST', 'HEAD', 'OPTIONS')
    authentication_classes = (CsrfExemptSessionAuthentication,)
    # permission_classes = [IsAuthenticated, ]
    pagination_class = MessagePagination

    def list(self, request, *args, **kwargs):
        self.queryset = self.queryset.filter(Q(room__seller=request.user) |
                                             Q(room__buyer=request.user))
        target = self.request.query_params.get('target', None)
        if target is not None:
            self.queryset = self.queryset.filter(
                Q(room__seller=request.user, room__buyer__nickname=target) |
                Q(room__seller__nickname=target, room__buyer=request.user))
        return super(MessageModelViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        print(request.user)
        msg = get_object_or_404(
            self.queryset.filter(Q(room__seller=request.user) |
                                 Q(room__buyer=request.user),
                                 Q(pk=kwargs['pk'])))
        serializer = self.get_serializer(msg)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = MessageModelSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
