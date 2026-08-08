import hashlib
import secrets
from datetime import timedelta

from django.core.exceptions import (
    ValidationError,
)
from django.db import transaction
from django.utils import timezone

from apps.schools.models import (
    SchoolMembership,
)

from .models import LoginHandoff


HANDOFF_LIFETIME_SECONDS = 60


def hash_handoff_token(
    token,
):
    return hashlib.sha256(
        token.encode(
            "utf-8"
        )
    ).hexdigest()


def create_login_handoff(
    *,
    user,
    school,
):
    membership_exists = (
        SchoolMembership.objects
        .filter(
            user=user,
            school=school,
            is_active=True,
        )
        .exists()
    )

    if not membership_exists:

        raise ValidationError(
            (
                "This user does not have "
                "active access to this school."
            )
        )

    token = secrets.token_urlsafe(
        32
    )

    LoginHandoff.objects.create(
        user=user,

        school=school,

        token_hash=(
            hash_handoff_token(
                token
            )
        ),

        expires_at=(
            timezone.now()
            + timedelta(
                seconds=(
                    HANDOFF_LIFETIME_SECONDS
                )
            )
        ),
    )

    return token


@transaction.atomic
def consume_login_handoff(
    *,
    token,
    school,
):
    if not token:

        raise ValidationError(
            "Login token is missing."
        )

    token_hash = (
        hash_handoff_token(
            token
        )
    )

    handoff = (
        LoginHandoff.objects
        .select_for_update()
        .select_related(
            "user",
            "school",
        )
        .filter(
            token_hash=token_hash
        )
        .first()
    )

    if not handoff:

        raise ValidationError(
            (
                "This login request "
                "is invalid."
            )
        )

    if (
        handoff.school_id
        != school.id
    ):

        raise ValidationError(
            (
                "This login request "
                "belongs to another school."
            )
        )

    if handoff.consumed_at:

        raise ValidationError(
            (
                "This login request "
                "has already been used."
            )
        )

    now = timezone.now()

    if handoff.expires_at <= now:

        raise ValidationError(
            (
                "This login request "
                "has expired."
            )
        )

    membership_exists = (
        SchoolMembership.objects
        .filter(
            user=handoff.user,

            school=school,

            is_active=True,
        )
        .exists()
    )

    if not membership_exists:

        raise ValidationError(
            (
                "Your access to this school "
                "is no longer active."
            )
        )

    handoff.consumed_at = now

    handoff.save(
        update_fields=[
            "consumed_at",
            "updated_at",
        ]
    )

    return handoff.user