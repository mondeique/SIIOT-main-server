from django.urls import path, include
from rest_framework.routers import SimpleRouter

from products.reply.views import ProductQuestionViewSet, ProductAnswerViewSet, ProductRepliesViewSet
from products.views import ProductViewSet, ShoppingMallViewSet, ProductCategoryViewSet, S3ImageUploadViewSet

router = SimpleRouter()
router.register('question', ProductQuestionViewSet, basename='question')
router.register('answer', ProductAnswerViewSet, basename='answer')
router.register('replies', ProductRepliesViewSet, basename='reply')

urlpatterns = [
    path('', include(router.urls)),
]

