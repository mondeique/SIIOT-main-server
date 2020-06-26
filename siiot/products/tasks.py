import random
import uuid
import json

import requests
from celery import shared_task
from django.conf import settings

from products.models import Product


@shared_task
def size_capture(product_id):
    product = Product.objects.get(id=product_id)
    crawl_product_id = product.crawl_product_id
    url = product.product_url

    answer_image, created = AnswerImage.objects.get_or_create(answer=answer, order=order,
                                                              defaults={'image_url': image_url})
    if not created:
        answer_image.image_url = image_url
        answer_image.save()
