from django.conf import settings
from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField


class Notice(models.Model):
    """
    공지사항 모델입니다.
    """
    title = models.CharField(max_length=40, help_text="this field is title")
    content = RichTextUploadingField(help_text="rich_text_field로 이미지 등을 추가할 수 있습니다.")
    important = models.BooleanField(default=False, help_text="true일 경우 앱내 상단에 강조되어 표시됩니다.")
    hidden = models.BooleanField(default=False, help_text="true일 경우 공지 리스트에서 보이지 않습니다.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name_plural = '공지사항'