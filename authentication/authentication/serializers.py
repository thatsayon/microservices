from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user with strong password validation
    and automatic username generation.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text=_("Password must meet complexity requirements.")
    )

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password')

    def validate_email(self, value):
        """
        Ensure email is unique.
        """
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("Email is already in use."))
        return value

    def validate_password(self, value):
        """
        Validate password complexity.
        """
        if len(value) < 8:
            raise serializers.ValidationError(_("Password must be at least 8 characters long."))
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(_("Password must contain at least one uppercase letter."))
        if not any(char.islower() for char in value):
            raise serializers.ValidationError(_("Password must contain at least one lowercase letter."))
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(_("Password must contain at least one digit."))
        if not re.search(r"[!@#$%^&*()_+{}\[\]:;\"'\\|<,>.?/`~-]", value):
            raise serializers.ValidationError(_("Password must contain at least one special character."))

        # Use Django's built-in validators
        validate_password(value)
        return value

    def create(self, validated_data):
        """
        Create a new user with generated username and hashed password.
        """
        full_name = validated_data.get('full_name', '')
        first_name = full_name.split()[0] if full_name else 'user'
        base_username = slugify(first_name) or "user"

        # Ensure unique username
        username = self._generate_unique_username(base_username)

        user = User(
            email=validated_data['email'],
            username=username,
            full_name=validated_data.get('full_name', ''),
            is_active=False
        )
        user.set_password(validated_data['password'])
        user.save()

        return user

    def _generate_unique_username(self, base_username):
        """
        Generate a unique username by appending a random number.

        TODO: have to find another better approach
        """
        for _ in range(100):
            username = f"{base_username}{random.randint(1000, 9999)}"
            if not User.objects.filter(username=username).exists():
                return username
        raise serializers.ValidationError(_("Unable to generate unique username. Please try again."))


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    TODO: have to find is there any better way to do that
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer to generate custom access token and
    add some custom value to the access token
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username  
        token['full_name'] = user.full_name
        token['email'] = user.email

        return token
