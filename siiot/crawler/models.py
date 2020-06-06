from django.db import models


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


class CrawlDetailImage(models.Model):
    product = models.ForeignKey('CrawlProduct', models.DO_NOTHING, related_name="bag_images")
    detail_url = models.CharField(max_length=200)
    detail_image = models.CharField(max_length=100) # s3 saved image name

    class Meta:
        managed = False
        db_table = 'crawler_crawldetailimage'


