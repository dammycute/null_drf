from django.shortcuts import render
from .serializers import *
from .utils import *
from .tasks import *
# from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
import logging
logger = logging.getLogger('password_change_logger')
from django_ratelimit.decorators import ratelimit
from rest_framework.permissions import  AllowAny


# Create your views here.
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from .models import CustomUser



class UserRegistrationView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    # @transaction.atomic
    def perform_create(self, serializer):
        user = serializer.save()
        user.activation_code = generate_activation_code()
        user.referral_code = generate_referral_code()
        user.save()

        #Check if a referrer's code was provided during registration
        referrer_code = serializer.validated_data.get('referrer_code')
        if referrer_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referrer_code)
                user.reffered_by = referrer
                user.save()

            #Reward the referrer everytime a person is referred by him/her
                reward_amount = Decimal(1000.00)
                referrer.referral_balance = Decimal(str(referrer.referral_balance))
                referrer.referral_balance += reward_amount
                referrer.referral_count += 1
                referrer.save()
            except CustomUser.DoesNotExist:
                pass

        redirect_url = reverse('activate', kwargs={'pk':user.id})

        print(f"Activate url: {redirect_url}")

        send_activation_code(user.id, redirect_url)
        return Response({"message": "Account Successfully Created"})
    

class ActivateAccountView(generics.UpdateAPIView):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = ActivationSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        activation_code = request.data.get('activation_code')
        user = self.get_object()

        if user.activation_code == activation_code:
            user.activation_code = ''
            user.is_active = True
            user.save()
            send_activation_msg(email=user.email)
            return Response({"message": "Account Activated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid activation code"}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(request, username=email, password=password)

            if user:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                return Response({"access_token": access_token})
            else:
                return Response({"error": "Invalid credentials."}, status=400)
        else:
            return Response(serializer.errors, status=400)


class SendOtpView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetOtpModelSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            
            email = serializer.validated_data['email']
            #Check if email provided exists in the database
            user = CustomUser.objects.filter(email=email).first()
            if user:
                #Generate and Send Otp
                otp = generate_otp()

                send_reset_otp(email, otp)

                otp_record, created = OtpModel.objects.get_or_create(user=user, defaults={'otp': otp})
                if not created:
                    otp_record.otp = otp
                    otp_record.save()
                return Response({"message": "OTP sent successfully."})
            else:
                return Response({"error": "User not found."}, status=400)
        else:
            return Response(serializer.errors, status=400)


class ConfirmOtpView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = ConfirmOtpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            otp_value = serializer.validated_data['otp']
            
            # Find the OTP record associated with the provided OTP value
            otp_record = OtpModel.objects.filter(otp=otp_value).first()

            if otp_record:
                user = otp_record.user

                if user:
                    # Check if the OTP is expired
                    current_time = timezone.now()
                    if otp_record.otp_expire and otp_record.otp_expire < current_time:
                        return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

                    new_password = serializer.validated_data['new_password']

                    # Delete the OTP record associated with this user
                    otp_record.delete()

                    if user.check_password(new_password):
                        return Response({"error": "New password matches the current password."}, status=status.HTTP_400_BAD_REQUEST)
                    elif len(new_password) < 8:
                        return Response({"message": "Password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        user.set_password(new_password)
                        user.save()

                        send_reset_msg(email=user.email)
                        return Response({"message": "Password successfully changed."})
                else:
                    return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(generics.CreateAPIView):
    serializer_class = ResetPasswordSerializer

    # @ratelimit(key='ip', rate='5/m', block=True)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            user = self.request.user  # Assuming the user is authenticated

            # Edge Case 1: Check if the old password is correct
            if not user.check_password(old_password):
                return Response({"message": "Invalid old password."}, status=status.HTTP_400_BAD_REQUEST)

            # Edge Case 2: Check if the old password is not the same as the new password
            if old_password == new_password:
                return Response({"message": "Old password is the same as the new one."}, status=status.HTTP_400_BAD_REQUEST)

            # Edge Case 3: Handle password complexity rules if needed
            # password complexity validation logic here
            if len(new_password) < 8:
                return Response({"message": "Password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            # Change the user's password
            user.set_password(new_password)
            user.save()

            send_password_msg(email = user.email)

            # Edge Case 4: You may log password changes and implement rate limiting here
            logger.info(f"Password changed for user {user.email}")
            return Response({"message": "Password changed successfully."})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
