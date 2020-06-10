import uuid

from django.db import transaction
from django.db.models import Case, When, IntegerField, Count
from django.http import Http404
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny

# Create your views here.
from core.permissions import ProductViewPermission
from crawler.models import CrawlProduct
from products.category.models import FirstCategory, SecondCategory, Size, Color
from products.category.serializers import FirstCategorySerializer, SecondCategorySerializer, SizeSerializer, \
    ColorSerializer
from products.models import Product, ProductImages, ProductUploadRequest, ProductViews
from products.serializers import ProductFirstSaveSerializer, ReceiptSaveSerializer, ProductSaveSerializer, \
    ProductImageSaveSerializer, ProductUploadDetailInfoSerializer, ProductTempUploadDetailInfoSerializer, \
    ProductRetrieveSerializer
from products.shopping_mall.models import ShoppingMall
from products.shopping_mall.serializers import ShoppingMallSerializer
from products.slack import slack_message
from products.supplymentary.serializers import ShoppingMallDemandSerializer
from products.utils import crawl_request, check_product_url


class ProductViewSet(viewsets.GenericViewSet,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin):
    permission_classes = [ProductViewPermission, ]
    queryset = Product.objects.all().select_related('seller', 'seller__profile', 'seller__delivery_policy')\
                              .select_related('receipt', 'category', 'purchased_time', 'color', 'size')

    """
    상품 업로드 및 조회에 관련된 ViewSet 입니다.
    유저가 상품 업로드 시 임시저장을 구현하기 위해 처음 저장정보(type, condition, shopping mall, link) 업로드시에만
    POST method 로 api를 구현하였고, 
    나머지 (ex: receipt 첨부, image 첨부, 가격 및 카테고리 등)의 경우 업데이트 개념으로 PUT method를 사용하였습니다.
    특히, receipt 와 image 첨부의 경우 다른 api로 구현한 상태입니다.
    """

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductFirstSaveSerializer
        elif self.action == 'receipt':
            return ReceiptSaveSerializer
        elif self.action == 'images':
            return ProductImageSaveSerializer
        elif self.action in ['update', 'complete', 'complete_with_receipt']:
            return ProductSaveSerializer
        elif self.action == 'temp_data':
            return ProductTempUploadDetailInfoSerializer
        elif self.action == 'retrieve':
            return ProductRetrieveSerializer
        else:
            return super(ProductViewSet, self).get_serializer_class()

    @action(methods=['post'], detail=False)
    def check_url(self, request, *args, **kwargs):

        """
        링크 입력 후 '확인' 버튼을 누를 때 호출되는 api 입니다.
        api : POST api/v1/product/check_url/

        data : "product_url"
        """
        data = request.data
        url = data.get('product_url')
        valid_url = check_product_url(url)

        if valid_url:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        상품 업로드 시 가장먼저 저장되는 정보(업로드 타입, 상태, 쇼핑몰, 링크)까지 저장하는 api 입니다.
        처음 호출하기 때문에 create를 활용하여 설정하였습니다.
        * 이 api 가 호출되는 시점에 crawling server에 요청을 보냅니다.
        * 특히 새로 등록할 때 호출되기 때문에 이전에 임시저장했던 상품은 임시저장 해제합니다.
        api : POST api/v1/product/

        data : "upload_type(int)", "condition(int)", "shopping_mall(int)", "product_url(str)"
        
        :return {"id",
                 "receipt_image_url(optional), <- 구매내역 첨부 후 상세정보 입력할 때만 data 존재
                 "crawl_data: {'thumbnail_image_url': ~~, "product_name":~~, "int_price":~~ }",
                 }
        """
        user = request.user
        data = request.data.copy()

        temp_products = self.get_queryset().filter(seller=user, temp_save=True)

        # temp data reset
        if temp_products.exists():
            for temp_product in temp_products:
                temp_product.temp_save = False
                temp_product.save()

        # save here
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        # crawl request
        product_url = data.get('product_url')
        if CrawlProduct.objects.filter(product_url=product_url).exists():
            crawl_product_id = CrawlProduct.objects.filter(product_url=product_url).last().id
        else:
            crawl_product_id = crawl_request(product_url)

        # product crawl id save
        product.crawl_product_id = crawl_product_id
        product.save()

        # 구매내역 인증 방식인 경우, 해당 api 호출 후 구매내역 첨부하는 페이지로..
        # 직접 입력인 경우 해당 api 호출 후 상세정보 입력 페이지지로
        product_info_serializer = ProductUploadDetailInfoSerializer(product)

        return Response(product_info_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['put'], detail=True)
    def receipt(self, request, *args, **kwargs):
        """
        구매내역 첨부시 사용하는 api 입니다.
        첨부 이후 상세정보 입력 페이지로 이동하기 때문에 필요한 정보들과 함께 return 합니다.
        api : PUT api/v1/product/{id}/receipt/

        data : "receipt_image_key"
        
        :return create return 과 동일
        """
        product = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = serializer.save()

        product.receipt = receipt
        product.save()

        product_info_serializer = ProductUploadDetailInfoSerializer(product)

        return Response(product_info_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['put'], detail=True)
    def images(self, request, *args, **kwargs):
        """
        상품 이미지 저장 시 사용하는 api 입니다. * 저장하는 (유저가 선택한) 사진의 uuid 만 주어야 합니다.
        api : PUT api/v1/product/{id}/images/

        data : "image_key(list)"
        """
        data = request.data.copy()
        product = self.get_object()
        image_key_list = data.get('image_key')

        if not image_key_list or not isinstance(image_key_list, list):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        bulk_create_list = []
        # image bulk create.. TODO : refac with serialzier
        for key in image_key_list:
            bulk_create_list.append(ProductImages(
                product=product,
                image_key=key
            ))
        ProductImages.objects.bulk_create(bulk_create_list)

        return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    def update(self, request, *args, **kwargs):
        """
        상품 업로드 과정에서 각각의 정보(사진제외)를 입력 할 때마다 호출되는(업데이트 되는) api 입니다.
        * 매번 호출하는게 문제가 없을까?
        ** product upload 흐름 :
            사진유형(사진,구매내역) 따로 저장, 나머지 data는 매번 update코드로 저장 | 상품 수정시에도 같은 플로우
        api : PUT api/v1/product/{id}/

        data : serializer 참고
        """
        data = request.data.copy()
        year = data.pop('purchased_year', None)
        month = data.pop('purchased_month', None)
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=data, partial=True)

        # purchased time 을 int 로 받기 위해 valid 이후 data 추가함. (TODO: better code!)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data.update({'purchased_year': year, 'purchased_month': month})
        serializer.update(obj, data)

        return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    @transaction.atomic
    @action(methods=['put'], detail=True)
    def complete(self, request, *args, **kwargs):
        """
        상품 업로드 완료시 호출되는 api 입니다.
        update 에 보냈던 데이터 형식과 동일하게 보내주어야 합니다(최종 저장)
        구매내역 없이 직접입력 하는경우 possible_upload = True, 구매내역 첨부한 경우 slack으로 알림을 보냅니다.
        최종저장시 임시저장 필드를 False로 바꾸어 조회되지 않도록 저장합니다.
        api : PUT api/v1/product/{id}/complete/

        data : update()에서 사용했던 데이터와 동일
        """
        data = request.data.copy()
        year = data.pop('purchased_year', None)
        month = data.pop('purchased_month', None)
        obj = self.get_object()

        serializer = self.get_serializer(obj, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        # purchased time 을 int 로 받기 위해 valid 이후 data 추가함. (TODO: better code!)
        if obj.receipt:
            # 구매내역이 있는 경우
            data = serializer.validated_data
            data.update({'purchased_year': year, 'purchased_month': month, 'possible_upload': True, 'temp_save': False})

            product = serializer.update(obj, data)

            upload_req = ProductUploadRequest.objects.create(product=product)
            left_count = ProductUploadRequest.objects.filter(is_done=False).count()
            slack_message("[업로드 요청] \n [id:{}] -상품명:{}, -신청자:{} || 남은개수 {} ({})".
                          format(upload_req.id, product.name, request.user, left_count,
                                 timezone.now().strftime('%y/%m/%d %H:%M')),
                          'upload_request')

            return Response(status=status.HTTP_206_PARTIAL_CONTENT)

        else:
            # 구매내역이 없는 경우
            data = serializer.validated_data
            data.update({'purchased_year': year, 'purchased_month': month,  'temp_save': False})
            serializer.update(obj, data)

            return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['get'], detail=False)
    def temp_data(self, request, *args, **kwargs):
        """
        임시저장한 상품정보를 조회할 때 사용하는 api 입니다.
        상품 업로드 과정에 전송했던 모든 데이터를 한번에 return 합니다.
        특히, 업로드시 처음 입력하는 upload_type, 구매내역 등과 같은 변수도 함께 return 하여 유저가 뒤로가기
        버튼을 눌렀을 때 클라에서 참고할 수 있도록 합니다. (TODO: 개발구현 논의필요)
        api : GET api/v1/product/temp_data/

        :return serializer 참고
        """
        user = request.user
        queryset = self.get_queryset().filter(seller=user, temp_save=True)
        if not queryset.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        temp_product = queryset.last()

        serializer = self.get_serializer(temp_product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def temp_save_cancel(self, request, *args, **kwargs):
        """
        이어서 작성 취소시 호출하는 api. 만약 해당 api를 호출하지 않고 유저가 처음부터 입력하다가 이탈하는 경우
        이전에 임시저장되었던 데이터가 존재하기 때문에 문제가 발생함.
        api: POST api/v1/product/temp_save_cancel/

        """
        user = request.user
        queryset = self.get_queryset().filter(seller=user, temp_save=True)
        if not queryset.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        temp_product = queryset.last()
        temp_product.temp_save = False
        temp_product.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        """
        상품 조회하는 api 입니다. 호출시마다 조회수가 증가합니다.
        api: GET api/v1/product/{id}/

        :return serializer 참고
        """
        product = self.get_object()
        views, _ = ProductViews.objects.get_or_create(product=product)
        views.count = views.count + 1
        views.save()

        return super(ProductViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        상품 list 조회하는 api 입니다.
        추가할 것) 판매자 상품인지 아닌지 등과 같은 부가정보 (기획필수)
        api: GET api/v1/product/
        """
        return super(ProductViewSet, self).list(request, *args, **kwargs)


class ShoppingMallViewSet(viewsets.GenericViewSet):
    queryset = ShoppingMall.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated, ]
    serializer_class = ShoppingMallSerializer

    def list(self, request, *args, **kwargs):
        """
        쇼핑몰 리스트 요청하는 api 입니다.
        api: GET ap1/v1/shopping_mall/
        """
        queryset = self.get_queryset().order_by('order')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    def searching(self, request, *args, **kwargs):
        """
        shopping mall 검색을 할 때 각 글자에 해당하는 쇼핑몰을 조회하는 api 입니다.
        api: POST api/v1/shopping_mall/searching/
        """
        keyword = request.data['keyword']
        if keyword:
            value = self.get_queryset()\
                    .filter(name__icontains=keyword) \
                    .order_by('id')[:20]
            serializer = self.get_serializer(value, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = self.get_queryset().order_by('order')
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def demand(self, request, *args, **kwargs):
        """
        쇼핑몰 추가 요청하는 api 입니다.
        api: POST api/v1/shopping_mall/demand/
        """
        serializer = ShoppingMallDemandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        demand = serializer.save()

        # slack message
        slack_message("[쇼핑몰 크롤링 요청] \n 쇼핑몰명:{}, -신청자:{}, 신청일 {}".
                      format(demand.shoppingmall_name, demand.user, timezone.now().strftime('%y/%m/%d %H:%M')),
                      'shopping_mall_demand')

        return Response(status=status.HTTP_201_CREATED)


class ProductCategoryViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        queryset = FirstCategory.objects.filter(is_active=True, gender=FirstCategory.WOMAN)
        if self.action == 'second_category':
            queryset = SecondCategory.objects.filter(is_active=True)
        elif self.action == 'size':
            queryset = Size.objects.all()
        elif self.action == 'color':
            queryset = Color.objects.filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        if self.action == 'first_category':
            return FirstCategorySerializer
        elif self.action == 'second_category':
            return SecondCategorySerializer
        elif self.action == 'size':
            return SizeSerializer
        elif self.action == 'color':
            return ColorSerializer
        else:
            return super(ProductCategoryViewSet, self).get_serializer_class()

    @action(methods=['get'], detail=False)
    def first_category(self, request, *args, **kwargs):
        """
        first_category 를 조회하는 api 입니다.
        api: GET api/v1/category/first_category/

        :return serialzier 참고
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=True)
    def second_category(self, request, *args, **kwargs):
        """
        second_category 를 조회하는 api 입니다.
        api: GET api/v1/category/{id}/second_category/
        *id 는 first category
        :return serialzier 참고
        """
        fc_pk = kwargs['pk']
        try:
            first_category = FirstCategory.objects.get(pk=fc_pk)
        except FirstCategory.DoesNotExist:
            raise Http404
        queryset = self.get_queryset().filter(first_category=first_category)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=True)
    def size(self, request, *args, **kwargs):
        """
        size 를 조회하는 api 입니다.
        api: GET api/v1/category/{id}/size/
        *id 는 first category
        :return serialzier 참고
        """
        fc_pk = kwargs['pk']
        try:
            first_category = FirstCategory.objects.get(pk=fc_pk)
        except FirstCategory.DoesNotExist:
            raise Http404
        queryset = self.get_queryset().filter(category=first_category)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def color(self, request, *args, **kwargs):
        """
        color 를 조회하는 api 입니다.
        api: GET api/v1/category/color/
        :return serialzier 참고
        """
        queryset = self.get_queryset().order_by('order')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class S3ImageUploadViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ]

    @action(methods=['get'], detail=False)
    def receipt_key(self, request):
        """
        구매내역 첨부 시 uuid를 발급받는 api 입니다. (TODO : presigned url)
        api: GET ap1/v1/s3/receipt_key/

        """
        ext = request.GET.get('ext', 'jpg')
        if ext not in ('jpg', 'mp3', 'mp4'):
            ext = 'jpg'
        key = uuid.uuid4()
        image_key = "%s.%s" % (key, ext)
        url = "https://{}.s3.amazonaws.com/".format('siiot-media-storage') # TODO: production s3
        content_type = "image/jpeg"
        data = {"url": url, "image_key": image_key, "content_type": content_type, "key": key}
        return Response(data)

    @action(methods=['post'], detail=False)
    def image_key_list(self, request):
        """
        이미지 첨부시 uuid list를 발급받는 api 입니다. (TODO : presigned url)
        api: POST api/v1/s3/image_key_list/
        data : {'count' : int}

        """
        data = request.data
        count = int(data['count'])
        temp_key_list = []
        for i in range(count):
            temp_key = self.fun_temp_key()
            temp_key_list.append(temp_key)
        return Response(temp_key_list)

    def fun_temp_key(self):
        ext = 'jpg'
        key = uuid.uuid4()
        image_key = "%s.%s" % (key, ext)
        url = "https://{}.s3.amazonaws.com/".format('siiot-media-storage') # TODO: production s3
        content_type = "image/jpeg"
        data = {"url": url, "image_key": image_key, "content_type": content_type, "key": key}
        return data
