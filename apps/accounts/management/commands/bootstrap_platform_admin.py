import os

from django.core.management.base import (
    BaseCommand,
)

from apps.accounts.models import User


class Command(BaseCommand):

    help = (
        "Create the initial platform "
        "administrator from environment variables."
    )

    def handle(
        self,
        *args,
        **options,
    ):
        username = os.environ.get(
            "BOOTSTRAP_ADMIN_USERNAME",
            "",
        ).strip()

        email = os.environ.get(
            "BOOTSTRAP_ADMIN_EMAIL",
            "",
        ).strip()

        password = os.environ.get(
            "BOOTSTRAP_ADMIN_PASSWORD",
            "",
        )

        if not username or not password:

            self.stdout.write(
                self.style.WARNING(
                    (
                        "Bootstrap administrator "
                        "variables are not complete. "
                        "Skipping."
                    )
                )
            )

            return

        if User.objects.filter(
            username=username
        ).exists():

            self.stdout.write(
                self.style.WARNING(
                    (
                        f"User '{username}' "
                        "already exists. No changes made."
                    )
                )
            )

            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        user.is_platform_admin = True
        user.must_change_password = True

        user.save(
            update_fields=[
                "is_platform_admin",
                "must_change_password",
                "updated_at",
            ]
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Created platform "
                    f"administrator '{username}'."
                )
            )
        )