from abc import ABC

from neomodel import RelationshipManager
from rest_framework.exceptions import NotAuthenticated


class NodeSerializableMixin:

    @property
    def serialize_simple(self):
        return {k: v for k, v in self.__dict__.items() if not issubclass(v.__class__, RelationshipManager)}

    @property
    def serialize(self):
        return {k: v if not issubclass(v.__class__, RelationshipManager) else self.serialize_relationships(v) for
                k, v in self.__dict__.items()}


class RelationshipsSerializableMixin:

    def serialize_relationships(self, nodes: list[NodeSerializableMixin]):
        serialized_nodes = []
        for node in nodes:
            serialized_nodes.append(node.serialize_simple)
        return serialized_nodes


class IsAuthenticatedMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not request.user:
            raise NotAuthenticated('Invalid token')
