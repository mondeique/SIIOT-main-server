from django.db import models
from crawler import CRAWLER_S3_HOST


class CrawlProduct(models.Model):
    shopping_mall = models.IntegerField()
    product_name = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_url = models.CharField(max_length=300)
    thumbnail_image = models.CharField(max_length=300)
    size_image = models.CharField(max_length=300)
    product_url = models.CharField(max_length=300)
    price = models.CharField(max_length=50)
    crawled_date = models.DateTimeField(blank=True, null=True)
    is_valid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'crawler_crawlproduct'

    @property
    def thumbnail_image_url(self):
        s3_host = CRAWLER_S3_HOST
        key = self.thumbnail_image
        url = s3_host + key
        return url

    @property
    def int_price(self):
        price = self.price
        int_price = int(''.join(x for x in price if x.isdigit()))
        return int_price


class CrawlDetailImage(models.Model):
    product = models.ForeignKey('CrawlProduct', models.DO_NOTHING, related_name="detail_images")
    detail_url = models.CharField(max_length=200)
    detail_image = models.CharField(max_length=100) # s3 saved image name

    class Meta:
        managed = False
        db_table = 'crawler_crawldetailimage'

    @property
    def detail_image_url(self):
        s3_host = CRAWLER_S3_HOST
        key = self.detail_image
        url = s3_host + key
        return url
