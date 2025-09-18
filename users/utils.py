from django.core.mail import EmailMessage


def send_mail(emails, mail_subject, mail_message):
    emailer = EmailMessage(
        mail_subject, mail_message, to= [emails] 
    )
    emailer.send()