# gee_api/google_auth.py

import requests
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .authentication_serializers import EnhancedUserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Authenticate user using Google token and return JWT tokens
    """
    # Extract token from request
    id_token = request.data.get('id_token')
    
    if not id_token:
        return Response({'error': 'Google ID token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verify the token with Google
        response = requests.get(f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}')
        if not response.ok:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)
        
        google_data = response.json()
        
        # Extract user information from Google response
        email = google_data.get('email')
        if not email:
            return Response({'error': 'Email not found in Google token'}, status=status.HTTP_400_BAD_REQUEST)
        
        google_id = google_data.get('sub')
        name_parts = google_data.get('name', '').split(' ')
        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        profile_picture = google_data.get('picture', '')
        
        # Check if user exists with this email
        try:
            user = User.objects.get(email=email)
            # Update Google info if needed
            if hasattr(user, 'member_profile'):
                user.member_profile.is_google_user = True
                user.member_profile.google_id = google_id
                if profile_picture:
                    user.member_profile.profile_image = profile_picture
                user.member_profile.save()
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
                first_name=first_name,
                last_name=last_name
            )
            
            # Set a random password since they'll login via Google
            user.set_password(User.objects.make_random_password())
            user.save()
            
            # Update the member profile
            user.member_profile.is_google_user = True
            user.member_profile.google_id = google_id
            if profile_picture:
                user.member_profile.profile_image = profile_picture
            user.member_profile.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Serialize user data
        user_serializer = EnhancedUserSerializer(user)
        
        return Response({
            'message': 'Google login successful',
            'user': user_serializer.data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(access_token),
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)