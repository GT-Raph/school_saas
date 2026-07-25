from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db.models import F

from apps.academics.models import (
    Enrollment,
    SubjectOffering,
    TeacherAssignment,
)
from apps.assessments.models import (
    OfferingAssessmentPlan,
    Score,
    SubjectResult,
)
from apps.attendance.models import (
    AttendanceRecord,
    AttendanceSession,
)
from apps.finance.models import (
    LedgerEntry,
    Payment,
    PaymentAllocation,
    StudentInvoice,
)
from apps.guardians.models import (
    StudentGuardian,
)
from apps.promotions.models import (
    PromotionEvaluation,
)
from apps.reports.models import (
    TermResult,
)


class Command(BaseCommand):

    help = (
        "Check critical records for "
        "cross-school relationship mismatches."
    )

    def handle(
        self,
        *args,
        **options,
    ):
        checks = [
            (
                "Enrollment → Student",
                Enrollment.objects.exclude(
                    student__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "Enrollment → AcademicYear",
                Enrollment.objects.exclude(
                    academic_year__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "Enrollment → ClassSection",
                Enrollment.objects.exclude(
                    class_section__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "StudentGuardian → Student",
                StudentGuardian.objects.exclude(
                    student__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "StudentGuardian → Guardian",
                StudentGuardian.objects.exclude(
                    guardian__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "SubjectOffering → Subject",
                SubjectOffering.objects.exclude(
                    subject__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "SubjectOffering → Class",
                SubjectOffering.objects.exclude(
                    class_section__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "TeacherAssignment → Offering",
                TeacherAssignment.objects.exclude(
                    offering__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "TeacherAssignment → Teacher",
                TeacherAssignment.objects.exclude(
                    teacher__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "AttendanceSession → Term",
                AttendanceSession.objects.exclude(
                    term__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "AttendanceRecord → Session",
                AttendanceRecord.objects.exclude(
                    session__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "AttendanceRecord → Enrollment",
                AttendanceRecord.objects.exclude(
                    enrollment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "AssessmentPlan → Offering",
                OfferingAssessmentPlan.objects.exclude(
                    offering__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "Score → Assessment",
                Score.objects.exclude(
                    assessment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "Score → Enrollment",
                Score.objects.exclude(
                    enrollment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "SubjectResult → Plan",
                SubjectResult.objects.exclude(
                    assessment_plan__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "SubjectResult → Enrollment",
                SubjectResult.objects.exclude(
                    enrollment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "TermResult → Enrollment",
                TermResult.objects.exclude(
                    enrollment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "TermResult → Term",
                TermResult.objects.exclude(
                    term__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "StudentInvoice → Enrollment",
                StudentInvoice.objects.exclude(
                    enrollment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "Payment → Enrollment",
                Payment.objects.exclude(
                    enrollment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "PaymentAllocation → Payment",
                PaymentAllocation.objects.exclude(
                    payment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "PaymentAllocation → Invoice",
                PaymentAllocation.objects.exclude(
                    invoice__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "LedgerEntry → Enrollment",
                LedgerEntry.objects.exclude(
                    enrollment__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "PromotionEvaluation → Policy",
                PromotionEvaluation.objects.exclude(
                    policy__school_id=F(
                        "school_id"
                    )
                ),
            ),

            (
                "PromotionEvaluation → Enrollment",
                PromotionEvaluation.objects.exclude(
                    enrollment__school_id=F(
                        "school_id"
                    )
                ),
            ),
        ]

        failures = []

        for label, queryset in checks:

            count = queryset.count()

            if count:

                sample_ids = list(
                    queryset.values_list(
                        "id",
                        flat=True,
                    )[:5]
                )

                failures.append(
                    {
                        "label": label,
                        "count": count,
                        "sample_ids": [
                            str(value)
                            for value
                            in sample_ids
                        ],
                    }
                )

                self.stdout.write(
                    self.style.ERROR(
                        (
                            f"{label}: "
                            f"{count} invalid records. "
                            f"Examples: {sample_ids}"
                        )
                    )
                )

            else:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{label}: OK"
                    )
                )

        if failures:

            raise CommandError(
                (
                    "Tenant integrity check "
                    "found cross-school "
                    "relationship errors."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "All critical tenant "
                    "integrity checks passed."
                )
            )
        )