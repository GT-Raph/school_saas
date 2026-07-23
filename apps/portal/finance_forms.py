from django import forms

from apps.academics.models import Enrollment
from apps.finance.models import (
    FeeStructure,
    Payment,
    StudentInvoice,
)


class BulkInvoiceForm(forms.Form):

    fee_structure = (
        forms.ModelChoiceField(
            queryset=(
                FeeStructure.objects.none()
            )
        )
    )

    issue_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        )
    )

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    auto_issue = forms.BooleanField(
        required=False,
        initial=False,
        help_text=(
            "Leave unchecked for safer "
            "draft review before issuing."
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
                "fee_structure"
            ].queryset = (
                FeeStructure.objects
                .for_school(school)
                .filter(
                    status=(
                        FeeStructure
                        .Status.ACTIVE
                    )
                )
                .select_related(
                    "term",
                    "class_level",
                    "academic_year",
                )
            )


class PaymentEntryForm(forms.Form):

    enrollment = (
        forms.ModelChoiceField(
            queryset=(
                Enrollment.objects.none()
            )
        )
    )

    invoice = (
        forms.ModelChoiceField(
            queryset=(
                StudentInvoice.objects.none()
            )
        )
    )

    amount = forms.DecimalField(
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
    )

    method = forms.ChoiceField(
        choices=Payment.Method.choices,
    )

    paid_at = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                "type":
                    "datetime-local",
            }
        )
    )

    payer_name = forms.CharField(
        max_length=180,
        required=False,
    )

    reference = forms.CharField(
        max_length=180,
        required=False,
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
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

        self.school = school

        if school:

            self.fields[
                "enrollment"
            ].queryset = (
                Enrollment.objects
                .for_school(school)
                .filter(
                    status=(
                        Enrollment
                        .Status.ACTIVE
                    )
                )
                .select_related(
                    "student",
                    "academic_year",
                    "class_section",
                )
                .order_by(
                    "student__last_name",
                    "student__first_name",
                )
            )

            self.fields[
                "invoice"
            ].queryset = (
                StudentInvoice.objects
                .for_school(school)
                .exclude(
                    status__in=[
                        StudentInvoice
                        .Status.DRAFT,

                        StudentInvoice
                        .Status.PAID,

                        StudentInvoice
                        .Status.VOID,
                    ]
                )
                .select_related(
                    "enrollment__student"
                )
                .order_by(
                    "-issue_date"
                )
            )

    def clean(self):
        cleaned = super().clean()

        enrollment = cleaned.get(
            "enrollment"
        )

        invoice = cleaned.get(
            "invoice"
        )

        if (
            enrollment
            and invoice
            and invoice.enrollment_id
            != enrollment.id
        ):
            self.add_error(
                "invoice",
                (
                    "The selected invoice "
                    "does not belong to "
                    "this student."
                ),
            )

        return cleaned