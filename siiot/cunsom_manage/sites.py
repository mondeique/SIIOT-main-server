from ajax_select import make_ajax_form
from django import forms
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site
from django.utils.text import capfirst


class StaffLoginForm(AuthenticationForm):
    """
    login method 에서 USERNAME_FIELD 대신 Email 을 사용하도록 필요한 부분을 override 했습니다.
    """
    username = forms.EmailField(
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': ''}),
    )

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

        # Set the label for the "username" field.
        UserModel = get_user_model()
        self.username_field = UserModel._meta.get_field('email')
        if self.fields['username'].label is None:
            self.fields['username'].label = capfirst(self.username_field.verbose_name)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = get_user_model().objects.get(email=username)

            authenticate = check_password(password, user.password)
            if authenticate:
                self.user_cache = user
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            else:
                setattr(self.user_cache, 'backend', 'django.contrib.auth.backends.ModelBackend')
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


# https://github.com/barszczmm/django-wpadmin/blob/d4183e2fbce03539fe47d46be9c829192e97ebcb/test_project/test_project/admin.py
class SuperAdminSite(AdminSite):
    login_form = StaffLoginForm

    def has_permission(self, request):
        """
        Allow only superusers.
        """
        return request.user.is_active and request.user.is_superuser


class StaffSite(AdminSite):
    login_form = StaffLoginForm

    def has_permission(self, request):
        """
        Allow only staffs.
        """
        return request.user.is_active and request.user.is_staff


superadmin_panel = SuperAdminSite(name='superadmin')
staff_panel = StaffSite(name='staff')


# Admin for Django default models

# https://github.com/django/django/blob/53ccffdb8c8e47a4d4304df453d8c79a9be295ab/django/contrib/sites/admin.py
superadmin_panel.register(Site, SiteAdmin)


# https://github.com/django/django/blob/53ccffdb8c8e47a4d4304df453d8c79a9be295ab/django/contrib/auth/admin.py
superadmin_panel.register(Group, GroupAdmin)
