# -*- encoding: utf-8 -*-
from django.contrib import admin
from django.utils import timezone

from .sites import superadmin_panel
from ajax_select import make_ajax_form


class ReadOnlyTabularInline(admin.TabularInline):
    extra = 0

    def __init__(self, *args, **kwargs):
        super(ReadOnlyTabularInline, self).__init__(*args, **kwargs)
        self.readonly_fields = self.fields

    class Media:
        css = {"all": ("admin/css/hide_admin_original.css",)}

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


class WriteOnlyTabularInline(admin.TabularInline):
    extra = 1

    class Media:
        css = {"all": ("admin/css/hide_admin_original.css",)}

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def create_filter_tag(display_name, key, value):
    return u'<a href="?%s=%s">%s</a>' % (key, value, display_name)


def toFriendlyDateTimeString(date_target):
    now = timezone.now()
    if date_target > now:
        return '몇 초전'
    delta = now - date_target
    if delta.days >= 365:
        return '%d년 전' % (delta.days // 365)
    elif delta.days >= 31:
        return '%d달 전' % (delta.days // 30.5)
    elif delta.days >= 7:
        return '%d주 전' % (delta.days // 7)
    elif delta.days >= 1:
        if delta.days == 1:
            return '하루 전'
        elif delta.days == 2:
            return '이틀 전'
        else:
            return '%d일 전' % (delta.days)
    elif delta.seconds >= 3600:        
        return '%d시간 전' % (delta.seconds // 3600)
    elif delta.seconds >= 60:        
        return '%d분 전' % (delta.seconds // 60)
    return '%d초 전' % (delta.seconds)


# superadmin을 위한 helper function
def superadmin_register(model, user_fields=None, **kwargs):
    class ObjectAdmin(admin.ModelAdmin):
        pass
    if user_fields is not None:
        for user_field in user_fields:
            ObjectAdmin.form = make_ajax_form(model, {user_field: 'user_channel'})
    for key in kwargs:
        setattr(ObjectAdmin, key, kwargs[key])
    if 'list_display' in kwargs:
        list_display = kwargs['list_display']
        for col in list_display:
            # supports '_xx' notation for list_display
            if col[0] == '_':
                obj_attr = col[1:]
                list_method = (
                    lambda self, obj, obj_attr=obj_attr: getattr(obj, obj_attr))
                list_method.short_description = obj_attr
                setattr(ObjectAdmin, col, list_method)
    superadmin_panel.register(model, ObjectAdmin)
