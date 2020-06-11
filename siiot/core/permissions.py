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
                and bool(request.user and request.user.is_authenticated)):
            user = request.user
            if not user == obj.user:
                return False
            return True
        return bool(request.user and request.user.is_authenticated)


class ProductViewPermission(BasePermission):
    """
    ProductViewSet의 Permission을 위해 만들었습니다.
    create, update, images 등은 IsAuthenticated / retrieve, list 등은 AllowAny
    """
    def has_permission(self, request, view):
        if view.action in ['retrieve', 'list', 'replies']:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve', 'list', 'replies']:
            return True
        return bool(request.user and request.user.is_authenticated)
