from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters, mixins
from rest_framework import permissions as rest_permission
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from reviews.models import Review, Title, Category, Genre
from users.models import User

from api import filter, permissions, serializers


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAdminOrAuthenticated]
    queryset = User.objects.all()
    lookup_field = 'username'


class TitleViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TitleListSerializer
    permission_classes = (permissions.IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filter.TitleFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.TitleListSerializer
        else:
            return serializers.TitleSerializer

    def get_queryset(self):
        return Title.objects.order_by('id')


class CreateListDeleteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    pass


class CategoryViewSet(CreateListDeleteViewSet):
    serializer_class = serializers.CategorySerializer
    permission_classes = (permissions.IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def get_queryset(self):
        return Category.objects.order_by('name')


class GenreViewSet(CreateListDeleteViewSet):
    serializer_class = serializers.GenreSerializer
    permission_classes = (permissions.IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def get_queryset(self):
        return Genre.objects.order_by('name')


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ReviewSerializer
    permission_classes = (
        rest_permission.IsAuthenticatedOrReadOnly,
        permissions.ReviewAndComment,
    )

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CommentSerializer
    permission_classes = (
        rest_permission.IsAuthenticatedOrReadOnly,
        permissions.ReviewAndComment,
    )

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id, title=title_id)
        return review.comments.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id, title=title_id)
        serializer.save(author=self.request.user, review=review)


class UserSignupView(CreateAPIView):
    model = get_user_model()
    permission_classes = [rest_permission.AllowAny]
    serializer_class = serializers.UserSignupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_200_OK, headers=headers
        )


class UserTokenView(CreateAPIView):
    model = get_user_model()
    permission_classes = [rest_permission.AllowAny]
    serializer_class = serializers.UserTokenSerializer
