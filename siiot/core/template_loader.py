# https://www.djangosnippets.org/snippets/1376/
# https://github.com/django/django/blob/1.8.4/django/template/loaders/filesystem.py
from os.path import dirname, join, abspath, isdir

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as FilesystemLoader


class AppLoader(FilesystemLoader):
    is_usable = True

    def _get_template_vars(self, template_name):
        app_name, template_name = template_name.split(":", 1)
        try:
            template_dir = abspath(join(apps.get_app_config(app_name).path, 'templates'))
        except ImproperlyConfigured:
            raise TemplateDoesNotExist(template_name)

        return template_name, template_dir

    def load_template_source(self, template_name, template_dirs=None):
        """
        Template loader that only serves templates from specific app's template directory.

        Works for template_names in format app_label:some/template/name.html
        """
        if ":" not in template_name:
            raise TemplateDoesNotExist()

        template_name, template_dir = self._get_template_vars(template_name)

        if not isdir(template_dir):
            raise TemplateDoesNotExist(template_name)

        return super(AppLoader, self).load_template_source(template_name, template_dirs=[template_dir])
