from django.conf import settings
from django.db import models

from core.fields import S3ImageKeyField
from products.category.models import MixCategory, Size, Color, SecondCategory
from products.shopping_mall.models import ShoppingMall
from products.supplymentary.models import SizeCaptureImage, PurchasedTime, PurchasedReceipt


def img_directory_path_profile(instance, filename):
    return 'user/{}/profile/{}'.format(instance.user.nickname, filename)


class Product(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="products", on_delete=models.CASCADE)

    # upload type
    # BY_RECEIPT = 11
    # BY_SELF = 12
    # UPLOAD_TYPE = (
    #     (BY_RECEIPT, '구매내역 인증 방식'),
    #     (BY_SELF, '직접 업로드 방식'),
    # )
    # upload_type = models.IntegerField(choices=UPLOAD_TYPE)

    # receipt
    receipt = models.OneToOneField(PurchasedReceipt, on_delete=models.SET_NULL, null=True, blank=True, related_name="product")

    # product condition
    UNOPENED = 1
    TEST = 2
    ONCETWICE = 3
    OVER = 4
    OTHER = 0
    CONDITION = (
        (UNOPENED, '미개봉'),
        (TEST, '시험 착용'),
        (ONCETWICE, '한두번 착용'),
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

    temp_save = models.BooleanField(default=True, help_text="임시저장 중인 상품을 확인하기 위해 만들었습니다. upload complete = False")

    # crawl product id
    crawl_product_id = models.IntegerField(null=True, blank=True)

    # user input data
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='상품명',
                            help_text="쇼핑몰 상품명과 다르게 저장하기 위해 사용")
    price = models.IntegerField(null=True, blank=True, verbose_name='가격')
    content = models.TextField(null=True, blank=True, verbose_name="설명")
    free_delivery = models.BooleanField(default=False, help_text="무료배송 여부")

    # category
    category = models.ForeignKey(SecondCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text="카테고리 참고 모델입니다. 카테고리 모델은 조합마다 하나만 생성됩니다,")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    # size capture
    size_capture = models.ForeignKey(SizeCaptureImage, on_delete=models.SET_NULL, null=True, blank=True)

    # 구매 시기
    purchased_time = models.ForeignKey(PurchasedTime, on_delete=models.CASCADE, null=True, blank=True)
    
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
            if self.receipt:
                return '[업로드 요청]' + self.name
            if self.name:
                return '[임시 저장]' + self.name
            else:
                return '[임시 저장 (상품명 미입력)]'
        else:
            if self.name:
                return '[업로드]' + self.name
        return ''

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

    @property
    def temp_crawl_thumbnail_image_url(self):
        return settings.MEDIA_ROOT + '999ea1e3-335e-44e9-b2f6-30c40c2dfa86.png'

    @property
    def temp_crawl_product_name(self):
        return ''

    @property
    def temp_crawl_int_price(self):
        return '정보를 불러오지 못했어요'


class ProductStatus(models.Model):
    # sold 처리 주체 : by 결제, by seller -> 이 경우 다시 sold 해제 가능
    SOLD_STATUS = [
        (1, 'by payment'),
        (2, 'by seller')
    ]

    sold = models.BooleanField(default=False, verbose_name='판매여부')
    sold_status = models.IntegerField(choices=SOLD_STATUS, null=True, blank=True, verbose_name='판매 과정')

    product = models.OneToOneField(Product, related_name='status', on_delete=models.CASCADE)
    editing = models.BooleanField(default=False, help_text="판매자가 상품 정보를 수정시 True 입니다. 결제가 되지 않도록 해야합니다.")

    purchasing = models.BooleanField(default=False, help_text='구매중일 경우 True 입니다. 다른 유저 결제가 되지 않도록 해야합니다.')

    hiding = models.BooleanField(default=False, help_text="숨기기 기능을 구현하기 위해 만들었습니다. True 이면 숨김 처리가 됩니다.")


class ProductImages(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image_key = S3ImageKeyField()

    @property
    def image_url(self):
        return self.image_key.url


class ProductUploadRequest(models.Model):
    """
    구매내역 첨부 후 업로드 요청이 생길 때 생성됩니다.
    admin page에서 해당 모델을 하나씩 처리해 가면 됩니다.
    * 임시 업로드 해제시 알림 필요
    """
    product = models.ForeignKey('Product', related_name='upload_requests', on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)

    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name='담당자')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_done and self.product.crawl_product_id:
            self.product.possible_upload = True
            self.product.temp_save = False
            self.product.save()
        super(ProductUploadRequest, self).save(*args, **kwargs)


class ProductCrawlFailedUploadRequest(models.Model):
    """
    크롤링 실패 후 임시 일러스트로 업로드 요청시 생성됩니다.
    product 의 product_url을 참고하여 admin page 에서 직접 입력 해 주어야 합니다.
    * 임시 업로드 해제시 알림 필요
    """
    product = models.ForeignKey('Product', related_name="crawl_failed_upload_requests", on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)

    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name='담당자')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # 관리자가 업로드 요청 처리 한 경우
        if self.is_done:

            # 상품의 구매내역이 없는경우(직접 업로드 인 경우)
            if not self.product.receipt:
                self.product.possible_upload = True
                self.product.save()

            # 상품의 구매내역이 있고, 관리자가 업로드 한 경우
            if self.product.receipt and self.product.upload_requests.filter(is_done=True).exists():
                self.product.possible_upload = True
                self.product.save()

        super(ProductCrawlFailedUploadRequest, self).save(*args, **kwargs)


class ProductViews(models.Model):
    product = models.OneToOneField(Product, related_name='views', on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def view_counts(self):
        count = self.count * 4
        return count


class ProductLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='liker', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='liked', on_delete=models.CASCADE)
    is_liked = models.BooleanField(default=True)
