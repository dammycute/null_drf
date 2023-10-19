from celery import shared_task
from django.core.mail import send_mail
from .models import CustomUser

@shared_task
def send_activation_code(user_id, redirect_url):
    user = CustomUser.objects.get(id=user_id)
    subject = "Activate your Account"
    message = f"Use this activation code: {user.activation_code}"
    from_email = "damilolaolawoore03@gmail.com"
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)

@shared_task
def send_activation_msg(email):
    user = CustomUser.objects.filter(email=email).first()
    if user:
        subject = "Account Activation"
        message = f"Your Account has been successfully Activated"
        from_email = "damilolaolawoore03@gmail.com"
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

@shared_task
def send_reset_otp(email, otp):
    user = CustomUser.objects.filter(email=email).first()
    if user:
        subject = "Password Reset Otp"
        message = f"Your OTP is: {otp}"
        from_email = "damilolaolawoore03@gmail.com"
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

@shared_task
def send_reset_msg(email):
    user = CustomUser.objects.filter(email=email).first()
    if user:
        subject = "Password Reset"
        message = f"Your Password has been successfully Reset"
        from_email = "damilolaolawoore03@gmail.com"
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)
        
    

@shared_task
def send_password_msg(email):
    user = CustomUser.objects.filter(email=email).first()
    if user:
        subject = "Change Password"
        message = f"You have sucessfully changed your password"
        from_email = "damilolaolawoore03@gmail.com"
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)