import json

from django.contrib.auth import get_user_model
from django.core import mail
from django.http import HttpResponse
from graphene_django.utils.testing import GraphQLTestCase
from graphql_auth.constants import TokenAction
from graphql_auth.utils import get_token
from graphql_jwt.shortcuts import get_token as get_auth_token

from apps.accounts.mailer import AccountsMailer
from sharky.schema import schema

from .mixins import AccountsMixin

User = get_user_model()


class AuthTests(AccountsMixin, GraphQLTestCase):
    """
    Test cases for authentication.
    """

    GRAPHQL_SCHEMA = schema

    def test_register_mutation(self):
        email = self.fake.email()
        password = self.fake.password()

        response = self.query(
            """
            mutation registerAccount($email: String!,
                                     $first_name: String!,
                                     $last_name: String!,
                                     $phone: String!,
                                     $password1: String!,
                                     $password2: String!) {
                register(email: $email,
                         firstName: $first_name,
                         lastName: $last_name,
                         phone: $phone,
                         password1: $password1,
                         password2: $password2) {
                    success
                    errors
                }
            }
            """,
            op_name="registerAccount",
            variables={
                "email": email,
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "phone": self.fake.phone_number(),
                "password1": password,
                "password2": password,
            },
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content["data"]["register"]["success"])

        user = User.objects.get(email=email)
        self.assertFalse(user.status.verified)

        token = get_token(user, TokenAction.ACTIVATION)

        response = self.query(
            """
            mutation activateAccount($token: String!) {
                verifyAccount(token: $token) {
                    success
                    errors
                    accessToken
                    refreshToken
                }
            }
            """,
            op_name="activateAccount",
            variables={"token": token},
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertTrue(content["data"]["verifyAccount"]["success"])
        user = User.objects.get(email=email)
        self.assertTrue(user.status.verified)

        # Test access token and refresh token after verify
        self.assertIsNotNone(content["data"]["verifyAccount"]["accessToken"])
        self.assertIsNotNone(content["data"]["verifyAccount"]["refreshToken"])

        # Test authenticated access using new access token
        access_token = content["data"]["verifyAccount"]["accessToken"]
        response = self.query(
            """
            query {
                me {
                    id
                    email
                }
            }
            """,
            headers={"HTTP_AUTHORIZATION": f"JWT {access_token}"},
        )
        self.assertResponseNoErrors(response)

    def test_register_existing_email_verified_user(self):
        email = self.fake.email()
        password = self.fake.password()

        # create an existing user
        user = self.create_user(email=email)
        status = user.status
        status.verified = True
        status.save(update_fields=["verified"])

        response = self.query(
            """
            mutation registerAccount($email: String!,
                                    $first_name: String!,
                                    $last_name: String!,
                                    $phone: String!,
                                    $password1: String!,
                                    $password2: String!) {
                register(email: $email,
                        firstName: $first_name,
                        lastName: $last_name,
                        phone: $phone,
                        password1: $password1,
                        password2: $password2) {
                    success
                    errors
                }
            }
            """,
            op_name="registerAccount",
            variables={
                "email": email,
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "phone": self.fake.phone_number()[:16],
                "password1": password,
                "password2": password,
            },
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content["data"]["register"]["success"])

        # Test that the right email has been sent
        mailer = AccountsMailer()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, mailer.subjects["existing_email"])

    def test_register_existing_email_unverified_user(self):
        email = self.fake.email()
        password = self.fake.password()

        # create an existing user
        self.create_user(email=email)

        response = self.query(
            """
            mutation registerAccount($email: String!,
                                    $first_name: String!,
                                    $last_name: String!,
                                    $phone: String!,
                                    $password1: String!,
                                    $password2: String!) {
                register(email: $email,
                        firstName: $first_name,
                        lastName: $last_name,
                        phone: $phone,
                        password1: $password1,
                        password2: $password2) {
                    success
                    errors
                }
            }
            """,
            op_name="registerAccount",
            variables={
                "email": email,
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "phone": self.fake.phone_number()[:16],
                "password1": password,
                "password2": password,
            },
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content["data"]["register"]["success"])

        # Test that the right email has been sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("activate", mail.outbox[0].subject.lower())

    def test_register_mutation_incorrect_password(self):
        email = self.fake.email()
        password1 = self.fake.password()
        password2 = self.fake.password()

        response = self.query(
            """
            mutation registerAccount($email: String!,
                                    $first_name: String!,
                                    $last_name: String!,
                                    $phone: String!,
                                    $password1: String!,
                                    $password2: String!) {
                register(email: $email,
                        firstName: $first_name,
                        lastName: $last_name,
                        phone: $phone,
                        password1: $password1,
                        password2: $password2) {
                    success
                    errors
                }
            }
            """,
            op_name="registerAccount",
            variables={
                "email": email,
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "phone": self.fake.phone_number(),
                "password1": password1,
                "password2": password2,
            },
        )

        self.assertResponseHasErrors(response)
        content = json.loads(response.content)

        self.assertIsNotNone(content["data"]["register"]["errors"])
        self.assertFalse(content["data"]["register"]["success"])

    def test_register_mutation_invalid_email_format(self):
        username = self.fake.profile(fields=["username"])["username"]
        password = self.fake.password()

        response = self.query(
            """
            mutation registerAccount($email: String!,
                                    $first_name: String!,
                                    $last_name: String!,
                                    $phone: String!,
                                    $password1: String!,
                                    $password2: String!) {
                register(email: $email,
                        firstName: $first_name,
                        lastName: $last_name,
                        phone: $phone,
                        password1: $password1,
                        password2: $password2) {
                    success
                    errors
                }
            }
            """,
            op_name="registerAccount",
            variables={
                "email": username,
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "phone": self.fake.phone_number(),
                "password1": password,
                "password2": password,
            },
        )

        self.assertResponseHasErrors(response)
        content = json.loads(response.content)

        self.assertIsNotNone(content["data"]["register"]["errors"])
        self.assertFalse(content["data"]["register"]["success"])

    def test_login_mutation_using_email(self):
        email = self.fake.email()
        password = self.fake.password()
        user = self.create_user(email=email)
        user.set_password(password)
        user.save()
        response = self.query(
            """
            mutation userLogin($email: String!, $password: String!) {
                tokenAuth(email: $email, password: $password) {
                    token
                    success
                    user {
                        email
                    }
                    errors
                }
            }
            """,
            op_name="userLogin",
            variables={
                "email": email,
                "password": password,
            },
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content["data"]["tokenAuth"]["success"])
        self.assertEqual(content["data"]["tokenAuth"]["user"]["email"], user.email)
        self.assertIsNotNone(content["data"]["tokenAuth"]["token"])

    def test_login_mutation_incorrect_password(self):
        email = self.fake.email()
        password = self.fake.password()
        incorrect_password = self.fake.password()

        user = self.create_user(email=email)
        user.set_password(password)
        user.save()

        response = self.query(
            """
            mutation loginAccount($email: String!, $password: String!) {
                tokenAuth(email: $email, password: $password) {
                    token
                    success
                    user {
                        email
                    }
                    errors
                }
            }
            """,
            op_name="loginAccount",
            variables={
                "email": email,
                "password": incorrect_password,
            },
        )

        self.assertResponseHasErrors(response)
        content = json.loads(response.content)

        self.assertIsNotNone(content["data"]["tokenAuth"]["errors"])
        self.assertFalse(content["data"]["tokenAuth"]["success"])

    def test_forgot_password_and_password_reset_mutations(self):
        email = self.fake.email()
        user = self.create_user(email=email)

        # verified users will receive password reset token while
        # unverified users will receive email activation token.
        status = user.status
        status.verified = True
        status.save(update_fields=["verified"])

        response = self.query(
            """
            mutation forgotPassword($email: String!) {
                sendPasswordResetEmail(email: $email) {
                    success
                    errors
                }
            }
            """,
            op_name="forgotPassword",
            variables={"email": email},
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content["data"]["sendPasswordResetEmail"]["success"])

        token = get_token(user, TokenAction.PASSWORD_RESET)
        password = self.fake.password()

        response = self.query(
            """
            mutation passwordReset($token: String!,
                                   $password1: String!,
                                   $password2: String!) {
                passwordReset(token: $token,
                              newPassword1: $password1,
                              newPassword2: $password2) {
                    success
                    errors
                }
            }
            """,
            op_name="passwordReset",
            variables={"token": token, "password1": password, "password2": password},
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertTrue(content["data"]["passwordReset"]["success"])

    def password_change_mutation(
        self, variables: dict, headers: dict = {}
    ) -> HttpResponse:
        return self.query(
            """
            mutation passwordChange($old_password: String!,
                                    $new_password1: String!,
                                    $new_password2: String!) {
                passwordChange(oldPassword: $old_password,
                               newPassword1: $new_password1,
                               newPassword2: $new_password2) {
                    success
                    errors
                    token
                }
            }
            """,
            op_name="passwordChange",
            variables=variables,
            headers=headers,
        )

    def test_password_change_mutation(self):
        user = self.create_user(email=self.fake.email())
        old_password = self.fake.password()
        new_password = self.fake.password()
        user.set_password(old_password)
        user.save()
        # only verified users can change their passwords
        status = user.status
        status.verified = True
        status.save(update_fields=["verified"])
        token = get_auth_token(user)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        variables = {
            "old_password": old_password,
            "new_password1": new_password,
            "new_password2": new_password,
        }
        response = self.password_change_mutation(variables, headers)
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertIsNone(content["data"]["passwordChange"]["errors"])
        self.assertTrue(content["data"]["passwordChange"]["success"])

    def test_password_change_mutation_unverified(self):
        user = self.create_user(email=self.fake.email())
        old_password = self.fake.password()
        new_password = self.fake.password()
        user.set_password(old_password)
        user.save()  # This user is not yet verified

        token = get_auth_token(user)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}

        variables = {
            "old_password": old_password,
            "new_password1": new_password,
            "new_password2": new_password,
        }
        response = self.password_change_mutation(variables, headers)

        content = json.loads(response.content)
        self.assertIsNotNone(content["data"]["passwordChange"]["errors"])

    def test_password_change_mutation_new_password_does_not_match(self):
        user = self.create_user(email=self.fake.email())
        old_password = self.fake.password()
        new_password = self.fake.password()
        user.set_password(old_password)
        user.save()

        # only verified users can change their passwords
        status = user.status
        status.verified = True
        status.save(update_fields=["verified"])

        token = get_auth_token(user)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}

        variables = {
            "old_password": old_password,
            "new_password1": new_password,
            "new_password2": self.fake.password(),
        }
        response = self.password_change_mutation(variables, headers)
        content = json.loads(response.content)

        self.assertIsNotNone(content["data"]["passwordChange"]["errors"])

    def test_password_change_mutation_incorrect_old_password(self):
        user = self.create_user(email=self.fake.email())
        old_password = self.fake.password()
        new_password = self.fake.password()
        user.set_password(old_password)
        user.save()

        # only verified users can change their passwords
        status = user.status
        status.verified = True
        status.save(update_fields=["verified"])

        token = get_auth_token(user)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}

        variables = {
            "old_password": self.fake.password(),
            "new_password1": new_password,
            "new_password2": new_password,
        }
        response = self.password_change_mutation(variables, headers)
        content = json.loads(response.content)

        self.assertIsNotNone(content["data"]["passwordChange"]["errors"])
