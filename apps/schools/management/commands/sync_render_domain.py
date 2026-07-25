import os

from django.conf import settings
from django.core.management.base import (
    BaseCommand,
)

from apps.schools.models import (
    School,
    SchoolDomain,
)


class Command(BaseCommand):

    help = (
        "Register the Render hostname "
        "against the configured default tenant."
    )

    def handle(
        self,
        *args,
        **options,
    ):
        hostname = os.environ.get(
            "RENDER_EXTERNAL_HOSTNAME",
            "",
        ).strip().lower()

        school_slug = getattr(
            settings,
            "DEFAULT_TENANT_SLUG",
            "",
        ).strip()

        if not hostname:

            self.stdout.write(
                self.style.WARNING(
                    (
                        "RENDER_EXTERNAL_HOSTNAME "
                        "is not set. Skipping."
                    )
                )
            )

            return

        if not school_slug:

            self.stdout.write(
                self.style.WARNING(
                    (
                        "DEFAULT_TENANT_SLUG "
                        "is not set. Skipping."
                    )
                )
            )

            return

        school = School.objects.get(
            slug=school_slug
        )

        domain, created = (
            SchoolDomain.objects.update_or_create(
                domain=hostname,
                defaults={
                    "school": school,
                    "is_verified": True,
                    "is_primary": False,
                },
            )
        )

        action = (
            "Created"
            if created
            else "Updated"
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{action} Render domain "
                    f"{domain.domain} for "
                    f"{school.name}."
                )
            )
        )