import requests
import aiohttp
import re
import logging

logger = logging.getLogger(__name__)

class Auth:

    def __init__(self,auth):
        self.username = auth['username']
        self.password = auth['password']

    def authenticate(self):
        session = requests.session()
        data = {
            'client_id': 'play-valorant-web-prod',
            'nonce': '1',
            'redirect_uri': 'https://playvalorant.com/opt_in',
            'response_type': 'token id_token',
        }
        r = session.post('https://auth.riotgames.com/api/v1/authorization', json=data)

        data = {
            'type': 'auth',
            'username': self.username,
            'password': self.password
        }
        r = session.put('https://auth.riotgames.com/api/v1/authorization', json=data)
        pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
        data = pattern.findall(r.json()['response']['parameters']['uri'])[0] 
        access_token = data[0]

        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        r = session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={})
        entitlements_token = r.json()['entitlements_token']

        r = session.post('https://auth.riotgames.com/userinfo', headers=headers, json={})
        user_id = r.json()['sub']
        headers['X-Riot-Entitlements-JWT'] = entitlements_token
        session.close()
        return user_id, headers, {}

    async def ASYNCauthenticate(self):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        # session = requests.session()
            headers = {
                "User-Agent": "RiotClient/43.0.1.4195386.4190634 rso-auth (Windows;10;;Professional, x64)",
            }
            data = {
                'client_id': 'play-valorant-web-prod',
                'nonce': '1',
                'redirect_uri': 'https://playvalorant.com/opt_in',
                'response_type': 'token id_token',
            }
            r = await session.post('https://auth.riotgames.com/api/v1/authorization', json=data, headers=headers)
            data = {
                'type': 'auth',
                'username': self.username,
                'password': self.password
            }
            r = await session.put('https://auth.riotgames.com/api/v1/authorization', json=data, headers=headers)
            pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
            responseJson = await r.json()
            data = pattern.findall(responseJson['response']['parameters']['uri'])[0]
                    # data = pattern.findall("https://account.riotgames.com/oauth2/log-in?code=dXcxOmNVNW93V3IzeGIwVU55N0lCUGlXNlEucGdJYmU2SXhqYkRSd05XaTBGQ2hFdw%3D%3D&iss=https%3A%2F%2Fauth.riotgames.com&state=1f516289-fe1c-4a1d-b136-66c72431711d&session_state=f_hKDUt01KM9v4B7X9cOsv1jpVO1vVfJIb964V1CGZw.yle7bc0IAx-FUTdxJv39wQ")[0]
            access_token = data[0]
            headers = {
                "User-Agent": "RiotClient/43.0.1.4195386.4190634 rso-auth (Windows;10;;Professional, x64)",
                'Authorization': f'Bearer {access_token}',
            }
            r = await session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={})
            entitlements_token = (await r.json())['entitlements_token']
            
            r = await session.post('https://auth.riotgames.com/userinfo', headers=headers, json={})
            user_id = (await r.json())['sub']
            headers['X-Riot-Entitlements-JWT'] = entitlements_token
            await session.close()
            return user_id, headers, {}