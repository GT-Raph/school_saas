from django.db import models

from apps.core.models import TimeStampedModel
from apps.schools.models import School


class SubscriptionPlan(TimeStampedModel):
    """
    Commercial SaaS plan.

    Do not hard-code:
        if school.plan == "Growth"

    Instead, read entitlements from the plan.
    """

    name = models.CharField(
        max_length=100,
    )

    code = models.SlugField(
        max_length=100,
        unique=True,
    )

    active_student_limit = models.PositiveIntegerField(
        default=200,
    )

    admin_user_limit = models.PositiveIntegerField(
        default=5,
    )

    features = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Feature entitlement map. "
            "Example: {'finance': true, 'payroll': false}"
        ),
    )

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self) -> str:
        return self.name


class SchoolSubscription(TimeStampedModel):
    class Status(models.TextChoices):
        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Active"
        PAYMENT_DUE = "payment_due", "Payment Due"
        GRACE_PERIOD = "grace_period", "Grace Period"
        READ_ONLY = "read_only", "Read Only"
        SUSPENDED = "suspended", "Suspended"
        CANCELLED = "cancelled", "Cancelled"

    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="school_subscriptions",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.TRIAL,
    )

    period_start = models.DateField()

    period_end = models.DateField()

    grace_period_end = models.DateField(
        null=True,
        blank=True,
    )

    auto_renew = models.BooleanField(
        default=False,
    )

    @property
    def can_write(self) -> bool:
        return self.status in {
            self.Status.TRIAL,
            self.Status.ACTIVE,
            self.Status.PAYMENT_DUE,
            self.Status.GRACE_PERIOD,
        }

    def __str__(self) -> str:
        return f"{self.school} - {self.plan}"