import factory

from django.conf import settings


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for AUTH_USER_MODEL
    """

    class Meta:
        model = settings.AUTH_USER_MODEL
