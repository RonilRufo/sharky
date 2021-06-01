from django.contrib.auth.forms import AuthenticationForm


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
