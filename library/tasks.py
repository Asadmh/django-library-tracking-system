from celery import shared_task
from .models import Loan
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass


@shared_task
def check_overdue_loans():
    # Task to check overdue loans
    loans = Loan.objects.filter(is_returned=False, due_date__lt=timezone.now().date()).select_related('member', 'book')

    for loan in loans:
        member = loan.member
        book = loan.book

        send_mail(
            subject=f'{book.title} Overdue Reminder',
            message=f'Hello {member.user.username}, The book {book.title} is overdue. Please return it as soon as possible.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member.user.email],
            fail_silently=False,
        )
