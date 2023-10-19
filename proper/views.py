from django.shortcuts import render
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied
from .serializers import *
import uuid
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.views.generic.edit import CreateAPIView
import datetime
from dateutil.relativedelta import relativedelta
from rest_framework import exceptions
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.generics import get_object_or_404
from rest_framework import status
from django.urls import reverse
from rest_framework.parsers import MultiPartParser, FormParser
from celery import shared_task
from django.http import JsonResponse
from .models import *
from django.db.models import Sum
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

# Create your views here.

class IsOwnerOfObject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


# Dashboard View: you'll be able to get the wallet balance 
# and the total amount of user's investment

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        wallet = Wallet.objects.filter(user=request.user).first()
        investments = Investment.objects.filter(user=request.user).aggregate(total_amount=Sum('current_value'))['total_amount']

        data = {
            'wallet_balance': wallet.balance if wallet else None,
            'investment': investments,
        }

        return Response(data)

# View for admin only, this is where the admin upload the properties

class CreatePropertyView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        serializer.save()

class UpdatePropertyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser, IsOwnerOfObject]
    
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    lookup_field = 'id'

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_staff or serializer.instance.owner == user:
            serializer.save(owner=user)
        else:
            raise PermissionDenied(detail="You do not have permission to update this property.")


#  User will be able to see all available investments
class PropertyListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Property.objects.all()
    serializer_class = PropertySerializer

    def get_serializer_context(self):
        return {'request': self.request}
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        for property_data in response.data:
            url = reverse('property-detail', args=[property_data['id']])
            full_url = request.build_absolute_uri(url)
            property_data['url'] = full_url
        return response

# Check the detail of each properties
class PropertyDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    lookup_field = 'pk'

# 

@shared_task
def update_investment_value(investment_id):
    investment = Investment.objects.get(pk=investment_id)
    today = datetime.date.today()
    elapsed_months = (today.year - investment.start_date.year) * 12 + (today.month - investment.start_date.month)
    investment.current_value = investment.total_price * (1 + ((investment.roi / 12) / 100) * elapsed_months)
    investment.save()


# ======= Buy View ==========



class Buy(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Investment.objects.select_related('product').all()
    serializer_class = InvestmentSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            product_id = kwargs['product_id']  # Get the product ID from the URL
            product = Property.objects.get(pk=product_id)
            slots = int(request.data.get('slots'))
            if slots <= 0:
                raise ValidationError({'slots': 'Slots must be greater than zero'})
            
            if product.slots_available < slots:
                raise ValidationError({slots: f'Only {product.slots_available} slots available'})
            product.slots_available -= slots
            product.save()

            total_price = product.price_per_slot * slots
            roi = product.roi
            
            wallet = Wallet.objects.select_for_update().get(user=self.request.user)
            if wallet.balance < total_price:
                raise ValidationError({'wallet': 'Insufficient funds'})
            wallet.balance -= total_price
            wallet.save()

            investment = Investment.objects.create(
                user=self.request.user,
                product=product,
                slots=slots,
                start_date=datetime.date.today(),
                end_date=datetime.date.today() + relativedelta(months=product.duration),
            )
            today = datetime.date.today()
            investment.total_price = total_price
            investment.roi = roi
            elapsed_months = (today.year - investment.start_date.year) * 12 + (today.month - investment.start_date.month)
            investment.current_value = total_price * (1 + ((roi / 12) / 100) * elapsed_months)
            investment.save()

            

            result = {
                'product': product.property_name,
                'amount': investment.current_value,
                'slots': slots,
                'investment_id': investment.id,
                'message': f"You've purchased {slots} slot(s) of {product.property_name} successfully",
            }

            if product.slots_available == 0:
                result['message'] = f"All {product.property_name} slots have been sold"
            else:
                result['message'] = f"You've purchased {slots} slot(s) of {product.property_name} successfully"

            # Trigger Celery task to update current value each month
            # update_investment_value.apply_async(args=[investment.id], eta=investment.end_date.replace(day=1))
            return Response(result, status=status.HTTP_201_CREATED)
        except Property.DoesNotExist:
            raise ValidationError({'property': 'Invalid property id'})
        # except Wallet.DoesNotExist:
        #     raise ValidationError({'wallet': 'Wallet not found for the user'})
        except Exception as e:
            return Response({'error': str(e)}, status= status.HTTP_400_BAD_REQUEST)

    # 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 git===>        

# ======== Sell Endpoint=========

class Sell(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, investment_id):
        try:
            investment = Investment.objects.select_related('product').get(pk=investment_id)
            seller = investment.user
            buyer_id = request.data.get('buyer')
            buyer = CustomUser.objects.get(pk=buyer_id)
            if seller == buyer:
                raise ValidationError({'buyer': 'You cannot sell to yourself'})

            price = investment.total_price

            # check if buyer has enough funds in their wallet
            buyer_wallet = Wallet.objects.filter(user=buyer).first()
            if not buyer_wallet or buyer_wallet.balance < price:
                raise ValidationError({'buyer': 'Insufficient funds to buy investment'})

            with transaction.atomic():
                # deduct amount from buyer's wallet
                buyer_wallet.balance -= price
                buyer_wallet.save()

                # credit amount to seller's wallet
                seller_wallet = Wallet.objects.filter(user=seller).first()
                if not seller_wallet:
                    seller_wallet = Wallet.objects.create(user=seller, balance=0)
                seller_wallet.balance += price
                seller_wallet.save()

                # create a new Investment object for the buyer
                new_investment = Investment.objects.create(
                    user=buyer,
                    product=investment.product,
                    slots=investment.slots,
                    start_date=investment.start_date,
                    end_date=investment.end_date,
                    total_price=investment.total_price,
                    roi=investment.roi
                )

                # Trigger Celery task to update current value each month for new investment
                update_investment_value.apply_async(args=[new_investment.id], eta=new_investment.end_date.replace(day=1))

                # delete the original investment
                investment.delete()

            return Response({'message': 'Investment sold successfully'}, status=status.HTTP_200_OK)
        except Investment.DoesNotExist:
            raise ValidationError({'investment': 'Invalid investment id'})
        # except CustomUser.DoesNotExist:
        #     raise ValidationError({'buyer': 'Invalid buyer id'})
        except Exception as e:
            raise ValidationError({'error': str(e)})




# ==================== This is the Endpoint that list out the investment of the user===========

class InvestmentListView(generics.ListAPIView):
    queryset = Investment.objects.all()
    serializer_class = InvestmentSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

# ==========================Flutterwave Payment Endpoint====================




from django.shortcuts import redirect
from django.db import transaction
import uuid
import requests
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from .serializers import TransactionSerializer
from .models import *
from django.contrib.auth import get_user_model

class FlutterwavePaymentLink(CreateAPIView):
    serializer_class = TransactionSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the Transaction object to the database with a 
        User = request.user
        customer = CustomerDetails.objects.get(user=request.user)
        wallet = Wallet.objects.get(user=request.user)
        transaction = Transaction.objects.create(
            user=User,
            customer=customer,
            amount=serializer.validated_data['amount'],
            status=Transaction.PENDING,
            tx_ref=uuid.uuid4().hex,
            wallet=wallet
        )
        tx_ref = transaction.tx_ref

        amount = serializer.validated_data['amount']
        if not amount:
            return Response({"error": "Amount not provided"}, status=400)

        url = "https://api.flutterwave.com/v3/payments"
        headers = {
            "Authorization": f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
            "Content-Type": "application/json"
        }

        # name =  

        payload = {
            "tx_ref": tx_ref,
            "amount": str(amount),
            "currency": "NGN",
            "redirect_url": "http://htcode12.pythonanywhere.com/",
            "payment_options": "card, ussd, banktransfer",
            "meta": {
                "consumer_id": request.user.id,
                "consumer_mac": "92a3-912ba-1192a"
            },
            "customer": {
                "email": request.user.email,
                "name": customer.first_name + " " + customer.last_name,
            },
            "customizations": {
                "title": "RealOwn",
                "description": "Payment for RealOwn",
                "logo": "https://drive.google.com/file/d/1dIWGQYH3ayKiG_xUw-JQuXSt2cfuu4HF/view?usp=drivesdk"
            },
            "bank_transfer_options": {
                "expires": 3600
            },
            # "callback_url": request.build_absolute_uri(reverse('webhook'))
        }

        # Make a request to Flutterwave's API to create the payment link
        response = requests.post(url, headers=headers, json=payload)

        try:
            payment_url = response.json()["data"]["link"]
        except (ValueError, KeyError):
            # Update the transaction status to failed if the payment link cannot be generated
            transaction.status = Transaction.FAILED
            transaction.save()
            return Response({"error": "An error occurred while processing your request. Please try again later."}, status=500)

        # Redirect the user to the payment URL
        return Response (payment_url + f"?amount={amount}")



# Webhook View


import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from decouple import config



@method_decorator(csrf_exempt, name='dispatch')
class Webhook(APIView):
    permission_classes=[AllowAny,]

    def post(self, request, format=None):
        jsondata = request.body
        data = json.loads(jsondata)
        print(data)

        if data['event'] == 'charge.completed':
            # Handle successful charge event
            amount = data['data']['amount']
            currency = data['data']['currency']
            tx_ref = data['data']['tx_ref']
            customer_name = data['data']['customer']['name']
            customer_email = data['data']['customer']['email']
            payment_method = data['data']['payment_type']

            try:
                # Find the transaction with the given tx_ref
                transaction = Transaction.objects.get(tx_ref=tx_ref)
            except Transaction.DoesNotExist:
                # This transaction doesn't exist in our database; ignore the event
                return Response(status=status.HTTP_200_OK)

            # Update the transaction status
            transaction.status = Transaction.COMPLETED
            transaction.payment_type = payment_method
            transaction.save()

            # Add the transaction amount to the user's wallet balance
            try:
                wallet = Wallet.objects.get(user=transaction.user)
            except Wallet.DoesNotExist:
                # The user doesn't have a wallet; ignore the event
                return Response(status=status.HTTP_200_OK)

            wallet.balance += amount
            wallet.save()

            

        elif data['event'] == 'charge.failed':
            # Handle failed charge event
            amount = data['data']['amount']
            currency = data['data']['currency']
            tx_ref = data['data']['tx_ref']
            customer_name = data['data']['customer']['name']
            customer_email = data['data']['customer']['email']

            try:
                # Find the transaction with the given tx_ref
                transaction = Transaction.objects.get(tx_ref=tx_ref)
            except Transaction.DoesNotExist:
                # This transaction doesn't exist in our database; ignore the event
                return Response(status=status.HTTP_200_OK)

            # Update the transaction status
            transaction.status = Transaction.FAILED
            transaction.save()

            return Response(f'Payment failed: {amount} {currency} from {customer_name} ({customer_email}) with transaction reference {tx_ref}')

        else:
            # Ignore other events
            pass

        return Response(data, status=status.HTTP_200_OK)


# ========= Activity Endpoint ========
class ActivityEndpoint(APIView):
    def get(self, request, format=None):
        try:
            user = request.user
            fund_wallet = Transaction.objects.filter(user=user)
            buy_property = Investment.objects.filter(user=user)
            transaction_details = []

            for transaction in fund_wallet:
                transaction_details.append({
                    'transaction_type' : "Wallet Funding",
                    'amount' : transaction.amount,
                    'transaction_reference' : transaction.tx_ref,
                    'payment_type' : transaction.payment_type,
                    'receiver' : transaction.customer.first_name + ' ' + transaction.customer.last_name,
                    'timestamp' : transaction.timestamp,
                })
            
            for transaction in buy_property:
                transaction_details.append({
                    'transaction_type' : "Purchase of Property",
                    'amount' : transaction.current_value,
                    'transaction_reference' : transaction.id,
                    'slots_numbers' : transaction.slots,
                    'start_date' : transaction.start_date,
                    'end_date' : transaction.end_date,
                    'product' : transaction.product.property_name
                    
                })

            return Response({'transaction_detail': transaction_details})
        except Exception as e:
            return Response({'error': str(e)}, status= status.HTTP_400_BAD_REQUEST)



        



import requests
from rest_framework import generics, status
from rest_framework.response import Response



class WithdrawToBankAPIView(generics.CreateAPIView):
    serializer_class = BankAccountSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bank_account = serializer.validated_data

        # Get bank code from Flutterwave API using bank name
        bank_name = bank_account['bank']
        response = requests.get(f'https://api.flutterwave.com/v3/banks',
                                headers={'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}'})
        if response.status_code != 200:
            return Response({'message': 'Unable to get bank code.'}, status=status.HTTP_400_BAD_REQUEST)

        bank_data = response.json()['data'][0]
        bank_account['bank_code'] = bank_data['code']

        # Verify account name using Flutterwave API
        account_number = bank_account['account_number']
        response = requests.get(f'https://api.flutterwave.com/v3/accounts/resolve'
                                f'account_bank={bank_data["code"]}',
                                headers={'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}'})
        if response.status_code != 200:
            return Response({'message': 'Unable to verify account name.'}, status=status.HTTP_400_BAD_REQUEST)

        account_data = response.json()['data']
        account_name = account_data['account_name']

        if account_name.lower() != bank_account['account_name'].lower():
            return Response({'message': 'Account name does not match.'}, status=status.HTTP_400_BAD_REQUEST)

        # Deduct transfer amount from user wallet
        user = self.request.user
        wallet = Wallet.objects.get(user=user)
        transfer_amount = bank_account['amount']
        if wallet.balance < transfer_amount:
            return Response({'message': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

        wallet.balance -= transfer_amount
        wallet.save()

        # Initiate transfer to user bank account using Flutterwave API
        payload = {
            "account_bank": bank_account['bank_code'],
            "account_number": account_number,
            "amount": transfer_amount,
            "narration": "Wallet withdrawal to bank account",
            "currency": "NGN",
            "reference": f"wallet_to_bank_{user.id}"
        }

        response = requests.post('https://api.flutterwave.com/v3/transfers', json=payload,
                                 headers={'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}'})
        if response.status_code == 200:
            return Response({'message': 'Transfer successful.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Unable to initiate transfer.'}, status=status.HTTP_400_BAD_REQUEST)


