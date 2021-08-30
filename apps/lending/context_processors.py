from django.contrib.auth import get_user_model

User = get_user_model()


def borrowers(request):
    """
    Returns the list of borrowers.
    """
    return {"borrowers_list": User.objects.filter(is_borrower=True)}
