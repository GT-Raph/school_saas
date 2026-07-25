from django import forms
from django.forms import formset_factory

from apps.attendance.models import AttendanceRecord


class AttendanceRowForm(forms.Form):
    enrollment_id = forms.UUIDField(
        widget=forms.HiddenInput()
    )

    student_name = forms.CharField(
        disabled=True,
        required=False,
    )

    admission_number = forms.CharField(
        disabled=True,
        required=False,
    )

    status = forms.ChoiceField(
        choices=AttendanceRecord.Status.choices,
        initial=AttendanceRecord.Status.PRESENT,
    )

    remarks = forms.CharField(
        required=False,
        max_length=255,
    )


AttendanceFormSet = formset_factory(
    AttendanceRowForm,
    extra=0,
    max_num=200,
    validate_max=True,
    absolute_max=250,
)


class ScoreRowForm(forms.Form):
    enrollment_id = forms.UUIDField(
        widget=forms.HiddenInput()
    )

    student_name = forms.CharField(
        disabled=True,
        required=False,
    )

    admission_number = forms.CharField(
        disabled=True,
        required=False,
    )

    raw_score = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=7,
    )

    is_absent = forms.BooleanField(
        required=False,
    )

    comment = forms.CharField(
        required=False,
        max_length=255,
    )

    def __init__(
        self,
        *args,
        max_score=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.max_score = max_score

        if max_score is not None:
            self.fields[
                "raw_score"
            ].max_value = max_score

            self.fields[
                "raw_score"
            ].help_text = (
                f"Maximum: {max_score}"
            )

    def clean(self):
        cleaned = super().clean()

        score = cleaned.get(
            "raw_score"
        )

        absent = cleaned.get(
            "is_absent"
        )

        if absent and score is not None:
            self.add_error(
                "raw_score",
                (
                    "Do not enter a score "
                    "for an absent student."
                ),
            )

        if (
            not absent
            and score is None
        ):
            self.add_error(
                "raw_score",
                (
                    "Enter a score or mark "
                    "the student absent."
                ),
            )

        if (
            score is not None
            and self.max_score is not None
            and score > self.max_score
        ):
            self.add_error(
                "raw_score",
                (
                    f"Score cannot exceed "
                    f"{self.max_score}."
                ),
            )

        return cleaned


ScoreFormSet = formset_factory(
    ScoreRowForm,
    extra=0,
    max_num=200,
    validate_max=True,
    absolute_max=250,
)