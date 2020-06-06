import requests
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated

# Create your views here.
from products.models import Product, ProductImages, ProductUploadRequest
from products.serializers import ProductFirstSaveSerializer, ReceiptSaveSerializer, ProductSaveSerializer, \
    ProductImageSaveSerializer, ProductUploadDetailInfoSerializer
from products.slack import slack_message
from products.utils import crawl_request


class ProductViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    permission_classes = [IsAuthenticated, ]
    queryset = Product.objects.all()

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
        elif self.action in ['update', ' complete']:
            return ProductSaveSerializer
        else:
            return super(ProductViewSet, self).get_serializer_class()

    @action(methods=['post'], detail=False)
    def check_url(self, request, *args, **kwargs):
        """
        링크 입력 후 '확인' 버튼을 누를 때 호출되는 api 입니다.

        data : "url"
        """
        data = request.data
        url = data.get('url')
        response = requests.post(url)
        if response.status_code == 200:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        """
        상품 업로드 시 가장먼저 저장되는 정보(업로드 타입, 상태, 쇼핑몰, 링크)까지 저장하는 api 입니다.
        처음 호출하기 때문에 create를 활용하여 설정하였습니다.
        * 이 api 가 호출되는 시점에 crawling server에 요청을 보냅니다. (TODO)
        * 특히 새로 등록할 때 호출되기 때문에 이전에 임시저장했던 상품은 임시저장 해제합니다.
        api : POST api/v1/product

        data : "upload_type(int)", "condition(int)", "shopping_mall(int)", "product_url(str)"
        
        :return {"id", "crawl_thumbnail_image_url", 
                 "receipt_image_url(optional), <- 구매내역 첨부 후 상세정보 입력할 때만 data 존재
                 "crawl_product_name",
                 "crawl_product_price"}
        """
        user = request.user
        data = request.data.copy()

        temp_products = Product.objects.filter(seller=user, temp_save=True)

        # save here
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        # temp save reset
        if temp_products.exists():
            for temp_product in temp_products:
                temp_product.temp_save = False
                temp_product.save()

        # crawl request
        product_url = data.get('product_url')
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
        api : PUT api/v1/product/{id}/receipt

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
        api : PUT api/v1/product/{id}/images

        data : "image_key(list)"
        """
        data = request.data.copy()
        product = self.get_object()
        image_key_list = data.get('image_key')

        if not image_key_list or isinstance(image_key_list, list):
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
        api : PUT api/v1/product/{id}/

        data : serializer 참고
        """
        # obj = self.get_object()
        # serializer = self.get_serializer(obj, data=request.data, partial=True)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        # return Response(status=status.HTTP_206_PARTIAL_CONTENT)

        return super(ProductViewSet, self).partial_update(request, *args, **kwargs)

    @action(methods=['put'], detail=True)
    def complete(self, request, *args, **kwargs):
        """
        직접 업로드 시 상품 업로드를 완료했을 때 호출되는 api 입니다.
        update 에 보냈던 데이터 형식과 동일하게 보내주어야 합니다(최종 저장)
        api : PUT api/v1/product/{id}/complete

        data : update()에서 사용했던 데이터와 동일
        """
        data = request.data.copy()
        data['possible_upload'] = True
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['put'], detail=True)
    def complete_with_receipt(self, request, *args, **kwargs):
        """
        구매내역 첨부로 업로드 완성시 호출되는 api 입니다.
        update 와 동일하게 저장하며 추가적으로 slack에 연동하여 알림을 줍니다.
        api : PUT api/v1/product/{id}/complete_with_receipt

        data : update()에서 사용했던 데이터와 동일
        """
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        upload_req = ProductUploadRequest.objects.create(product=product)
        left_count = ProductUploadRequest.objects.filter(is_done=False).count()

        # slack message
        slack_message("[업로드 요청] [id:{}] -상품명:{}, -신청자:{} || 남은개수 {}".
                      format(upload_req.id, product.name, request.user, left_count))

        return Response(status=status.HTTP_206_PARTIAL_CONTENT)