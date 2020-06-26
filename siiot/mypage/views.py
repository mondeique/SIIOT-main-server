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
from mypage.models import Accounts
from products.category.models import FirstCategory, SecondCategory, Size, Color, Bank
from products.category.serializers import FirstCategorySerializer, SecondCategorySerializer, SizeSerializer, \
    ColorSerializer, BankListSerializer, AccountsSerializer
from products.models import Product, ProductImages, ProductUploadRequest, ProductViews, ProductCrawlFailedUploadRequest, \
    ProductLike
# ProductLike
from products.reply.serializers import ProductRepliesSerializer
from products.serializers import ProductFirstSaveSerializer, ReceiptSaveSerializer, ProductSaveSerializer, \
    ProductImageSaveSerializer, ProductUploadDetailInfoSerializer, ProductTempUploadDetailInfoSerializer, \
    ProductRetrieveSerializer,  ProductMainSerializer #LikeSerializer
from products.shopping_mall.models import ShoppingMall
from products.shopping_mall.serializers import ShoppingMallSerializer
from products.slack import slack_message
from products.supplymentary.serializers import ShoppingMallDemandSerializer
from products.utils import crawl_request, check_product_url
from core.pagination import SiiotPagination


class AccountsViewSet(viewsets.ModelViewSet):
    queryset = Accounts
    permission_classes = [IsAuthenticated, ]
    serializer_class = AccountsSerializer

    def create(self, request, *args, **kwargs):
        """
        Accounts create api
        api: POST api/v1/accounts/

        data = {'bank" :int(bank id), 'bank_accounts': str, 'accounts_holder': str}
        """
        return super(AccountsViewSet, self).create(request, *args, **kwargs)

    @action(methods=['get'], detail=False)
    def bank_list(self, request, *args, **kwargs):
        qs = Bank.objects.filter(is_active=True)
        serializer = BankListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
