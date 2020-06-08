from django.contrib import admin
from django.utils.safestring import mark_safe

from crawler.models import CrawlProduct
from cunsom_manage.sites import staff_panel
from products.category.models import FirstCategory, SecondCategory, Size, Color
from products.models import Product, ProductUploadRequest
from products.shopping_mall.models import ShoppingMall
from products.supplymentary.models import PurchasedReceipt


class ProductStaffadmin(admin.ModelAdmin):
    list_display = ['name', 'pk', 'seller', 'upload_type', 'condition',
                    'shopping_mall', 'sold', 'price', 'is_active', 'temp_save', 'prod_thumb_img']
    list_editable = ('sold', 'is_active')
    fields = ('seller', 'crawl_name', 'crawl_price', 'product_url', 'name', 'price', 'category', 'color', 'size',
              'content', 'purchased_time', 'possible_upload', 'created_at'
              )

    def prod_thumb_img(self, obj):
        c_product = CrawlProduct.objects.get(obj.crawl_product_id)
        if c_product.thumbnail_url:
            return mark_safe('<img src="%s" width=120px "/>' % c_product.thumbnail_url)


class ProductUploadRequestStaffAdmin(admin.ModelAdmin):
    """
    구매내역을 첨부하여 업로드 요청했을 때 admin page 에서 관리하는 adminmodel 입니다.
    (TODO: 구매내역 첨부시 바로 수정할 수 있는 api 및 html 개발)
    """
    list_display = ['product', 'user', 'created_at', 'updated_at', 'is_done']
    list_editable = ['is_done']

    def user(self, obj):
        product = obj.product
        return product.seller


class FirstCategoryStaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'gender', 'is_active']

    def gender(self, obj):
        return obj.get_gender_display()


class SecondCategoryStaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'first_category', 'is_active']
    fields = ('first_category', 'name', 'is_active')


class SizeStaffAdmin(admin.ModelAdmin):
    list_display = ['category', 'size_name', 'get_size']

    def get_size(self, obj):
        if obj.size_max:
            return "[{}] {}-{}".format(obj.category.name, obj.size, obj.size_max)
        if obj.category.name == 'SHOES':
            return "[{}] {} (cm)".format(obj.category.name, obj.size)
        return "[{}] {}".format(obj.category.name, obj.size_name)


class ColorStaffAdmin(admin.ModelAdmin):
    list_display = ['color', 'image', 'is_active']

    def image(self, obj):
        if self.image:
            return mark_safe('<img src="%s" width=120px "/>' % self.image.url)


class ShoppingMallStaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'order', 'is_active']


class PurchasedReceiptStaffAdmin(admin.ModelAdmin):
    list_display = ['image', 'link', 'product', 'seller', 'possible_upload']

    def image(self, obj):
        return obj.image_url

    def link(self, obj):
        product = Product.objects.get(receipt=obj)
        return product.product_url

    def product(self, obj):
        product = Product.objects.get(receipt=obj)
        return product

    def seller(self, obj):
        product = Product.objects.get(receipt=obj)
        return product.seller

    def possible_upload(self, obj):
        product = Product.objects.get(receipt=obj)
        return product.possible_upload

    link.short_description = '상품 링크'


staff_panel.register(Product, ProductStaffadmin)
staff_panel.register(ProductUploadRequest, ProductUploadRequestStaffAdmin)
staff_panel.register(FirstCategory, FirstCategoryStaffAdmin)
staff_panel.register(SecondCategory, SecondCategoryStaffAdmin)
staff_panel.register(Size, SizeStaffAdmin)
staff_panel.register(Color, ColorStaffAdmin)
staff_panel.register(ShoppingMall, ShoppingMallStaffAdmin)
staff_panel.register(PurchasedReceipt, PurchasedReceiptStaffAdmin)
