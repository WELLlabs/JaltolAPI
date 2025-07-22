# gee_api/authentication_serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import Member, Plan, UserPlan

class PlanSerializer(serializers.ModelSerializer):
    """
    Serializer for the Plan model.
    """
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'display_name', 'price', 'currency', 
            'duration_days', 'description', 'features', 'limitations',
            'max_api_calls_per_day', 'max_village_views_per_month', 'max_projects',
            'is_active', 'is_default'
        ]
        read_only_fields = ['id']

class UserPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserPlan model.
    """
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True, required=False)
    is_active = serializers.ReadOnlyField()
    can_make_api_call = serializers.ReadOnlyField()
    can_view_village = serializers.ReadOnlyField()
    
    class Meta:
        model = UserPlan
        fields = [
            'id', 'plan', 'plan_id', 'status', 'start_date', 'end_date',
            'api_calls_today', 'village_views_this_month', 'is_active',
            'can_make_api_call', 'can_view_village', 'next_billing_date'
        ]
        read_only_fields = [
            'id', 'start_date', 'api_calls_today', 'village_views_this_month'
        ]

class MemberSerializer(serializers.ModelSerializer):
    """
    Serializer for the Member model.
    """
    current_plan = PlanSerializer(read_only=True)
    
    class Meta:
        model = Member
        fields = [
            'member_id', 'organization', 'bio', 'profile_image', 'is_google_user',
            'role', 'has_selected_plan', 'phone', 'designation', 'current_plan', 'is_admin'
        ]
        read_only_fields = ['member_id', 'is_google_user', 'current_plan', 'is_admin']

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with extended Member profile data
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all())])
    
    # Optional Member fields
    organization = serializers.CharField(max_length=255, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    designation = serializers.CharField(max_length=100, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'organization', 'bio', 'phone', 'designation')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        # Remove non-User fields
        organization = validated_data.pop('organization', '')
        bio = validated_data.pop('bio', '')
        phone = validated_data.pop('phone', '')
        designation = validated_data.pop('designation', '')
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
        if organization or bio or phone or designation:
            member = user.member_profile
            if organization:
                member.organization = organization
            if bio:
                member.bio = bio
            if phone:
                member.phone = phone
            if designation:
                member.designation = designation
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
    Enhanced serializer for User model with Member profile and plan information
    """
    member_id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    is_google_user = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    has_selected_plan = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    current_plan = serializers.SerializerMethodField()
    user_plan = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'date_joined',
            'member_id', 'organization', 'bio', 'profile_image', 'is_google_user',
            'role', 'has_selected_plan', 'phone', 'designation', 'current_plan',
            'user_plan', 'is_admin'
        )
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
    
    def get_role(self, obj):
        return obj.member_profile.role if hasattr(obj, 'member_profile') else 'user'
    
    def get_has_selected_plan(self, obj):
        return obj.member_profile.has_selected_plan if hasattr(obj, 'member_profile') else False
    
    def get_phone(self, obj):
        return obj.member_profile.phone if hasattr(obj, 'member_profile') else None
    
    def get_designation(self, obj):
        return obj.member_profile.designation if hasattr(obj, 'member_profile') else None
    
    def get_current_plan(self, obj):
        if hasattr(obj, 'member_profile') and obj.member_profile.current_plan:
            return PlanSerializer(obj.member_profile.current_plan).data
        return None
    
    def get_user_plan(self, obj):
        try:
            return UserPlanSerializer(obj.user_plan).data
        except UserPlan.DoesNotExist:
            return None
    
    def get_is_admin(self, obj):
        return obj.member_profile.is_admin if hasattr(obj, 'member_profile') else False


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

class PlanSelectionSerializer(serializers.Serializer):
    """
    Serializer for plan selection/upgrade
    """
    plan_id = serializers.IntegerField()
    
    def validate_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
            return value
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive plan selected.")