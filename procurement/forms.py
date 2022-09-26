from django import forms

from procurement.procurement_utils import is_valid_postcode
from procurement.mapit import (
    MapIt,
    NotFoundException,
    BadRequestException,
    InternalServerErrorException,
    ForbiddenException,
)


class CouncilChoiceAlertForm(forms.Form):
    CHOICES = [
        ("All UK councils", "All UK councils"),
        ("Councils in a region...", "Councils in a region..."),
        ("My council...", "My council..."),
    ]
    council_choice = forms.CharField(widget=forms.RadioSelect(choices=CHOICES))


class HomePageTenderForm(forms.Form):
    def clean_pc(self):
        pc = self.cleaned_data["pc"]
        if not is_valid_postcode(pc):
            self._errors["pc"] = "Invalid postcode or council name"
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
                self._errors["pc"] = "Invalid postcode or council name"
            if gss_codes is not None:
                return gss_codes
        return pc
