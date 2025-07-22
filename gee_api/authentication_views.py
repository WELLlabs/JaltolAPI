# gee_api/authentication_views.py

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from .authentication_serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    EnhancedUserSerializer,
    ChangePasswordSerializer,
    PlanSerializer,
    UserPlanSerializer,
    PlanSelectionSerializer
)
from .models import Plan, UserPlan


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that returns user data along with tokens
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Get user data
            username = request.data.get('username')
            user = User.objects.get(username=username)
            user_serializer = EnhancedUserSerializer(user)
            
            # Add user data to response
            response.data['user'] = user_serializer.data
            
        return response


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user with enhanced profile data
    """
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens for the new user
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Serialize user data with enhanced fields
            user_serializer = EnhancedUserSerializer(user)
            
            return Response({
                'message': 'User registered successfully',
                'user': user_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user and return tokens with enhanced user data
    """
    if request.method == 'POST':
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Serialize user data with enhanced fields
            user_serializer = EnhancedUserSerializer(user)
            
            return Response({
                'message': 'Login successful',
                'user': user_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user by blacklisting the refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile with enhanced data
    """
    serializer = EnhancedUserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update user profile including Member fields
    """
    user = request.user
    
    # Extract Member profile fields
    member_data = {}
    for field in ['organization', 'bio', 'profile_image', 'phone', 'designation']:
        if field in request.data:
            member_data[field] = request.data.pop(field, None)
    
    # Update User model fields
    serializer = EnhancedUserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        # Update Member profile if there are Member fields
        if member_data:
            member = user.member_profile
            for field, value in member_data.items():
                setattr(member, field, value)
            member.save()
        
        # Get updated user data
        updated_serializer = EnhancedUserSerializer(user)
        
        return Response({
            'message': 'Profile updated successfully',
            'user': updated_serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Plan Management Views

@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_plans(request):
    """
    Get all available/active plans
    """
    plans = Plan.objects.filter(is_active=True).order_by('name')
    serializer = PlanSerializer(plans, many=True)
    return Response({
        'success': True,
        'plans': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_plan(request):
    """
    Get current user's plan information
    """
    try:
        user_plan = UserPlan.objects.get(user=request.user)
        serializer = UserPlanSerializer(user_plan)
        return Response({
            'success': True,
            'user_plan': serializer.data
        }, status=status.HTTP_200_OK)
    except UserPlan.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No plan assigned to user'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_plan(request):
    """
    Select or upgrade user plan
    """
    serializer = PlanSelectionSerializer(data=request.data)
    if serializer.is_valid():
        plan_id = serializer.validated_data['plan_id']
        plan = Plan.objects.get(id=plan_id)
        user = request.user
        
        # Get or create user plan
        user_plan, created = UserPlan.objects.get_or_create(
            user=user,
            defaults={'plan': plan}
        )
        
        if not created:
            # Update existing plan
            user_plan.plan = plan
            user_plan.status = 'active'
            user_plan.start_date = timezone.now()
            
            # Set end date for time-limited plans
            if plan.duration_days:
                user_plan.end_date = timezone.now() + timezone.timedelta(days=plan.duration_days)
            else:
                user_plan.end_date = None  # Lifetime/enterprise plans
                
            user_plan.save()
        
        # Mark that user has selected a plan
        member = user.member_profile
        member.has_selected_plan = True
        member.save()
        
        # Return updated user data
        user_serializer = EnhancedUserSerializer(user)
        
        return Response({
            'success': True,
            'message': f'Successfully selected {plan.display_name} plan',
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_plan(request):
    """
    Change/upgrade user's current plan
    """
    serializer = PlanSelectionSerializer(data=request.data)
    if serializer.is_valid():
        plan_id = serializer.validated_data['plan_id']
        new_plan = Plan.objects.get(id=plan_id)
        user = request.user
        
        try:
            user_plan = UserPlan.objects.get(user=user)
            old_plan = user_plan.plan
            
            # Update plan
            user_plan.plan = new_plan
            user_plan.status = 'active'
            user_plan.start_date = timezone.now()
            
            # Set end date for time-limited plans
            if new_plan.duration_days:
                user_plan.end_date = timezone.now() + timezone.timedelta(days=new_plan.duration_days)
            else:
                user_plan.end_date = None
                
            # Reset usage counters
            user_plan.api_calls_today = 0
            user_plan.village_views_this_month = 0
            user_plan.last_api_call_date = None
            user_plan.last_village_view_date = None
            
            user_plan.save()
            
            # Return updated user data
            user_serializer = EnhancedUserSerializer(user)
            
            return Response({
                'success': True,
                'message': f'Successfully upgraded from {old_plan.display_name} to {new_plan.display_name}',
                'user': user_serializer.data
            }, status=status.HTTP_200_OK)
            
        except UserPlan.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No existing plan found. Use select_plan endpoint instead.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_plan_requirements(request):
    """
    Check if user needs to select a plan (for first-time login popup)
    """
    user = request.user
    member = user.member_profile
    
    needs_plan_selection = not member.has_selected_plan
    
    try:
        user_plan = UserPlan.objects.get(user=user)
        has_active_plan = user_plan.is_active
    except UserPlan.DoesNotExist:
        has_active_plan = False
        needs_plan_selection = True
    
    return Response({
        'success': True,
        'needs_plan_selection': needs_plan_selection,
        'has_active_plan': has_active_plan,
        'is_first_login': needs_plan_selection and not member.has_selected_plan
    }, status=status.HTTP_200_OK)