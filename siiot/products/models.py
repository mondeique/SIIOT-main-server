from django.conf import settings
from django.db import models

from core.fields import S3ImageKeyField
from products.category.models import MixCategory, Size, Color
from products.shopping_mall.models import ShoppingMall
from products.supplymentary.models import SizeCaptureImage, PurchasedTime, PurchasedReceipt


def img_directory_path_profile(instance, filename):
    return 'user/{}/profile/{}'.format(instance.user.nickname, filename)


class Product(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="products", on_delete=models.CASCADE)

    # upload type
    BY_RECEIPT = 11
    BY_SELF = 12
    UPLOAD_TYPE = (
        (BY_RECEIPT, '구매내역 인증 방식'),
        (BY_SELF, '직접 업로드 방식'),
    )
    upload_type = models.IntegerField(choices=UPLOAD_TYPE)

    # receipt
    receipt = models.OneToOneField(PurchasedReceipt, on_delete=models.SET_NULL, null=True, blank=True, related_name="product")

    # product condition
    UNOPENED = 1
    ONCE = 2
    TWICE = 3
    OVER = 4
    OTHER = 0
    CONDITION = (
        (UNOPENED, '미개봉'),
        (ONCE, '한번 착용'),
        (TWICE, '두번 착용'),
        (OVER, '여러번 착용'),
        (OTHER, '기타'),
    )
    condition = models.IntegerField(choices=CONDITION)

    # shopping mall
    shopping_mall = models.ForeignKey(ShoppingMall, on_delete=models.CASCADE, related_name="products")

    # shop product url
    product_url = models.URLField(null=True, blank=True, help_text="추후 링크 없는 상품을 위해 null 가능 처리")

    # check url valid -> detail page 접속시 check 하여 save, 상세페이지 return 을 결정합니다.
    valid_url = models.BooleanField(default=True,
                                    help_text="링크 유효성 검증을 위해 사용합니다. 링크가 내려간 경우 False,"
                                              "(나중)링크 없는 상품 업로드시 False로서, False 인 경우 임시 페이지를 보여줍니다.")

    temp_save = models.BooleanField(default=True, help_text="임시저장 중인 상품을 확인하기 위해 만들었습니다. upload complete = True")

    # crawl product id
    crawl_product_id = models.IntegerField(null=True, blank=True)

    # user input data
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='상품명',
                            help_text="쇼핑몰 상품명과 다르게 저장하기 위해 사용")
    price = models.IntegerField(null=True, blank=True, verbose_name='가격')
    content = models.TextField(null=True, blank=True, verbose_name="설명")
    free_delivery = models.BooleanField(default=False, help_text="무료배송 여부")

    # sold 처리 주체 : by 결제, by seller -> 이 경우 다시 sold 해제 가능
    SOLD_STATUS = [
        (1, 'by payment'),
        (2, 'by seller')
    ]
    sold = models.BooleanField(default=False, verbose_name='판매여부')
    sold_status = models.IntegerField(choices=SOLD_STATUS, null=True, blank=True, verbose_name='판매 과정')

    # category
    category = models.ForeignKey(MixCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text="카테고리 참고 모델입니다. 카테고리 모델은 조합마다 하나만 생성됩니다,")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    # size capture
    size_capture = models.ForeignKey(SizeCaptureImage, on_delete=models.SET_NULL, null=True, blank=True)

    # 구매 시기
    purchased_time = models.OneToOneField(PurchasedTime, on_delete=models.CASCADE, null=True, blank=True)
    
    # 업로드 가능 여부 (모든 정보 입력시 True)
    possible_upload = models.BooleanField(default=False,
                                          help_text="업로드 가능성 여부입니다. True 이면 main에 노출됩니다."
                                                    "운영진이 직접 올릴 때 사용합니다.")
    # 끌올 (optional)
    refresh_date = models.DateTimeField(null=True, blank=True,
                                        help_text="끌어올리기 기능을 구현하기 위해 사용합니다. 하루에 1번 제한 등을 위해 참고합니다.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True, help_text="상품 삭제시 False")

    def __str__(self):
        if self.temp_save:
            if self.name:
                return '[임시 저장]' + self.name
            else:
                return '[임시 저장 (상품명 미입력)]'
        return self.name

    @property
    def seller_name(self):
        return self.seller.nickname

    @property
    def crawl_name(self):
        crawl_id = self.crawl_product_id
        return None

    @property
    def crawl_thumbnail(self):
        crawl_id = self.crawl_product_id
        return None

    @property
    def crawl_price(self):
        crawl_id = self.crawl_product_id
        return None


class ProductImages(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image_key = S3ImageKeyField()

    @property
    def image_url(self):
        return self.image_key.url


class ProductUploadRequest(models.Model):

    product = models.ForeignKey('Product', related_name='upload_requests', on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)

    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name='담당자')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)