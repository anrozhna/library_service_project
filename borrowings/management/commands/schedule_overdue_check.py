from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Schedule the daily overdue borrowings check task"

    def handle(self, *args, **options):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="9",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )

        task, created = PeriodicTask.objects.get_or_create(
            name="Check overdue borrowings daily",
            defaults={
                "crontab": schedule,
                "task": "borrowings.tasks.check_overdue_borrowings",
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS("Scheduled task created successfully.")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Scheduled task already exists.")
            )
