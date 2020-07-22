from django.urls import path, include
from custom_manage.views import StaffManageTemplateView, ProductUploadManageTemplateView, \
    ProductInitialUploadTemplateView, ProductImagesUploadTemplateView, ProductInfoUploadTemplateView

urlpatterns = [
    path('manage/', StaffManageTemplateView.as_view(), name='home'),
    path('manage/product/', ProductInitialUploadTemplateView.as_view(), name='product_initial_upload'),
    path('manage/product-images/<int:pk>/', ProductImagesUploadTemplateView.as_view(), name='product_images_upload'),
    path('manage/product-info/<int:pk>/', ProductInfoUploadTemplateView.as_view(), name='product_info_upload'),
]

