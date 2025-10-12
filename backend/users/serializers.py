from rest_framework import serializers
from .models import CustomUser
from utils.validators import validate_e164_phone

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','username','email','first_name','last_name','phone_number','role']
        read_only_fields = ['id','username','email']  # role is now writable

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id','username','email','password','first_name', 'last_name', 'password_confirm','role','phone_number']
        read_only_fields = ['id']  # role is now writable

    def validate_phone_number(self, value):
        # Use the validator, but also normalize & return
        normalized = validate_e164_phone(value)
        return normalized

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm':'Passwords do not match'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        role = validated_data.pop('role', 'customer')  # default fallback
        user = CustomUser(**validated_data)
        user.role = role
        user.set_password(password)
        user.save()
        return user

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name','last_name','phone_number']
