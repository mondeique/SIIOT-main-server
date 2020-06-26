# -*- encoding: utf-8 -*-
from django import forms
from django.contrib import admin
# from chats.models import ChatRoom, ChatRoomTagValue, ChatMessage, ChatRoomReportHistory
from custom_manage.sites import staff_panel
from custom_manage.tools import ReadOnlyTabularInline

#
# class ChatRoomTagValueInline(ReadOnlyTabularInline):
#     model = ChatRoomTagValue
#     fields = ['user', 'key', 'value']

#
# class ChatRoomAdmin(admin.ModelAdmin):
#     list_display = ['id', 'owner', 'room_type', '_question_id', 'get_chat_room_link']
#     readonly_fields = ['room_type', 'owner']
#     inlines = [ChatRoomTagValueInline]
#     search_fields = ['owner__email',
#                      'owner__common_profile__nickname',
#                      'owner__common_profile__social_nickname',
#                      '=question__id']
#
#     def get_queryset(self, request):
#         return super(ChatRoomAdmin, self).get_queryset(request).select_related('question')
#
#     def _question_id(self, obj):
#         try:
#             return obj.question.id
#         except:
#             return ''
#
#
# class ChatMessageAdmin(admin.ModelAdmin):
#     list_display = ['id', 'message_type', 'code', 'created_at']
#     raw_id_fields = ['room', 'source_user', 'target_user', 'postback_parent']
#     search_fields = ['room__id']
#
#
# class ChatRoomTagValueAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'room', 'key', 'get_value_staff']
#     raw_id_fields = ['room', 'user']
#     search_fields = ['room__id']
#
#
# class ChatRoomReportHistoryAdmin(admin.ModelAdmin):
#     list_display = ['id', 'room', 'user', 'reporter', 'reason']
#     raw_id_fields = ['room', 'user', 'reporter']
#     search_fields = ['room__id']
#
#
# staff_panel.register(ChatRoom, ChatRoomAdmin)
# staff_panel.register(ChatMessage, ChatMessageAdmin)
# staff_panel.register(ChatRoomTagValue, ChatRoomTagValueAdmin)
# staff_panel.register(ChatRoomReportHistory, ChatRoomReportHistoryAdmin)
