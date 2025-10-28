# gee_api/google_auth.py

import requests
import secrets
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .authentication_serializers import EnhancedUserSerializer
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Authenticate user using Google OAuth2 token and return JWT tokens
    """
    # Extract token from request
    id_token_str = request.data.get('id_token')
    
    if not id_token_str:
        return Response({'error': 'Google ID token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # For now, we'll use the tokeninfo endpoint which is simpler
        # Later you can switch to the google-auth library for production
        response = requests.get(
            f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token_str}'
        )
        
        if response.status_code != 200:
            logger.error(f"Google token validation failed: {response.text}")
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)
        
        google_data = response.json()
        
        # Verify the audience (client ID)
        if google_data.get('aud') != settings.GOOGLE_OAUTH2_CLIENT_ID:
            logger.error(f"Invalid audience: {google_data.get('aud')} != {settings.GOOGLE_OAUTH2_CLIENT_ID}")
            return Response({'error': 'Invalid token audience'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Extract user information from Google response
        email = google_data.get('email')
        if not email:
            return Response({'error': 'Email not found in Google token'}, status=status.HTTP_400_BAD_REQUEST)
        
        google_id = google_data.get('sub')
        email_verified = google_data.get('email_verified', 'false').lower() == 'true'
        name = google_data.get('name', '')
        given_name = google_data.get('given_name', '')
        family_name = google_data.get('family_name', '')
        profile_picture = google_data.get('picture', '')
        
        # Only allow verified emails
        if not email_verified:
            return Response({'error': 'Email not verified with Google'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists with this email
        try:
            user = User.objects.get(email=email)
            
        except User.MultipleObjectsReturned:
            # Handle case where there are multiple users with the same email
            logger.warning(f"Multiple users found with email: {email}. Using the first one.")
            user = User.objects.filter(email=email).first()
            
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            base_username = username
            counter = 1
            
            # Ensure username is unique
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=given_name or name.split()[0] if name else '',
                last_name=family_name or ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
            )
            
            # Set a strong random password since they'll login via Google
            user.set_password(secrets.token_urlsafe(32))
            user.save()
            
            # Update the member profile
            if hasattr(user, 'member_profile'):
                user.member_profile.is_google_user = True
                user.member_profile.google_id = google_id
                if profile_picture:
                    user.member_profile.profile_image = profile_picture
                user.member_profile.save()
            
            logger.info(f"New user created via Google: {email}")
        
        # Ensure Member profile exists (create if missing)
        if not hasattr(user, 'member_profile'):
            from .models import Member
            Member.objects.create(user=user)
            
        # Update Google info and user details for existing users
        if hasattr(user, 'member_profile'):
            member = user.member_profile
            member.is_google_user = True
            member.google_id = google_id
            if profile_picture and not member.profile_image:
                member.profile_image = profile_picture
            member.save()
            
            # Update user info if it was empty
            if not user.first_name and given_name:
                user.first_name = given_name
            if not user.last_name and family_name:
                user.last_name = family_name
            user.save()
        
        logger.info(f"User logged in via Google: {email}")
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Add custom claims to tokens
        access_token['email'] = user.email
        access_token['is_google_user'] = user.member_profile.is_google_user if hasattr(user, 'member_profile') else False
        access_token['member_id'] = str(user.member_profile.member_id) if hasattr(user, 'member_profile') else None
        
        # Serialize user data
        user_serializer = EnhancedUserSerializer(user)
        
        # Check if this is a new user (needs profile setup)
        if hasattr(user, 'member_profile'):
            # User is new if they haven't completed profile setup and haven't skipped it
            is_new_user = not (user.member_profile.organization or user.member_profile.bio or user.member_profile.phone) and not user.member_profile.profile_skipped
        else:
            is_new_user = True
        
        return Response({
            'message': 'Google login successful',
            'user': user_serializer.data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(access_token),
            },
            'is_new_user': is_new_user  # Add flag to indicate if profile setup is needed
        }, status=status.HTTP_200_OK)
        
    except requests.RequestException as e:
        logger.error(f"Network error during Google token validation: {str(e)}")
        return Response({'error': 'Network error during authentication'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Unexpected error during Google login: {str(e)}", exc_info=True)
        return Response({'error': 'Authentication failed. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_config(request):
    """
    Return Google OAuth2 client ID for frontend configuration
    """
    client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
    if not client_id:
        logger.error("GOOGLE_OAUTH2_CLIENT_ID not configured in settings")
        return Response({'error': 'Google OAuth not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    return Response({
        'client_id': client_id
    }, status=status.HTTP_200_OK)