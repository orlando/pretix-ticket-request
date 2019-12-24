import json

from django import forms
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django_countries import Countries
from i18nfield.forms import (
    I18nForm, I18nFormField, I18nTextarea, I18nTextInput,
)
from pretix.base.forms import SettingsForm
from pretix.base.forms.widgets import DatePickerWidget
from pretix.base.models import (Item, Quota)
from .models import TicketRequest


class TicketRequestsSettingsForm(I18nForm, SettingsForm):
    ticket_request_quota = forms.ModelChoiceField(
        label='Ticket Quota',
        queryset=Quota.objects.none(),
        required=False,
        empty_label='Choose a Quota',
        help_text="Voucher will be created for any ticket under this quota"
    )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)

        # Load tickets
        self.fields['ticket_request_item'].queryset = Item.objects.filter(event=self.event)

        # Load quotas
        self.fields['ticket_request_quota'].queryset = Quota.objects.filter(event=self.event)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class TicketRequestForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Full name"),
        required=True,
    )

    public_name = forms.CharField(
        label=_("Public display name"),
        required=True,
    )

    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.TextInput(
            attrs={
                'type': 'email',
                'placeholder': _('example@internetfreedomfestival.org')
            })
    )

    years_attended_iff = forms.MultipleChoiceField(
        label='Have you attended the IFF before?',
        required=True,
        choices=(
            ("Not yet!", _("Not yet!")),
            ("2019", _("2019")),
            ("2018", _("2018")),
            ("2017", _("2017")),
            ("2016", _("2016")),
            ("2015", _("2015 (CTF)")),
        ),
        widget=forms.CheckboxSelectMultiple(),
    )

    pgp_key = forms.CharField(
        label=_("PGP Key"),
        required=False,
        widget=forms.Textarea(),
    )

    gender = forms.ChoiceField(
        label=_("Gender"),
        choices=(
            ("Female", _("Female")),
            ("Gender-nonconforming", _("Gender-nonconforming")),
            ("Male", _("Male")),
            ("Other", _("Other")),
            ("Prefer not to say", _("Prefer not to say")),
        ),
    )

    country = forms.ChoiceField(
        label=_("Country of Origin"),
        choices=Countries()
    )

    is_refugee = forms.TypedChoiceField(
        label=_("Do you identify as being part of a refugee diaspora community?"),
        choices=(
            ((True, 'Yes'), (False, 'No'))
        ),
        widget=forms.RadioSelect
    )

    belongs_to_minority_group = forms.TypedChoiceField(
        label=_("Do you identify as being part of a refugee diaspora community?"),
        choices=(
            ((True, 'Yes'), (False, 'No'))
        ),
        widget=forms.RadioSelect
    )

    professional_areas = forms.MultipleChoiceField(
        label='Check the boxes that most closely describe the work you do.',
        choices=(
            ("Digital Security Training", _("Digital Security Training")),
            ("Software/Web Development", _("Software/Web Development")),
            ("Cryptography", _("Cryptography")),
            ("Information Security", _("Information Security")),
            ("Student", _("Student")),
            ("Frontline Activism", _("Frontline Activism")),
            ("Research/Academia", _("Research/Academia")),
            ("Social Sciences", _("Social Sciences")),
            ("Policy/Internet Governance", _("Policy/Internet Governance")),
            ("Data Science", _("Data Science")),
            ("Advocacy", _("Advocacy")),
            ("Communications", _("Communications")),
            ("Journalism and Media", _("Journalism and Media")),
            ("Arts & Culture", _("Arts & Culture")),
            ("Design", _("Design")),
            ("Program Management", _("Program Management")),
            ("Philanthropic/Grantmaking Organization", _("Philanthropic/Grantmaking Organization")),
            ("Other", _("Other")),
        ),
        widget=forms.CheckboxSelectMultiple(),
    )

    professional_title = forms.CharField(
        label=_("Professional Title"),
        required=False,
    )

    organization = forms.CharField(
        label=_("Organization"),
        required=False,
    )

    project = forms.CharField(
        label=_("Project"),
        required=False,
    )

    follow_coc = forms.BooleanField(
        label=_("Do you agree to respect and follow IFF’s Code of Conduct?"),
        required=True,
    )

    subscribe_mailing_list = forms.BooleanField(
        label=_("Would you like to subscribe to the IFF Mailing List?"),
        required=False,
    )

    receive_mattermost_invite = forms.BooleanField(
        label=_("Would you like to receive a Mattermost invite?"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            meta_json = self.instance.data
            for field in self.Meta.json_fields:
                if meta_json.get(field):
                    self.fields[field].initial = meta_json.get(field)

    def save(self, commit=True):
        meta_json = self.instance.data
        for field in self.Meta.json_fields:
            meta_json[field] = self.cleaned_data[field]
        self.instance.data = meta_json

        return super().save(commit=commit)

    class Meta:
        model = TicketRequest
        fields = (
            'name',
            'email',
        )
        json_fields = (
            'public_name',
            'years_attended_iff',
            'pgp_key',
            'gender',
            'country',
            'is_refugee',
            'belongs_to_minority_group',
            'professional_areas',
            'professional_title',
            'organization',
            'project',
            'follow_coc',
            'subscribe_mailing_list',
            'receive_mattermost_invite',
        )
