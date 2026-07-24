from django import forms

from apps.academics.models import (
    AcademicYear,
    ClassSection,
)
from apps.promotions.models import (
    PromotionDecision,
)


class PromotionDecisionForm(
    forms.Form
):

    final_decision = (
        forms.ChoiceField(
            choices=(
                PromotionDecision
                .Decision.choices
            )
        )
    )

    target_class_section = (
        forms.ModelChoiceField(
            queryset=(
                ClassSection.objects.none()
            ),
            required=False,
        )
    )

    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
            }
        ),
    )

    def __init__(
        self,
        *args,
        school=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        if school:

            self.fields[
                "target_class_section"
            ].queryset = (
                ClassSection.objects
                .for_school(school)
                .filter(
                    is_active=True
                )
                .select_related(
                    "level"
                )
                .order_by(
                    "level__order",
                    "name",
                )
            )


class PromotionExecutionForm(
    forms.Form
):

    next_academic_year = (
        forms.ModelChoiceField(
            queryset=(
                AcademicYear.objects.none()
            ),
            required=False,
        )
    )

    enrolled_on = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    def __init__(
        self,
        *args,
        school=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        if school:

            self.fields[
                "next_academic_year"
            ].queryset = (
                AcademicYear.objects
                .for_school(school)
                .filter(
                    status__in=[
                        AcademicYear.Status.PLANNED,
                        AcademicYear.Status.ACTIVE,
                    ]
                )
                .order_by(
                    "starts_on"
                )
            )