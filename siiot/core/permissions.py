from rest_framework.permissions import BasePermission


class AnswerIsSellerPermission(BasePermission):
    """
    답변시 판매자인지 확인하는 permission 입니다.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if bool(request.user and request.user.is_authenticated):
            user = request.user
            if obj.question.product.seller != user:
                return False
            return True
        return False


class IsQuestionWriterPermission(BasePermission):
    """
    question 작성자가 본인인지 확인하는 permission 입니다.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if (view.action in ['update', 'destroy', 'partial_update']
                and super(IsQuestionWriterPermission, self).has_object_permission(request, view, obj)):
            user = request.user
            if not user == obj.user:
                return False
            return True
        return super(IsQuestionWriterPermission, self).has_object_permission(request, view, obj)
