from django.urls import path, include
from rest_framework.routers import SimpleRouter

from products.reply.views import ProductQuestionViewSet, ProductAnswerViewSet
from products.views import ProductViewSet, ShoppingMallViewSet, ProductCategoryViewSet, S3ImageUploadViewSet

router = SimpleRouter()
router.register('product', ProductViewSet, basename='product')
router.register('shopping_mall', ShoppingMallViewSet, basename='shopping_mall')
router.register('category', ProductCategoryViewSet, basename='category')
router.register('s3', S3ImageUploadViewSet, basename='s3')

urlpatterns = [
    path('', include(router.urls)),
    path('reply/', include('products.reply.urls'))
]

