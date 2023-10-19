import random, string

def generate_activation_code(): 
    return str(random.randint(100000 , 999999))

def generate_referral_code():
    code = string.ascii_lowercase + string.digits
    return ''.join(random.choice(code) for i in range(6))

def generate_otp():
    return str(random.randint(100000, 999999))