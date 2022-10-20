from django import forms

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
        if pc != '':
            if not is_valid_postcode(pc):
                self._errors["pc"] = [
                    "Invalid postcode or council name"
                ]
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
                    self._errors["pc"] = [
                        "Invalid postcode or council name"
                    ]
                if gss_codes is not None:
                    return gss_codes
        return pc

class ContactPostcodeForm(PostcodeForm):
    pc = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control"
    }))
