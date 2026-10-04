from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Contact1


class AccountLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "class": "account-input",
                "placeholder": "Your username",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "account-input",
                "placeholder": "Your password",
            }
        ),
    )


class AccountSignUpForm(UserCreationForm):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "class": "account-input",
                "placeholder": "you@example.com",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "autocomplete": "username",
                    "class": "account-input",
                    "placeholder": "Choose a username",
                }
            )
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "class": "account-input",
                "placeholder": "Create a password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "class": "account-input",
                "placeholder": "Confirm your password",
            }
        )


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact1
        fields = ("name1", "emaild", "msg")
        widgets = {
            "name1": forms.TextInput(
                attrs={
                    "autocomplete": "name",
                    "placeholder": "Enter your name",
                    "required": True,
                }
            ),
            "emaild": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "placeholder": "Enter your email",
                    "required": True,
                }
            ),
            "msg": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "How can we help?",
                    "required": True,
                }
            ),
        }


class BookingForm(forms.Form):
    fname = forms.CharField(max_length=25)
    lname = forms.CharField(max_length=25)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField()
    room = forms.ChoiceField(choices=())
    date = forms.DateField(
        input_formats=("%Y-%m-%d",),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    checkout_date = forms.DateField(
        input_formats=("%Y-%m-%d",),
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, room_choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room"].choices = room_choices

    def clean_date(self):
        arrival_date = self.cleaned_data["date"]
        if arrival_date < timezone.localdate():
            raise forms.ValidationError("Arrival date cannot be in the past.")
        return arrival_date

    def clean(self):
        cleaned_data = super().clean()
        arrival_date = cleaned_data.get("date")
        checkout_date = cleaned_data.get("checkout_date")
        if arrival_date and checkout_date and checkout_date <= arrival_date:
            self.add_error(
                "checkout_date",
                "Checkout date must be after the arrival date.",
            )
        return cleaned_data
