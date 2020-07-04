from django.conf import settings
from django.db import models
from products.models import Product


class ProductQuestion(models.Model):
    product = models.ForeignKey(Product, related_name='questions', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="product_questions", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = '상품 관련 질문'
        verbose_name_plural = '상품 관련 질문'

    def __str__(self):
        return '{}] {}'.format(self.id, self.product.name)


class ProductAnswer(models.Model):
    question = models.ForeignKey(ProductQuestion, related_name='answers', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='product_answers', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = '상품 관련 답변'
        verbose_name_plural = '상품 관련 답변'

    def __str__(self):
        return '{}] {}| Q_id:{}'.format(self.id, self.question.product.name, self.question.id)
