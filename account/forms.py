from __future__ import unicode_literals

import re

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = None

from django import forms
from django.utils.translation import ugettext_lazy as _

from django.contrib import auth

from account.compat import get_user_model, get_user_lookup_kwargs
from account.conf import settings
from account.hooks import hookset
from account.models import EmailAddress, SignupCode, SignupCodeExtended
from geonode.base.enumerations import COUNTRIES, ORG_ACCRONYM, ORG_NAME_STATUS

from geonode.people.models import Organization

alnum_re = re.compile(r"^\w+$")

class SignupForm(forms.Form):
    
    TITLE_CHOICES = (
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Ms', 'Ms'),
        ('DR', 'DR'),
        ('Prof', 'Prof')
    )

    username = forms.CharField(
        label=_("Username"),
        max_length=30,
        widget=forms.TextInput(),
        required=False
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False)
    )
    password_confirm = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput(render_value=False)
    )

    title = forms.ChoiceField(
        label=_("Title"),
        widget=forms.Select(), choices=TITLE_CHOICES, required=True)

    first_name = forms.CharField(
        label=_("First Name"),
        widget=forms.TextInput(),
        required=True
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        widget=forms.TextInput(),
        required=True
    )

    email = forms.EmailField(
        label=_("Email"),
        widget=forms.TextInput(), required=True)

    organization = forms.ChoiceField(
        label=_("Organization"),
        widget=forms.Select(), required=True)

    org_acronym = forms.CharField(
        label=_("Organisation acronym"),
        widget=forms.TextInput(attrs={'readonly':'readonly'}), required=False)

    org_type = forms.CharField(
        label=_("Organization Type"),
        widget=forms.TextInput(attrs={'readonly':'readonly'}), required=False)

    org_name_status = forms.CharField(
        label=_("Organization Name Status"),
        widget=forms.TextInput(attrs={'readonly':'readonly'}), required=False)


    position = forms.CharField(
        label=_("Function / Position"),
        widget=forms.TextInput(), required=False)

    code = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.HiddenInput()
    )
    
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        if 'code' in self.initial:
            code = self.initial['code']
            sc = SignupCode.objects.get(code=code)
            if SignupCodeExtended.objects.filter(signupcode = sc).exists():
                field = self.fields['username']
                field.widget.attrs['readonly'] = True
        self.fields['organization'].choices = Organization.valid_only()\
            .values_list('org_acronym','organization')\
            .order_by('organization')

    def clean_username(self):
        if not alnum_re.search(self.cleaned_data["username"].replace('.', '')):
            raise forms.ValidationError(_("Usernames can only contain letters, numbers, dots and underscores."))
        User = get_user_model()
        lookup_kwargs = get_user_lookup_kwargs({
            "{username}__iexact": self.cleaned_data["username"]
        })
        qs = User.objects.filter(**lookup_kwargs)
        if not qs.exists():
            return self.cleaned_data["username"]
        raise forms.ValidationError(_("This username is already taken. Please choose another."))

    def clean_email(self):
        value = self.cleaned_data["email"]
        qs = EmailAddress.objects.filter(email__iexact=value)
        if not qs.exists() or not settings.ACCOUNT_EMAIL_UNIQUE:
            return value
        raise forms.ValidationError(_("A user is registered with this email address."))

    def clean_organization(self):
        qs = Organization.valid_only().filter(org_acronym=self.cleaned_data["organization"])
        if not qs.exists():
            raise forms.ValidationError(_("Organization not found."))
        self.cleaned_data["organization"] = qs[0].organization
        self.cleaned_data["org_type"] = qs[0].org_type
        self.cleaned_data["org_name_status"] = qs[0].org_name_status
        return self.cleaned_data["organization"]

    def clean(self):
        if "password" in self.cleaned_data and "password_confirm" in self.cleaned_data:
            if self.cleaned_data["password"] != self.cleaned_data["password_confirm"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data


class LoginForm(forms.Form):

    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False)
    )
    remember = forms.BooleanField(
        label=_("Remember Me"),
        required=False
    )
    user = None

    def clean(self):
        if self._errors:
            return
        user = auth.authenticate(**self.user_credentials())
        if user:
            if user.is_active:
                self.user = user
            else:
                raise forms.ValidationError(_("This account is inactive."))
        else:
            raise forms.ValidationError(self.authentication_fail_message)
        return self.cleaned_data

    def user_credentials(self):
        return hookset.get_user_credentials(self, self.identifier_field)


class LoginUsernameForm(LoginForm):

    username = forms.CharField(label=_("Username"), max_length=30)
    authentication_fail_message = _("The username and/or password you specified are not correct.")
    identifier_field = "username"

    def __init__(self, *args, **kwargs):
        super(LoginUsernameForm, self).__init__(*args, **kwargs)
        field_order = ["username", "password", "remember"]
        if not OrderedDict or hasattr(self.fields, "keyOrder"):
            self.fields.keyOrder = field_order
        else:
            self.fields = OrderedDict((k, self.fields[k]) for k in field_order)


class LoginEmailForm(LoginForm):

    email = forms.EmailField(label=_("Email"))
    authentication_fail_message = _("The email address and/or password you specified are not correct.")
    identifier_field = "email"

    def __init__(self, *args, **kwargs):
        super(LoginEmailForm, self).__init__(*args, **kwargs)
        field_order = ["email", "password", "remember"]
        if not OrderedDict or hasattr(self.fields, "keyOrder"):
            self.fields.keyOrder = field_order
        else:
            self.fields = OrderedDict((k, self.fields[k]) for k in field_order)


class ChangePasswordForm(forms.Form):

    password_current = forms.CharField(
        label=_("Current Password"),
        widget=forms.PasswordInput(render_value=False)
    )
    password_new = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(render_value=False)
    )
    password_new_confirm = forms.CharField(
        label=_("New Password (again)"),
        widget=forms.PasswordInput(render_value=False)
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_password_current(self):
        if not self.user.check_password(self.cleaned_data.get("password_current")):
            raise forms.ValidationError(_("Please type your current password."))
        return self.cleaned_data["password_current"]

    def clean_password_new_confirm(self):
        if "password_new" in self.cleaned_data and "password_new_confirm" in self.cleaned_data:
            if self.cleaned_data["password_new"] != self.cleaned_data["password_new_confirm"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password_new_confirm"]


class PasswordResetForm(forms.Form):

    email = forms.EmailField(label=_("Email"), required=True)

    def clean_email(self):
        value = self.cleaned_data["email"]
        if not EmailAddress.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError(_("Email address can not be found."))
        return value


class PasswordResetTokenForm(forms.Form):

    password = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(render_value=False)
    )
    password_confirm = forms.CharField(
        label=_("New Password (again)"),
        widget=forms.PasswordInput(render_value=False)
    )

    def clean_password_confirm(self):
        if "password" in self.cleaned_data and "password_confirm" in self.cleaned_data:
            if self.cleaned_data["password"] != self.cleaned_data["password_confirm"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password_confirm"]


class SettingsForm(forms.Form):

    email = forms.EmailField(label=_("Email"), required=True)
    timezone = forms.ChoiceField(
        label=_("Timezone"),
        choices=[("", "---------")] + settings.ACCOUNT_TIMEZONES,
        required=False
    )
    if settings.USE_I18N:
        language = forms.ChoiceField(
            label=_("Language"),
            choices=settings.ACCOUNT_LANGUAGES,
            required=False
        )

    def clean_email(self):
        value = self.cleaned_data["email"]
        if self.initial.get("email") == value:
            return value
        qs = EmailAddress.objects.filter(email__iexact=value)
        if not qs.exists() or not settings.ACCOUNT_EMAIL_UNIQUE:
            return value
        raise forms.ValidationError(_("A user is registered with this email address."))
        
class SignupCodeForm(forms.ModelForm):

    username = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = SignupCode
        fields = ('email', )

