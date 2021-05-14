import graphene

from graphql_auth.schema import UserQuery, MeQuery
from apps.accounts.api.mutations import AuthMutation


class Query(UserQuery, MeQuery, graphene.ObjectType):
    """
    This class will inherit from multiple Queries as we begin to
    add more apps to our project
    """
    pass


class Mutation(AuthMutation, graphene.ObjectType):
    """
    This class will inherit from multiple Mutations as we begin to
    add more apps to our project
    """
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
