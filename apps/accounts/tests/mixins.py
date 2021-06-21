from faker import Faker

from .factories import UserFactory


class AccountsMixin(object):
    """
    A collection of methods for creating test data for accounts app.
    """

    def __init__(self, *args, **kwargs):
        self.fake = Faker()
        super(AccountsMixin, self).__init__(*args, **kwargs)

    def create_user(self, **kwargs):

        if "email" not in kwargs:
            kwargs.update({"email": self.fake.email()})

        return UserFactory(**kwargs)
