import datetime
import json

from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from neomodel import DoesNotExist, AttemptedCardinalityViolation
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.views import APIView

from neoflix.mixins import IsAuthenticatedMixin
from neoflix.models import MovieModel, UserModel


class MoviesView(IsAuthenticatedMixin, APIView):

    def get(self, request):
        sort = request.query_params.get('order', 'released')
        qs = MovieModel.nodes.order_by(sort).all()
        paginator = PageNumberPagination()
        res = paginator.paginate_queryset(qs, request)
        res = [] if not res else [movie.serialize for movie in res]
        return JsonResponse({'count': len(res), 'results': res})


class MovieRatingView(IsAuthenticatedMixin, APIView):
    def post(self, request, sid):
        try:
            movie = MovieModel.nodes.get(sid=sid)
        except DoesNotExist as e:
            raise ValidationError({'message': 'Movie not found'})
        try:
            rel = request.user.rated_movies.connect(movie, {'rating': request.data.get('rating', 5), 'timestamp': datetime.datetime.now()})
            movie.ratings.append(request.data.get('rating', 5))
            rel.save()
            return JsonResponse(movie.serialize)
        except AttemptedCardinalityViolation as e:
            raise ValidationError({'message': 'You already rated this movie'})


class MovieFavoriteView(IsAuthenticatedMixin, APIView):
    def post(self, request, sid):
        try:
            movie = MovieModel.nodes.get(sid=sid)
        except DoesNotExist as e:
            raise ValidationError({'message': 'Movie not found'})
        request.user.favorite_movies.connect(movie)
        return JsonResponse(request.user.serialize)


