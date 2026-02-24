from django import forms
from django.contrib.auth.models import User

from .permissions import ROLE_GROUPS


class RoleAssignmentForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'), label='Хэрэглэгч')
    role = forms.ChoiceField(
        choices=[(key, label) for key, label in ROLE_GROUPS.items()],
        label='Эрхийн түвшин',
    )
