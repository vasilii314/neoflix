from django.urls import path

from neoflix.views import MoviesView, MovieRatingView, MovieFavoriteView

urlpatterns = [
        path('home/', MoviesView.as_view(), name='movies-main'),
        path('account/ratings/<sid>/', MovieRatingView.as_view(), name='movie-rating'),
        path('account/favorites/<sid>/', MovieFavoriteView.as_view(), name='movie-favorite')
]
