from django.db import models

# Create your models here.
from neomodel import StructuredNode, UniqueIdProperty, StringProperty, IntegerProperty, RelationshipTo, \
    RelationshipFrom, RelationshipDefinition, ZeroOrMore, RelationshipManager, One, ArrayProperty

from neoflix.mixins import NodeSerializableMixin, RelationshipsSerializableMixin
from neoflix.relationships import ActedInRel, RatedRel


class MovieModel(StructuredNode, NodeSerializableMixin, RelationshipsSerializableMixin):
    __label__ = 'Movie'
    sid = UniqueIdProperty()
    title = StringProperty()
    tagline = StringProperty()
    released = IntegerProperty()
    actors = RelationshipFrom('PersonModel', rel_type='ACTED_IN', model=ActedInRel)
    directors = RelationshipFrom('PersonModel', rel_type='DIRECTED')
    writers = RelationshipFrom('PersonModel', rel_type='WROTE')
    producers = RelationshipFrom('PersonModel', rel_type='PRODUCED')
    users_rated = RelationshipFrom('UserModel', rel_type='RATED', model=RatedRel)
    ratings = ArrayProperty(default=[])


class PersonModel(StructuredNode, NodeSerializableMixin, RelationshipsSerializableMixin):
    __label__ = 'Person'
    sid = UniqueIdProperty()
    name = StringProperty()
    born = IntegerProperty(default=0)

    movies_acted = RelationshipTo(MovieModel, rel_type='ACTED_IN', model=ActedInRel)
    movies_directed = RelationshipTo(MovieModel, rel_type='DIRECTED')
    movies_written = RelationshipTo(MovieModel, rel_type='WROTE')
    movies_produced = RelationshipTo(MovieModel, rel_type='PRODUCED')


class UserModel(StructuredNode, NodeSerializableMixin, RelationshipsSerializableMixin):
    __label__ = 'User'
    sid = UniqueIdProperty()
    name = StringProperty()
    email = StringProperty(unique_index=True)
    rated_movies = RelationshipTo(MovieModel, rel_type='RATED', model=RatedRel, cardinality=One)
    favorite_movies = RelationshipTo(MovieModel, rel_type='HAS_FAVORITE')
