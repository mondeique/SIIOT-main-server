import requests
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import TemplateView, DetailView
import time
from core.permissions import StaffPermission
from crawler.models import CrawlProduct
from custom_manage.forms import UploadRequestForm, InitialProductUploadForm, ProductImagesUploadForm, \
    ProductInfoUploadForm
from custom_manage.utils import upload_s3
from products.models import ProductUploadRequest, Product, ProductImages, ProductStatus, ProdThumbnail
from products.slack import slack_message
from products.supplymentary.models import PurchasedTime
from products.utils import crawl_request, image_key_list


class StaffManageTemplateView(TemplateView):
    """
    Staff Management Page
    """
    template_name = 'manage.html'
    permission_classes = [StaffPermission, ]

    def get_context_data(self,**kwargs):
        context = super(StaffManageTemplateView, self).get_context_data()
        context['user'] = self.request.user
        # context['crawl_fails'] = ProductCrawlFailedUploadRequest.objects.filter(is_done=False)
        return context


class ProductUploadManageTemplateView(DetailView):
    template_name = 'upload_request/work_page.html'
    permission_classes = [StaffPermission, ]
    queryset = ProductUploadRequest.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ProductUploadManageTemplateView, self).get_context_data()
        self.get_product()
        context['product'] = self.product
        context['next_id'] = self.has_next()
        context['prev_id'] = self.has_prev()
        form = UploadRequestForm
        context['form'] = form
        return context

    def has_prev(self):
        pk = self.kwargs['pk']
        prev_obj = self.get_queryset().filter(pk__lt=pk).order_by('pk').last()
        print(prev_obj)
        return prev_obj

    def has_next(self):
        pk = self.kwargs['pk']
        next_obj = self.get_queryset().filter(pk__gt=pk).order_by('pk').first()
        return next_obj

    def get_product(self):
        self.product = self.get_object().product

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = UploadRequestForm(instance=self.get_object().product, data=request.POST)
        pk = kwargs['pk']
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            obj = self.get_object()
            obj.is_done = True
            obj.save()
            if self.has_next():
                pk = self.has_next().id
            return redirect('upload_reqs', pk)
        return redirect('upload_reqs', pk)


class ProductInitialUploadTemplateView(TemplateView):
    template_name = 'upload_request/product_upload1.html'
    permission_classes = [StaffPermission, ]

    def get_context_data(self, **kwargs):
        context = super(ProductInitialUploadTemplateView, self).get_context_data()
        form = InitialProductUploadForm
        context['form'] = form
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data = request.POST

        user = request.user

        temp_products = Product.objects.filter(seller=user, temp_save=True)

        # temp data reset
        if temp_products.exists():
            for temp_product in temp_products:
                temp_product.delete()  # temp saved data delete
        form = InitialProductUploadForm(data=data)

        # Valid
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            pk = product.id
            product_url = product.product_url

            if CrawlProduct.objects.filter(product_url=product_url).exists() and \
                    CrawlProduct.objects.filter(product_url=product_url).last().detail_images.exists():
                crawl_product_id = CrawlProduct.objects.filter(product_url=product_url).last().id
            else:
                start = time.time()
                sucess, id = crawl_request(product_url)
                end = time.time() - start
                if end > 5:  # 5초 이상 걸린 경우 slack noti
                    slack_message("[최소정보 크롤링 5초이상 지연] \n 걸린시간 {}s, 요청 url: {}".
                                  format(end, product_url), 'crawl_error_upload')
                elif not id:
                    slack_message("[최소정보 크롤링 실패ㅠ] \n 걸린시간 {}s, 요청 url: {}".
                                  format(end, product_url), 'crawl_error_upload')
                else:
                    slack_message("[최소정보 크롤링 성공] \n 걸린시간 {}s, 요청 url: {}".
                                  format(end, product_url), 'crawl_error_upload')
                if sucess:
                    crawl_product_id = id
                else:
                    # crawling 실패했을 경우 또는 서버 에러
                    crawl_product_id = None
                print(time.time() - start)
            # product crawl id save
            product.crawl_product_id = crawl_product_id
            product.save()

            return redirect('product_images_upload', pk)



class ProductImagesUploadTemplateView(DetailView):
    template_name = 'upload_request/product_upload2.html'
    permission_classes = [StaffPermission, ]
    queryset = Product.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ProductImagesUploadTemplateView, self).get_context_data()
        formset = ProductImagesUploadForm
        context['formset'] = formset
        context['product'] = self.get_object()
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        product = self.get_object()

        if product.temp_save and product.images.last():
            product.images.all().delete()
            product.prodthumbnail.delete()

        files = request.FILES.getlist('image')
        print(files)
        count = len(files)
        whole_key_list = image_key_list(count)

        _image_key_list = []
        _key_list = []
        for data in whole_key_list:
            image_key = data['image_key']
            key = data['key']
            _image_key_list.append(image_key)
            _key_list.append(key)

        image_save_list = []
        for i, f in enumerate(files):

            upload_s3(f, _image_key_list[i])

            image_save_list.append(ProductImages(
                product=product,
                image_key=_key_list[i]
            ))

        ProductImages.objects.bulk_create(image_save_list)
        # Thumbnail image 따로 저장
        ProdThumbnail.objects.create(product=product)
        pk = kwargs['pk']
        return redirect('product_info_upload', pk)


class ProductInfoUploadTemplateView(DetailView):
    template_name = 'upload_request/product_upload3.html'
    permission_classes = [StaffPermission, ]
    queryset = Product.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ProductInfoUploadTemplateView, self).get_context_data()
        form = ProductInfoUploadForm
        product = self.get_object()
        context['form'] = form
        context['product'] = product

        if product.crawl_product_id:
            crawl_obj = CrawlProduct.objects.get(id=product.crawl_product_id)
            crawl_price = crawl_obj.int_price
            crawl_name = crawl_obj.product_name
        else:
            crawl_name = '실패'
            crawl_price = '실패'

        context['crawl_name'] = crawl_name
        context['crawl_price'] = crawl_price
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        product = self.get_object()

        form = ProductInfoUploadForm(instance=product, data=request.POST)

        data = request.POST
        data._mutable = True
        year = data.get('purchased_year', None)
        month = data.get('purchased_month', None)

        if year and month:
            time, _ = PurchasedTime.objects.get_or_create(year=int(year), month=int(month))
            product.purchased_time = time
            product.save()

        if form.is_valid():
            product = form.save(commit=False)
            product.temp_save = False
            product.possible_upload = True
            product.save()

            # status save
            ProductStatus.objects.create(product=product)

            return redirect('home')