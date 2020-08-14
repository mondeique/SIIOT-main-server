from django.conf import settings
from django.db import models
# import jsonfield


def get_choices():
    from notification.types import action_types
    return action_types


class Notification(models.Model):
    target = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, help_text="대상을 의미합니다.",
                               related_name='notifications', on_delete=models.CASCADE)
    action = models.IntegerField(choices=get_choices(), db_index=True,
                                 help_text="해당 notification의 종류를 의미합니다.")
    title = models.CharField(max_length=30, null=True, blank=True, help_text="제목입니다.")
    content = models.CharField(max_length=100, null=True, blank=True, help_text="내용입니다.")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    image = models.TextField(blank=True, null=True, help_text="프로필 이미지 등 push msg에 사용되는 큰 아이콘")
    icon = models.TextField(blank=True, null=True, help_text="작은 아이콘 이미지")
    link = models.TextField(blank=True, null=True, help_text="딥링크 주소")
    big_image = models.TextField(blank=True, null=True, help_text="큰 이미지 notification에 사용합니다.")

    class Meta:
        verbose_name_plural = 'Push 알림'
        ordering = ['-created_at']

    @property
    def is_readable(self):
        try:
            from notification.types import notification_types
            return notification_types[self.action].is_readable
        except:
            return False

    @property
    def is_notifiable(self):
        try:
            from notification.types import notification_types
            return notification_types[self.action].is_notifiable
        except:
            return False


class NotificationUserLog(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='user_logs')
    read_at = models.DateTimeField(blank=True, null=True, help_text="유저가 해당 메시지를 읽었다면 null이 아니게 됩니다.")
    deleted_at = models.DateTimeField(blank=True, null=True,
                                      help_text="해당 푸쉬가 보여서는 안될 종류의 것이라면 생성과 동시에 auto_now_add 유저가 해당 메시지를 지웠다면 null이 아니게 됩니다.")
    # extras = jsonfield.JSONField(null=True, blank=True, help_text="json형식으로 추가 정보를 전달할 때 사용합니다.")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True, null=True)
