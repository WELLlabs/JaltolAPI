# gee_api/authentication_views.py

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .authentication_serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    EnhancedUserSerializer,
    ChangePasswordSerializer
)


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
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
    for field in ['organization', 'bio', 'profile_image']:
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