from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta , datetime
from prof.models import Posts
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
class Command(BaseCommand):



    def handle(self, *args, **kwargs):
        current_time = now()
        one_day_from_now = current_time + timedelta(days=1)
        next_day_time = current_time + timedelta(days=1)

        upcoming_jobs = Posts.objects.filter(
            post_date__lte=next_day_time.date(),
            post_date__gte=current_time.date(),
            is_accepted__isnull=False
        )

        for job in upcoming_jobs:

            try:
                worker = User.objects.get(id=job.is_accepted)
                homeowner = job.homeowner
                worker_email = worker.email
                homeowner_email = homeowner.email
                job_title = job.title
                scheduled_datetime = datetime.combine(job.post_date, job.post_time)


                subject = f"Reminder: Upcoming Job - {job_title}"
                message_worker = (
                    f"Dear Worker,\n\n"
                    f"You have a job titled '{job_title}' scheduled at {scheduled_datetime}. "
                    f"Please make sure to prepare accordingly.\n\n"
                    f"Best regards,\n"
                    f"The Professionals Team"
                )
                message_homeowner = (
                    f"Dear Homeowner,\n\n"
                    f"Your job titled '{job_title}' is scheduled at {scheduled_datetime}. "
                    f"Please prepare for the worker's arrival.\n\n"
                    f"Best regards,\n"
                    f"The Professionals Team"
                )


                send_mail(
                    subject,
                    message_worker,
                    settings.DEFAULT_FROM_EMAIL,
                    [worker_email],
                    fail_silently=False,
                )
                send_mail(
                    subject,
                    message_homeowner,
                    settings.DEFAULT_FROM_EMAIL,
                    [homeowner_email],
                    fail_silently=False,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Reminder emails sent for job '{job_title}' to worker ({worker_email}) and homeowner ({homeowner_email})"
                    )
                )

            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Worker with ID {job.is_accepted} does not exist. Skipping job '{job.title}'."
                    )
                )
