import graphene
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired
from django.utils.translation import ugettext_lazy as _
from graphql_auth import mutations
from graphql_auth.constants import Messages
from graphql_auth.exceptions import TokenScopeError, UserAlreadyVerified
from graphql_auth.models import TokenAction, UserStatus
from graphql_auth.settings import graphql_auth_settings as app_settings
from graphql_auth.utils import get_token_paylod
from graphql_jwt.shortcuts import create_refresh_token, get_token

from ..mailer import AccountsMailer

User = get_user_model()


class CustomRegister(mutations.Register):
    @classmethod
    def mutate(cls, root, info, **input):
        """
        Override mutate method to check if `email` alredy exists. If True, send
        an email notification informing the user that the email has been used
        in signup. Otherwise, send an activation email.
        """

        # This can be either `username` or `email` depending on what is set
        # in USERNAME_FIELD
        username = input.get(User.USERNAME_FIELD)
        kwargs = {User.USERNAME_FIELD: username}

        # Check if user already exists
        try:
            user = User.objects.get(**kwargs)
        except User.DoesNotExist:
            user = None

        if user:
            # If user is already verified, send an email informing him/her
            # that the email has been used in sign up. If user is not yet
            # verified, resend the activation email. Terminate the process
            # afterwards.
            if user.status.verified:
                mailer = AccountsMailer()
                mailer.send_existing_email(**input)
            else:
                user.status.resend_activation_email(info)
            return cls(success=True, errors=None)

        return cls.resolve_mutation(root, info, **input)


class CustomVerify(mutations.VerifyAccount):

    access_token = graphene.String(description=_("Access token of the verified user."))
    refresh_token = graphene.String(
        description=_("Refresh token of the verified user.")
    )

    @classmethod
    def get_user(cls, token):
        """
        Retrieves the User object based on the given verification token.
        """
        payload = get_token_paylod(
            token, TokenAction.ACTIVATION, app_settings.EXPIRATION_ACTIVATION_TOKEN
        )
        return User.objects.get(**payload)

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        """
        Override verify account to allow returning of `acces_token` and
        `refresh_token` into the response so users can login after account
        verification.
        """

        try:
            token = kwargs.get("token")
            UserStatus.verify(token)
            response = {"success": True}

            if settings.GRAPHQL_AUTH.get("ALLOW_LOGIN_AFTER_VERIFY", False):
                user = cls.get_user(token)
                access_token = get_token(user)
                refresh_token = create_refresh_token(user)
                response.update(
                    {"access_token": access_token, "refresh_token": refresh_token}
                )

            return cls(**response)
        except UserAlreadyVerified:
            return cls(success=False, errors=Messages.ALREADY_VERIFIED)
        except SignatureExpired:
            return cls(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return cls(success=False, errors=Messages.INVALID_TOKEN)


class AuthMutation(graphene.ObjectType):
    """
    Mutatiions used particularly in authentication.
    """

    register = CustomRegister.Field()
    verify_account = CustomVerify.Field()
    resend_activation_email = mutations.ResendActivationEmail.Field()
    send_password_reset_email = mutations.SendPasswordResetEmail.Field()
    password_reset = mutations.PasswordReset.Field()
    password_change = mutations.PasswordChange.Field()
    update_account = mutations.UpdateAccount.Field()
    delete_account = mutations.DeleteAccount.Field()

    # django-graphql-jwt inheritances
    token_auth = mutations.ObtainJSONWebToken.Field()
    verify_token = mutations.VerifyToken.Field()
    refresh_token = mutations.RefreshToken.Field()
    revoke_token = mutations.RevokeToken.Field()
