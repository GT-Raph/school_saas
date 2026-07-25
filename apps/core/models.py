import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """
    Base model for entities that need UUID primary keys
    and creation/update timestamps.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True


class SchoolOwnedQuerySet(models.QuerySet):
    """
    Common tenant-scoping helper.

    Example:
        Student.objects.for_school(request.school)
    """

    def for_school(self, school):
        return self.filter(
            school=school
        )


class SchoolOwnedManager(
    models.Manager.from_queryset(
        SchoolOwnedQuerySet
    )
):
    pass


class SchoolOwnedModel(TimeStampedModel):
    """
    Base model for any record owned by a school tenant.

    Every tenant-specific business record should normally inherit
    from this model.
    """

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name=(
            "%(app_label)s_%(class)s_records"
        ),
    )

    objects = SchoolOwnedManager()

    class Meta:
        abstract = True