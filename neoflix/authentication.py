import requests
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import exceptions, status
from rest_framework.authentication import BaseAuthentication
from rest_framework.response import Response

from neoflix.models import UserModel


class KeycloakConnect:
    def __init__(self, server_url, realm_name, client_id, client_secret_key=None):
        self.server_url = server_url
        self.realm_name = realm_name
        self.client_id = client_id
        self.client_secret_key = client_secret_key

        self.well_known_endpoint = self.server_url + "/realms/" + self.realm_name + "/.well-known/openid-configuration"
        self.token_introspection_endpoint = self.server_url + "/realms/" + self.realm_name + "/protocol/openid-connect/token/introspect"
        self.userinfo_endpoint = self.server_url + "/realms/" + self.realm_name + "/protocol/openid-connect/userinfo"
        self.group_info_endpoint = self.server_url + "/admin/master/console/#/realms/" + self.realm_name + "/groups"

    def well_known(self):
        """Lists endpoints and other configuration options
        relevant to the OpenID Connect implementation in Keycloak.

        Returns:
            [type]: [list of keycloak endpoints]
        """
        response = requests.request("GET", self.well_known_endpoint, verify=False)
        return response.json()

    def introspect(self, token, token_type_hint=None):
        """
        Introspection Request token
        Implementation: https://tools.ietf.org/html/rfc7662#section-2.1

        Args:
            token (string):
                REQUIRED. The string value of the token.  For access tokens, this
                is the "access_token" value returned from the token endpoint
                defined in OAuth 2.0 [RFC6749], Section 5.1.  For refresh tokens,
                this is the "refresh_token" value returned from the token endpoint
                as defined in OAuth 2.0 [RFC6749], Section 5.1.  Other token types
                are outside the scope of this specification.
            token_type_hint ([string], optional):
                OPTIONAL.  A hint about the type of the token submitted for
                introspection.  The protected resource MAY pass this parameter to
                help the authorization server optimize the token lookup.  If the
                server is unable to locate the token using the given hint, it MUST
                extend its search across all of its supported token types.  An
                authorization server MAY ignore this parameter, particularly if it
                is able to detect the token type automatically.  Values for this
                field are defined in the "OAuth Token Type Hints" registry defined
                in OAuth Token Revocation [RFC7009].

        Returns:
            json: The introspect token
        """
        payload = {
            "token": token,
            "client_id": self.client_id,
            "client_secret": self.client_secret_key
        }
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'authorization': "Bearer " + token
        }

        response = requests.request("POST", self.token_introspection_endpoint, data=payload, headers=headers, verify=False)
        print(response.text)
        # TODO: check status code first
        return response.json()

    def is_token_active(self, token):
        """Verify if introspect token is active.

        Args:
            token (str): The string value of the token.

        Returns:
            bollean: Token valid (True) or invalid (False)
        """
        introspect_token = self.introspect(token)
        is_active = introspect_token.get('active', None)
        print('is active')
        print(is_active)
        return True if is_active else False

    def userinfo(self, token) -> dict:
        """Get user info from authenticated token

        Args:
            token (str): The string value of the token.

        Returns:
            json: user info data
        """
        headers = {
            'authorization': "Bearer " + token
        }
        response = requests.request("GET", self.userinfo_endpoint, headers=headers, verify=False)
        return response.json()

    def group_info(self, token):
        """Get user info from authenticated token

        Args:
            token (str): The string value of the token.

        Returns:
            json: user info data
        """

        headers = {
            'authorization': "Bearer " + token,
            'first': '0',
            'max': '20'
        }
        response = requests.request("GET", self.group_info_endpoint, headers=headers, verify=False)
        return response.json()


class Neo4jKeycloakAuthentication(BaseAuthentication):

    def __init__(self):
        self.config = settings.KEYCLOAK_CONFIG

        try:
            self.server_url = self.config['KEYCLOAK_SERVER_URL']
            self.realm = self.config['KEYCLOAK_REALM']
            self.client_id = self.config['KEYCLOAK_CLIENT_ID']
            self.client_secret_key = self.config['KEYCLOAK_CLIENT_SECRET_KEY']
            self.group_key = self.config['KEYCLOAK_CLIENT_GROUP_KEY']
        except KeyError as e:
            raise Exception("The mandatory KEYCLOAK configuration variables has not defined.")

        if self.config['KEYCLOAK_SERVER_URL'] is None:
            raise Exception("The mandatory KEYCLOAK_SERVER_URL configuration variables has not defined.")

        if self.config['KEYCLOAK_REALM'] is None:
            raise Exception("The mandatory KEYCLOAK_REALM configuration variables has not defined.")

        if self.config['KEYCLOAK_CLIENT_ID'] is None:
            raise Exception("The mandatory KEYCLOAK_CLIENT_ID configuration variables has not defined.")

        if self.config['KEYCLOAK_CLIENT_SECRET_KEY'] is None:
            raise Exception("The mandatory KEYCLOAK_CLIENT_SECRET_KEY configuration variables has not defined.")

        if self.config['KEYCLOAK_CLIENT_GROUP_KEY'] is None:
            raise Exception("The mandatory KEYCLOAK_CLIENT_GROUP_KEY configuration is wrong.")

        # Create Keycloak instance
        self.keycloak = KeycloakConnect(server_url=self.server_url,
                                        realm_name=self.realm,
                                        client_id=self.client_id,
                                        client_secret_key=self.client_secret_key)

    def authenticate(self, request):
        if 'HTTP_AUTHORIZATION' not in request.META:
            return None, False

        auth_header = request.META.get('HTTP_AUTHORIZATION').split()
        token = auth_header[1] if len(auth_header) == 2 else auth_header[0]

        if not self.keycloak.is_token_active(token):
            return None, False

        userinfo = self.keycloak.userinfo(token)

        if not userinfo.get('email'):
            return None, False

        try:
            user = UserModel.nodes.get(sid=userinfo.get('sub'))
        except Exception as e:
            user = UserModel(sid=userinfo.get('sub'))

        user.name = userinfo.get('preferred_username')
        user.email = userinfo.get('email')
        user.save()

        return user, None
