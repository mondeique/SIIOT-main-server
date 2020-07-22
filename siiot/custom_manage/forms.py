from django import forms
from products.category.models import SecondCategory, Color, Size, FirstCategory
from products.models import ProductUploadRequest, Product
from products.shopping_mall.models import ShoppingMall


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


class InitialProductUploadForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['seller', 'condition', 'shopping_mall', 'product_url']

    def __init__(self, *args, **kwargs):
        super(InitialProductUploadForm, self).__init__(*args, **kwargs)

    condition = forms.ChoiceField(choices=((1, '미개봉'), (2, '시험 착용'), (3, '한두번 착용')))
    shopping_mall = forms.ModelChoiceField(queryset=ShoppingMall.objects.filter(is_active=True))


class ProductImagesUploadForm(forms.Form):
    image = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))


class ProductInfoUploadForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'purchased_year', 'purchased_month', 'content', 'category', 'color', 'size', 'free_delivery']

    def __init__(self, *args, **kwargs):
        super(ProductInfoUploadForm, self).__init__(*args, **kwargs)

    purchased_year = forms.IntegerField()
    purchased_month = forms.IntegerField()
    category = forms.ModelChoiceField(queryset=SecondCategory.objects.filter(is_active=True))
    color = forms.ModelChoiceField(queryset=Color.objects.filter(is_active=True))
    size = forms.ModelChoiceField(queryset=Size.objects.all())
