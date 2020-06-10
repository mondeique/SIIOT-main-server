import uuid

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets, mixins, generics
from core.permissions import AnswerIsSellerPermission, IsQuestionWriterPermission
from products.models import Product
from products.reply.models import ProductQuestion, ProductAnswer
from products.reply.serializers import ProductQuestionCreateSerializer, ProductAnswerCreateSerializer, \
    ProductAnswerRetrieveSerializer, ProductQuestionRetrieveSerializer, ProductRepliesSerializer


class ProductQuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsQuestionWriterPermission, ]
    queryset = ProductQuestion.objects.all()
    serializer_class = ProductQuestionCreateSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        질문 하나 조회 api
        사용 안함. just for client test
        """
        instance = self.get_object()
        serializer = ProductQuestionRetrieveSerializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """사용 x"""
        return Response(None)

    def create(self, request, *args, **kwargs):
        """
        question 생성하는 api 입니다.
        api: POST api/v1/reply/question/
        data: {'product(id), 'text'}

        :return: {'id', 'profile', 'question', 'text', 'age'}
        * 생성시 만들어진 data 를 return 함으로써 클라에서 바로 보여줄 때 사용합니다.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        serializer = ProductQuestionRetrieveSerializer(question, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        api: PUT api/v1//reply/question/{id}
        * id: question id
        """

        # check permission : IsQuestionWriterPermission (작성자 본인인지 확인하는 permission) 아닐경우 403 forbidden
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()

        serializer = ProductQuestionRetrieveSerializer(question, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        # check permission : IsQuestionWriterPermission (작성자 본인인지 확인하는 permission) 아닐경우 403 forbidden
        question = self.get_object()
        if question.answers.exists(): # 답글이 달린 경우 :클라에서 edit_possible로 버튼을 활성화 하겠지만, 서버에서도 처리
            return Response({'Already answered'}, status=status.HTTP_403_FORBIDDEN)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductAnswerViewSet(viewsets.ModelViewSet):
    permission_classes = [AnswerIsSellerPermission, ]
    queryset = ProductAnswer.objects.all()
    serializer_class = ProductAnswerCreateSerializer

    def get_product(self):
        question = get_object_or_404(ProductQuestion, pk=self.question_id)
        self.product = question.product

    def retrieve(self, request, *args, **kwargs):
        """
        답글 하나 조회 api
        사용 안함. just for client test
        """
        instance = self.get_object()
        serializer = ProductAnswerRetrieveSerializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """사용 x"""
        return Response(None)

    def create(self, request, *args, **kwargs):
        """
        question 에 seller 가 답글을 생성하는 api 입니다.
        ProductSellerPermission 을 통해 판매자 본인인지를 확인합니다.
        api: POST api/v1/reply/answer/
        data: {'question(id)', 'text'}

        :return: {'id', 'question', 'text', 'age'}
        * 생성시 만들어진 data 를 return 함으로써 클라에서 바로 보여줄 때 사용합니다.
        """
        data = request.data.copy()
        self.question_id = data.get('question')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        answer = serializer.save()

        # check permission
        self.check_object_permissions(request, self.product)

        serializer = ProductAnswerRetrieveSerializer(answer, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        question 에 seller 가 답글을 수정하는 api 입니다.
        api: PUT api/v1/reply/answer/{id}/
        * id: answer id

        :return: create와 마찬가지
        """
        # check permission: ProductSellerPermission
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        answer = serializer.save()

        serializer = ProductAnswerRetrieveSerializer(answer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        answer 삭제하는 api 입니다.
        api: DELETE api/v1/reply/answer/{id}/

        return status: 403->forbidden(권한 없음), 404: not found(해당 id 존재x), 204: 삭제
        """
        return super(ProductAnswerViewSet, self).destroy(request, *args, **kwargs)


class ProductRepliesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [AllowAny, ]
    serializer_class = ProductRepliesSerializer
    queryset = ProductQuestion.objects.all()

    def list(self, request, *args, **kwargs):
        """
        replies 전체 조회하는 api 입니다.
        pagination이 구현되었습니다.
        api: GET api/v1/reply/replies/

        :return:
                * #pagination# 안의 results에 담김
                {'id', 'profile_img', 'product', 'text',
                'age', 'edit_possible',
                'answers':
                    [{'id', 'question', 'text', 'age'}, {} ..]
        """
        return super(ProductRepliesViewSet, self).list(request, *args, **kwargs)