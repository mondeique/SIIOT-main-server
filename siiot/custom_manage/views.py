from django.db import transaction
from django.shortcuts import redirect
from django.views.generic import TemplateView, DetailView

from core.permissions import StaffPermission
from custom_manage.forms import UploadRequestForm
from products.models import ProductUploadRequest, ProductCrawlFailedUploadRequest


class StaffManageTemplateView(TemplateView):
    """
    Staff Management Page
    """
    template_name = 'manage.html'
    permission_classes = [StaffPermission, ]

    def get_context_data(self,**kwargs):
        context = super(StaffManageTemplateView, self).get_context_data()
        context['upload_reqs'] = ProductUploadRequest.objects.filter(is_done=False)
        context['crawl_fails'] = ProductCrawlFailedUploadRequest.objects.filter(is_done=False)
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
