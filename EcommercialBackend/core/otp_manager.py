import random
from .models import OTP
from django.contrib.auth import get_user_model

User = get_user_model()

class OTPManager:
    @classmethod
    def generate_otp(cls, email, length=6):
        """Generate a random OTP and save it to the database"""
        # Generate a random OTP code
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        
        try:
            user = User.objects.get(email=email)
            # Create new OTP in database
            OTP.create_otp(user=user, code=otp_code)
            return otp_code
        except User.DoesNotExist:
            return None
    
    @classmethod
    def validate_otp(cls, email, otp_code):
        """Validate an OTP for a given email"""
        try:
            user = User.objects.get(email=email)
            otp = OTP.objects.get(user=user, code=otp_code)
            
            if otp.is_valid():
                # Delete OTP after successful validation
                otp.delete()
                return True
            else:
                # Delete expired OTP
                otp.delete()
                return False
        except (User.DoesNotExist, OTP.DoesNotExist):
            return False