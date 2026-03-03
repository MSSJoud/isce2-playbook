#!/usr/bin/env python3
"""Test Copernicus Dataspace authentication"""
import os
import requests

USERNAME = os.getenv("COPERNICUS_USER")
PASSWORD = os.getenv("COPERNICUS_PASSWORD")

print(f"Testing authentication for user: {USERNAME}")

# Get OAuth2 token
token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
data = {
    "client_id": "cdse-public",
    "username": USERNAME,
    "password": PASSWORD,
    "grant_type": "password"
}

try:
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        print("✅ Authentication successful!")
        token_data = response.json()
        print(f"Access token received (expires in {token_data.get('expires_in')} seconds)")
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
