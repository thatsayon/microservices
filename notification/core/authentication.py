# your_app/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class SimpleUser:
    """
    A simple user object that doesn't require database lookup
    """
    def __init__(self, user_id):
        self.id = user_id
        self.pk = user_id
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def __str__(self):
        return f"User {self.id}"

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Returns a stateless user object from the token without database lookup
        """
        try:
            user_id = validated_token.get('user_id')
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')
        
        return SimpleUser(user_id)
