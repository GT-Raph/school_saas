from django import forms

from .models import (
    School,
    SchoolBranding,
)


class SchoolProfileForm(
    forms.ModelForm
):

    class Meta:
        model = School

        fields = [
            "name",
            "timezone",
            "currency",
            "default_language",
        ]


class SchoolBrandingForm(
    forms.ModelForm
):

    class Meta:
        model = SchoolBranding

        fields = [
            "logo_url",
            "favicon_url",
            "login_background_url",
            "primary_color",
            "secondary_color",
            "accent_color",
            "motto",
        ]