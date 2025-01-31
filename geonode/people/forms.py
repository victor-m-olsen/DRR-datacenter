# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import taggit

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import ugettext_lazy as _

from geonode.people.models import Profile, Organization
from geonode.base.models import ContactRole

# Ported in from django-registration
attrs_dict = {'class': 'required'}


class ProfileCreationForm(UserCreationForm):

    class Meta:
        model = Profile
        fields = ("username",)

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            Profile.objects.get(username=username)
        except Profile.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )


class ProfileChangeForm(UserChangeForm):

    class Meta:
        model = Profile
        fields = '__all__'


class ForgotUsernameForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_(u'Email Address'))


class RoleForm(forms.ModelForm):

    class Meta:
        model = ContactRole
        exclude = ('contact', 'layer')


class PocForm(forms.Form):
    contact = forms.ModelChoiceField(label="New point of contact",
                                     queryset=Profile.objects.all())


class ProfileForm(forms.ModelForm):
    keywords = taggit.forms.TagField(
        required=False,
        help_text=_("A space or comma-separated list of keywords"))

    class Meta:
        model = Profile
        exclude = (
            'user',
            'password',
            'last_login',
            'groups',
            'user_permissions',
            'username',
            'is_staff',
            'is_superuser',
            'is_active',
            'date_joined')

class OrganizationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(OrganizationForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        for field in self.Meta.required:
            self.fields[field].required = True

    def clean_org_acronym(self):
        qs = Organization.valid_only().filter(org_acronym=self.cleaned_data["org_acronym"])
        if qs.exists():
            raise forms.ValidationError(_("Organization acronym already exist."))
        return self.cleaned_data["org_acronym"]

    class Meta:
        model = Organization
        required = (
            'organization',
            'org_acronym',
            'org_type',
            'org_name_status',
            'requester_email',
            'requester_first_name',
            'requester_last_name',
        )
        exclude = (
            'record_status',
            'request_reject_reason',
            'created_at',
            'updated_at',
        )
