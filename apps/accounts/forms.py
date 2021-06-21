from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm


class LoginForm(AuthenticationForm):
    """
    custom authentication form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control form-control-user"

        self.fields["username"].widget.attrs["placeholder"] = "Enter Email Address..."
        self.fields["username"].widget.attrs["aria-describedby"] = "emaiHelp"
        self.fields["password"].widget.attrs["placeholder"] = "Password"


class CustomSetPasswordForm(SetPasswordForm):
    """
    custom password change form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"
            self.fields["new_password1"].widget.attrs["placeholder"] = "New Password"
            self.fields["new_password2"].widget.attrs[
                "placeholder"
            ] = "Password Confirmation"
