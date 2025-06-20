# gee_api/authentication_serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import Member

class MemberSerializer(serializers.ModelSerializer):
    """
    Serializer for the Member model.
    """
    class Meta:
        model = Member
        fields = ['member_id', 'organization', 'bio', 'profile_image', 'is_google_user']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with enhanced fields
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    # Optional Member profile fields
    organization = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password_confirm', 'email', 'first_name', 
                 'last_name', 'organization', 'bio')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove non-User fields
        organization = validated_data.pop('organization', '')
        bio = validated_data.pop('bio', '')
        validated_data.pop('password_confirm')
        
        # Create User
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # Update Member profile with additional info
        if organization or bio:
            member = user.member_profile
            if organization:
                member.organization = organization
            if bio:
                member.bio = bio
            member.save()
            
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid username or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')


class EnhancedUserSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for user profile that includes Member data
    """
    member_id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    is_google_user = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined',
                 'member_id', 'organization', 'bio', 'profile_image', 'is_google_user')
        read_only_fields = ('id', 'date_joined', 'member_id', 'is_google_user')
    
    def get_member_id(self, obj):
        return str(obj.member_profile.member_id) if hasattr(obj, 'member_profile') else None
    
    def get_organization(self, obj):
        return obj.member_profile.organization if hasattr(obj, 'member_profile') else None
    
    def get_bio(self, obj):
        return obj.member_profile.bio if hasattr(obj, 'member_profile') else None
        
    def get_profile_image(self, obj):
        return obj.member_profile.profile_image if hasattr(obj, 'member_profile') else None
        
    def get_is_google_user(self, obj):
        return obj.member_profile.is_google_user if hasattr(obj, 'member_profile') else False


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs