from django import forms
from products.category.models import SecondCategory, Color, Size, FirstCategory
from products.models import ProductUploadRequest, Product


class UploadRequestForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'color', 'size']

    def __init__(self, *args, **kwargs):
        super(UploadRequestForm, self).__init__(*args, **kwargs)

    name = forms.CharField()
    category = forms.ModelChoiceField(queryset=SecondCategory.objects.filter(is_active=True))
    color = forms.ModelChoiceField(queryset=Color.objects.filter(is_active=True))
    size = forms.ModelChoiceField(queryset=Size.objects.filter())
