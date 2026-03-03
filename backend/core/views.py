from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token


@api_view(['GET'])
def health_check(request):
    """
    Endpoint simples para verificar se o backend está funcionando
    """
    return Response({
        'status': 'ok',
        'message': 'ProjectOuvidoria API está funcionando!',
        'version': '0.1.0'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Autenticação: recebe username (e-mail) e password, retorna token e dados do usuário.
    """
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''

    if not username or not password:
        return Response(
            {'detail': 'Informe usuário (e-mail) e senha.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {'detail': 'E-mail ou senha incorretos.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    if not user.is_active:
        return Response(
            {'detail': 'Usuário inativo.'},
            status=status.HTTP_403_FORBIDDEN
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.pk,
            'username': user.username,
            'email': getattr(user, 'email', None) or user.username,
            'full_name': getattr(user, 'full_name', None) or user.get_full_name(),
            'sector': getattr(user, 'sector', None),
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
        }
    }, status=status.HTTP_200_OK)
