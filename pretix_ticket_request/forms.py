import json

from django import forms
from django.db.models.query import QuerySet
from django.utils.translation import (
    pgettext_lazy, ugettext_lazy as _, ugettext_noop,
)
from django_countries import Countries
from i18nfield.forms import (
    I18nForm, I18nFormField, I18nTextarea, I18nTextInput,
)
from i18nfield.strings import LazyI18nString
from django.core.exceptions import ValidationError
from pretix.base.validators import EmailBanlistValidator
from pretix.base.forms import SettingsForm
from pretix.base.models import Quota
from pretix.base.services.mail import mail
from pretix.base.i18n import language
from .models import TicketRequest, Attendee


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
        label=_("Do you identify as being part of an ethnic, racial or cultural minority group?"),
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
        self.event = kwargs.pop('event')

        super().__init__(*args, **kwargs)

        if self.instance:
            meta_json = self.instance.data
            for field in self.Meta.json_fields:
                if meta_json.get(field):
                    self.fields[field].initial = meta_json.get(field)

    def save(self, commit=True):
        event = self.event
        meta_json = self.instance.data
        for field in self.Meta.json_fields:
            meta_json[field] = self.cleaned_data[field]
        self.instance.data = meta_json

        saved = super().save(commit=commit)

        locale = 'en'
        email = self.instance.email
        name = self.instance.name

        if saved:
            with language(locale):
                email_content = LazyI18nString.from_gettext(ugettext_noop("""Dear {name} ,

Thank you for applying for an IFF Ticket. We are currently reviewing ticket requests, and as space becomes available, we will be issuing tickets.

If you have any questions, please email team@internetfreedomfestival.org

Best regards,
Your {event} team"""))

                email_context = {
                    'event': event,
                    'name': name
                }

                mail(
                    email,
                    _('Your {event} ticket request').format(event=str(event)),
                    email_content,
                    email_context,
                    event,
                    locale=locale
                )

        return saved

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


class YourAccountStepForm(forms.Form):
    required_css_class = 'required'
    email = forms.EmailField(label=_('E-mail'),
                             validators=[EmailBanlistValidator()],
                             widget=forms.EmailInput(attrs={'autocomplete': 'section-contact email'}),
                             required=True,
                             )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.request = kwargs.pop('request')

        super().__init__(*args, **kwargs)

        self.fields['email_repeat'] = forms.EmailField(
            label=_('E-mail address (repeated)'),
            help_text=_('Please enter the same email address again to make sure you typed it correctly.'),
        )

    def clean(self):
        if self.event.settings.order_email_asked_twice and self.cleaned_data.get('email') and self.cleaned_data.get('email_repeat'):
            if self.cleaned_data.get('email').lower() != self.cleaned_data.get('email_repeat').lower():
                raise ValidationError(_('Please enter the same email address twice.'))

    def save(self, commit=True):
        return super().save(commit=commit)


class VerifyAccountStepForm(forms.Form):
    required_css_class = 'required'
    verification_code = forms.CharField(label=_('Verification code'),
                                        max_length=6, min_length=6,
                                        help_text=_('Enter the 6 digits verification code'),
                                        required=True,
                                        )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.request = kwargs.pop('request')

        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        return super().save(commit=commit)


class AttendeeProfileForm(forms.Form):
    name = forms.CharField(
        label=_("Full name"),
        required=True,
    )

    public_name = forms.CharField(
        label=_("Public display name"),
        required=True,
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
        label=_("Do you identify as being part of an ethnic, racial or cultural minority group?"),
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
        self.attendee = kwargs.pop('attendee')

        super().__init__(*args, **kwargs)

        meta_json = self.attendee.profile
        for field in self.Meta.json_fields:
            if meta_json.get(field):
                self.fields[field].initial = meta_json.get(field)

    def save(self, commit=True):
        meta_json = self.attendee.profile
        for field in self.Meta.json_fields:
            meta_json[field] = self.cleaned_data[field]
        self.attendee.profile = meta_json

        return self.attendee.save()

    class Meta:
        model = Attendee
        fields = ()
        json_fields = (
            'name',
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


class AttendeeDetailForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Full name"),
        required=True,
    )

    public_name = forms.CharField(
        label=_("Public display name"),
        required=True,
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
        label=_("Do you identify as being part of an ethnic, racial or cultural minority group?"),
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
            meta_json = self.instance.profile
            for field in self.Meta.json_fields:
                if meta_json.get(field):
                    self.fields[field].initial = meta_json.get(field)

    def save(self, commit=True):
        meta_json = self.instance.profile
        for field in self.Meta.json_fields:
            meta_json[field] = self.cleaned_data[field]
        self.instance.profile = meta_json

        return super().save(commit=commit)

    class Meta:
        model = Attendee
        fields = (
            'email',
            'verified'
        )
        json_fields = (
            'name',
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
