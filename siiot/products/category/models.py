from django.db import models


class FirstCategory(models.Model):
    """
    대분류 모델입니다.
    """
    WOMAN = 1
    MAN = 2
    UNISEX = 3
    GENDER = (
        (WOMAN, 1),
        (MAN, 2),
        (UNISEX, 3)
    )
    gender = models.IntegerField(choices=GENDER, default=1)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "[{}]{}".format(self.gender, self.name)


class SecondCategory(models.Model):
    """
    소분류 모델입니다.
    """
    name = models.CharField(max_length=100)
    first_category = models.ForeignKey('FirstCategory', on_delete=models.CASCADE, related_name='second_categories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "[{}]_{}".format(self.first_category, self.name)


class MixCategory(models.Model):
    """
    Product 가 참조하는 category 모델입니다. 카테고리 조합마다 하나씩 생성되어 같은 category 조합을 참고합니다.
    """
    first_category = models.ForeignKey(FirstCategory, on_delete=models.CASCADE, related_name="mix_first_categories")
    second_category = models.ForeignKey(SecondCategory, on_delete=models.CASCADE, related_name="mix_second_categories")


class Size(models.Model):
    category = models.ForeignKey('FirstCategory', null=True, on_delete=models.CASCADE, related_name='size')
    size_name = models.CharField(max_length=20, help_text="L, M 등과 같은 분류")
    size = models.PositiveIntegerField(null=True, blank=True,
                                       help_text='기본 size (ex: 66, 신발인경우 245 등), 범위가 있다면 최소 사이즈 (ex: 24~)')
    size_max = models.PositiveIntegerField(null=True, blank=True, help_text='사이즈 범위가 있는 경우 최대 사이즈 (ex: ~26')

    def __str__(self):
        if self.size_max:
            return "[{}] {}-{}".format(self.category.name, self.size, self.size_max)
        if self.category.name == 'SHOES':
            return "[{}] {} (cm)".format(self.category.name, self.size)
        return "[{}] {}".format(self.category.name, self.size)


def img_directory_path_profile(instance, filename):
    return 'color/{}/{}'.format(instance.color, filename)


class Color(models.Model):
    color = models.CharField(max_length=20)
    image = models.ImageField(null=True, blank=True, upload_to=img_directory_path_profile)
    order = models.PositiveIntegerField(unique=True, help_text="client에서 보여주는 순서")
    is_active = models.BooleanField(default=True)