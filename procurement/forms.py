from django import forms
from django.core.validators import RegexValidator, EmailValidator

from procurement.procurement_utils import is_valid_postcode
from procurement.mapit import (
    MapIt,
    NotFoundException,
    BadRequestException,
    InternalServerErrorException,
    ForbiddenException,
)


class PostcodeForm(forms.Form):
    def clean_pc(self):
        pc = self.cleaned_data["pc"]
        if pc != "":
            if not is_valid_postcode(pc):
                self._errors["pc"] = ["Invalid UK postcode."]
            else:
                mapit = MapIt()

                gss_codes = None
                try:
                    gss_codes = mapit.postcode_point_to_gss_codes(pc)
                except (
                    NotFoundException,
                    BadRequestException,
                    InternalServerErrorException,
                    ForbiddenException,
                ) as error:
                    self._errors["pc"] = ["Invalid UK postcode."]
                if gss_codes is not None:
                    return gss_codes
        return pc


class ContactPostcodeForm(PostcodeForm):
    pc = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))


class ContactRepresentativeForm(PostcodeForm):
    message = forms.CharField(widget=forms.Textarea())
    name = forms.CharField(widget=forms.TextInput())
    # Use CharField + TextInput for the email boxes so that the
    # validator raises errors rather than using the browser validation,
    # for consistency.
    email = forms.CharField(widget=forms.TextInput(), validators=[EmailValidator()])
    email_check = forms.CharField(
        widget=forms.TextInput(), validators=[EmailValidator()]
    )
    # EXTREMELY permissive regex validation for UK phone numbers.
    phone = forms.CharField(
        validators=[
            RegexValidator(
                regex="^(\d|\s){10,13}$",
                message=("Invalid UK phone number"),
                code="invalid_phone_number",
            )
        ],
        widget=forms.TextInput(),
        required=False,
    )
    address_1 = forms.CharField(widget=forms.TextInput())
    address_2 = forms.CharField(widget=forms.TextInput(), required=False)
    town_city = forms.CharField(widget=forms.TextInput())
    county = forms.CharField(widget=forms.TextInput(), required=False)
    pc = forms.CharField(widget=forms.TextInput())

    def __init__(self, *args, **kwargs):
        super(ContactRepresentativeForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["name"] = field
            self.fields[field].widget.attrs["id"] = field

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        email_check = cleaned_data.get("email_check")
        if email and email_check:
            if email != email_check:
                self._errors["email_check"] = ["Emails do not match."]

        return self.cleaned_data
