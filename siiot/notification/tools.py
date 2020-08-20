# -*- encoding: utf-8 -*-
import json
import random
import math
import operator
from datetime import datetime

# from core.aws.clients import lambda_client
from notification.models import Notification, NotificationUserLog
from notification.serializers import NotificationSerializer
from notification.types import *


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def _push_android(list_user, notification):
    serializers = NotificationSerializer(notification)
    try:
        serializer_data = serializers.data
    except Exception as e:
        serializer_data = None

    if serializer_data:
        from push_notifications.models import GCMDevice
        device = GCMDevice.objects.filter(user=list_user[0])
        device.send_message(notification.content, extra={"title": notification.title, "icon": "ic_notification_icon"})
    # if serializer_data:
        # for sliced_endpoints in batch(endpoints, 100):
        #     data = {
        #         "action": notification.action,
        #         "param": serializer_data,
        #         "is_notifiable": notification.is_notifiable,
        #     }
        #     gcm_data = {
        #         "data": data,
        #         "priority": "high",
        #     }
        #     payload = json.dumps({
        #         "endpoints": sliced_endpoints,
        #         "gcm_data": gcm_data,
        #     })
        #     lambda_client.invoke(FunctionName="NotificationSender",
        #                          Payload=payload,
        #                          InvocationType='Event')


# def _push_ios(endpoints, notification, badge=1):
#     serializers = NotificationSerializer(notification)
#     try:
#         serializer_data = serializers.data
#     except Exception as e:
#         serializer_data = None
#
#     if serializer_data:
#         for sliced_endpoints in batch(endpoints, 100):
#             data = {
#                 "action": notification.action,
#                 "param": serializer_data,
#                 "is_notifiable": notification.is_notifiable,
#             }
#             gcm_data = {
#                 "data": data,
#                 "priority": "high",
#                 "notification": {
#                     "title": notification.title.encode(encoding='UTF-8', errors='strict'),
#                     "body": notification.content.encode(encoding='UTF-8', errors='strict'),
#                     "sound": None,
#                     "badge": badge,
#                     "content_available": True,
#                     "id": 0,
#                 },
#             }
#             payload = json.dumps({
#                 "endpoints": sliced_endpoints,
#                 "gcm_data": gcm_data,
#             })
#             lambda_client.invoke(FunctionName="NotificationSender",
#                                  Payload=payload,
#                                  InvocationType='Event')


def send_push_async(list_user, notification, reserved_notification=None):
    from notification.models import NotificationUserLog
    """
    1. notification model 을 생성합니다. (Notification Type 을 활용합니다.) - on_xxx 방식의 함수에서 요청
    title, content, image, link, is_readable, icon, link, big_image 등등 

    2. 해당 notification 에 해당하는 NotificationUserLog 를 bulkcreate 합니다. - send_push_async 에서 처리 
    
    3. 해당 notification 을 해당 user 들에게 send 합니다. - send_push async 에서 처리
    """
    # 1. notification model 을 생성합니다.
    bulk_data = []
    user_ids = []

    if notification.is_readable:
        deleted_at = None
    else:
        deleted_at = datetime.now()

    # for user in list_user:
    #     bulk_data.append(
    #         NotificationUserLog(notification=notification, deleted_at=deleted_at))
    #     user_ids.append(user.id)
    #
    # NotificationUserLog.objects.bulk_create(bulk_data)
    NotificationUserLog.objects.get_or_create(notification=notification, deleted_at=deleted_at)
    # device_queryset = SIIOTGCMDevice.objects.filter(user__in=user_ids)

    # badge = 1
    # if len(list_user) == 1:
    #     badge = NotificationUserLog.objects.filter(user=list_user[0], read_at=None,
    #                                                deleted_at=None).distinct().count()

    # android_endpoints = device_queryset.filter(device_type=1).values_list('endpoint_arn', flat=True)
    _push_android(list_user, notification)

    # ios_endpoints = device_queryset.filter(device_type=2).values_list('endpoint_arn', flat=True)
    # _push_ios(ios_endpoints, notification, badge=badge)


# class NotificationHelper(object):
#     """
#     action : action값(정수), notifications.models.Notification 참고
#     target : push 대상 user
#     """
#
#     # ACTION 번호 순서로 정리
#     # V1 NOTIFICATION START ============================================================================================
#     def on_student_notice_create(self, notice):
#         # ACTION 101
#         from accounts.models import User
#         StudentNotice(list_user=User.objects.filter(student_profile__isnull=False),
#                       notice=notice).send()
#
#     def on_student_event_create(self, event_notice):
#         # ACTION 102
#         from accounts.models import User
#         StudentEventNotice(list_user=User.objects.filter(student_profile__isnull=False),
#                            event_notice=event_notice).send()
#
#     def on_answer_start(self, question, solver):
#         # ACTION 200
#         locale = None
#         if question.subject:
#             locale = question.subject.locale
#         else:
#             locale = question.book_chapters.first().chapter.book.language_code
#         activate(locale)
#         StudentMatchingTeacher(list_user=[question.author], question=question, teacher=solver)
#         self.on_solve_start(question)  # Will DEPRECATED
#
#     def on_answer(self, answer):
#         # ACTION 201
#         locale = None
#         if answer.question.subject:
#             locale = answer.question.subject.locale
#         else:
#             locale = answer.question.book_chapters.first().chapter.book.language_code
#         question = answer.question
#         activate(locale)
#         StudentNewAnswer(list_user=[question.author], question=question, answer=answer).send()
#
#     def on_6_hours_before_auto_accept(self, queryset):
#         # ACTION 202 accept_question_push_every_hour
#         for question in queryset:
#             if question.subject:
#                 locale = question.subject.locale
#             else:
#                 locale = question.book_chapters.first().chapter.book.language_code
#             activate(locale)
#             StudentRequestAcceptAnswer(list_user=[question.author], question=question).send()
#
#     def on_1_hours_before_auto_accept(self, queryset):
#         # ACTION 202 accept_question_push_every_hour
#         for question in queryset:
#             locale = None
#             if question.subject:
#                 locale = question.subject.locale
#             else:
#                 locale = question.book_chapters.first().chapter.book.language_code
#             activate(locale)
#             StudentRequestAcceptAnswerOneHour(list_user=[question.author], question=question).send()
#     # V1 NOTIFICATION END ==============================================================================================