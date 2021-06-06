import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import requests
import pprint as pp
import json

# access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
# secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
# server_url = os.environ['UPBIT_OPEN_API_SERVER_URL']

access_key = "oKkffgWyKg3EJI7U3o8gfS430nxvdsKTBIGMPzhJ"
secret_key = "bqnka7H5f5S5x7CpZl2oYPeqFy3xGguyYCxxCG7G"
server_url = "https://api.upbit.com"


def upbit_authenticate(payload, secret_key):
    jwt_token = jwt.encode(payload, secret_key)
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}
    return headers