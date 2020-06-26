from django.conf import settings
from django.db import models
from pilkit.processors import ResizeToFill

from payment.models import Deal
from imagekit.models import ProcessedImageField


def review_directory_path(instance, filename):
    return 'user/{}/review/thumbnail_{}'.format(instance.seller.id, filename)


class Review(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviews', on_delete=models.CASCADE)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_reviews', on_delete=models.CASCADE)
    context = models.CharField(max_length=500, null=True, blank=True)
    satisfaction = models.DecimalField(decimal_places=2, max_digits=4)
    deal = models.OneToOneField(Deal, on_delete=models.CASCADE, related_name='review')
    thumbnail = ProcessedImageField(
        null=True, blank=True,
        upload_to=review_directory_path,  # 저장 위치
        processors=[ResizeToFill(300, 300)],  # 사이즈 조정
        format='JPEG',  # 최종 저장 포맷
        options={'quality': 60})
    created_at = models.DateTimeField(auto_now_add=True)
