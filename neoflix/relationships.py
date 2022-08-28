from neomodel import StructuredRel, ArrayProperty, IntegerProperty, DateTimeProperty


class ActedInRel(StructuredRel):
    roles = ArrayProperty()


class RatedRel(StructuredRel):
    rating = IntegerProperty()
    timestamp = DateTimeProperty()

