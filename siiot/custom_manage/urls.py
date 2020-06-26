from django.urls import path, include
from custom_manage.views import StaffManageTemplateView, ProductUploadManageTemplateView

urlpatterns = [
    path('manage/', StaffManageTemplateView.as_view(), name='home'),
    path('manage/upload_req/<int:pk>/', ProductUploadManageTemplateView.as_view(), name='upload_reqs'),
]

