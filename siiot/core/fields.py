import uuid

import os
import six
from django import forms
from django.db import models
from django.template.loader import render_to_string
from django.utils.deconstruct import deconstructible
from django.utils.safestring import mark_safe
from rest_framework import fields as rest_framework_fields
from . import S3_HOST

"""
Django model field
"""


def _resolve(key):
    # return '%s/resolve/?key=%s' % (FILESERVER_HOST, key)
    return '%s/%s.jpg' % (S3_HOST, key)


class URLResolvableUUID(uuid.UUID):
    @property
    def url(self):
        return _resolve(self)


class S3ImageKeyField(models.UUIDField):
    description = 'Fileserver image key (UUIDField)'

    # https://github.com/django/django/blob/2a7ce34600d0f879e93c9a5e02215948ed3bb6ac/django/db/models/fields/__init__.py
    """
    def to_python(self, value):
        if value and not isinstance(value, URLResolvableUUID):
            try:
                return URLResolvableUUID(value)
            except ValueError:
                raise exceptions.ValidationError(
                    self.error_messages['invalid'],
                    code='invalid',
                    params={'value': value},
                )
        return value
    """

    def from_db_value(self, value, expression, connection):
        if isinstance(value, uuid.UUID):
            return URLResolvableUUID(value.hex)
        return value


"""
Serializer field
"""


class URLResolvableUUIDField(rest_framework_fields.UUIDField):
    def to_internal_value(self, data):
        if not isinstance(data, URLResolvableUUID):
            try:
                if isinstance(data, six.integer_types):
                    return URLResolvableUUID(int=data)
                elif isinstance(data, six.string_types):
                    return URLResolvableUUID(hex=data)
                else:
                    self.fail('invalid', value=data)
            except (ValueError):
                self.fail('invalid', value=data)
        return data


"""
Form field
"""


# good reference code : https://github.com/crucialfelix/django-ajax-selects/blob/develop/ajax_select/fields.py
class S3ImageUploaderWidget(forms.widgets.TextInput):
    def _media(self):
        js = ('s3uploader/js/s3uploader.js',)
        css = {'all': ('s3uploader/css/s3uploader.css',)}
        return forms.Media(js=js, css=css)

    media = property(_media)

    def render(self, name, value, attrs=None):
        template = 's3uploader/s3uploader.html'
        context = {
            'name': name,
            'value': value,
        }
        return mark_safe(render_to_string(template, context))


class S3ImageUploaderField(forms.fields.CharField):
    widget = S3ImageUploaderWidget


# See: https://code.djangoproject.com/ticket/22999#no1
@deconstructible
class GiveRandomFileName(object):
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        filename = filename.split('.')
        extension = filename[-1]
        filename = '{}.{}'.format(filename[0] + '_' + str(uuid.uuid4().hex), extension)
        return os.path.join(self.path, filename)
