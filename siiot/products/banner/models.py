from django.db import models


def banner_directory_path_profile(instance, filename):
    return 'banner/main/{}_{}'.format(instance.id, filename)


class MainBanner(models.Model):
    image = models.ImageField(upload_to=banner_directory_path_profile)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    order = models.IntegerField(unique=True)

    @property
    def image_url(self):
        return self.image.url
