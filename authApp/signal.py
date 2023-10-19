from django.db.models.signals import Signal, post_save
from django.dispatch import receiver
from .models import CustomUser, Wallet

referral_reward_signal = Signal(providing_args=["user", "referred_user"])

@receiver(post_save, sender=CustomUser)
def handle_referral_reward(sender, instance, **kwargs):
    # Check if a referral is happening (referred_by is not None)
    if instance.referred_by:
        referred_user = instance
        referrer = instance.referred_by

        # Perform the logic to determine if the referred user's action triggers a reward
        if referred_user.has_completed_purchase:  # Replace with your condition
            reward_amount = 10.00  # Adjust the reward amount as needed

            # Update the referrer's wallet balance
            referrer_wallet, created = Wallet.objects.get_or_create(user=referrer)
            referrer_wallet.balance += reward_amount
            referrer_wallet.save()

            # Trigger the custom referral reward signal
            referral_reward_signal.send(sender=instance.__class__, user=referrer, referred_user=referred_user)
