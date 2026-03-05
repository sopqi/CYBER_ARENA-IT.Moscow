from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Tournament
from .models import User

class SignUpForm(UserCreationForm):
    fio = forms.CharField(label="ФИО", required=True)
    campus = forms.ChoiceField(choices=User.CAMPUSES, label="Корпус")
    group_number = forms.CharField(label="Группа", widget=forms.Select(choices=[]))

    class Meta:
        model = User
        fields = ('username', 'email', 'fio', 'campus', 'group_number')

class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['title', 'game', 'image', 'description', 'max_participants', 'date']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }