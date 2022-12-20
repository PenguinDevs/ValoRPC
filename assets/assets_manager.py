import requests
import json
from os import path

EMPTY_ASSETS = {
   'agents': {},
   'maps': {},
   'map_urls_to_uuid': {},
   'modes': {},
   'mode_path_to_uuid': {}
}

class AssetsManager():
   def __init__(self) -> None:
      self.assets_dir = path.abspath(path.join(path.dirname(__file__), 'val_assets.json')) # 'assets/val_assets.json'

      self.assets = EMPTY_ASSETS
      self.read_assets()

   def read_assets(self) -> dict:
      with open(self.assets_dir, mode='r') as f:
         self.assets = json.load(f)

         return self.assets

   def write_assets(self) -> None:
      with open(self.assets_dir, mode='w') as f:
         json.dump(self.assets, f, indent=4)

   def register_agent(self, data: dict) -> None:
      if not data['isPlayableCharacter']:
         return
      
      new_entry = {}
      new_entry['uuid'] = data['uuid']
      new_entry['name'] = data['displayName']
      new_entry['role'] = data['role']['displayName']

      self.assets['agents'][data['uuid']] = new_entry

   def register_map(self, data: dict) -> None:
      new_entry = {}
      new_entry['uuid'] = data['uuid']
      new_entry['name'] = data['displayName']
      new_entry['url'] = data['mapUrl']

      self.assets['maps'][data['uuid']] = new_entry
      self.assets['map_urls_to_uuid'][new_entry['url']] = data['uuid']

   def register_mode(self, data: dict) -> None:
      new_entry = {}
      new_entry['uuid'] = data['uuid']
      new_entry['name'] = data['displayName']
      new_entry['path'] = data['assetPath']

      if new_entry['name'] == 'PRACTICE':
         new_entry['name'] = 'Shooting Range'

      self.assets['modes'][data['uuid']] = new_entry
      self.assets['mode_path_to_uuid'][new_entry['path']] = data['uuid']

   def bulk_download_all_assets(self) -> bool:
      if self.assets == EMPTY_ASSETS:
         self.read_assets()

      responses = {}

      try:
         def get_response(name, url):
            response = requests.get(url)
            response.raise_for_status()
            
            responses[name] = response

         get_response('agents', 'https://valorant-api.com/v1/agents')
         get_response('maps', 'https://valorant-api.com/v1/maps')
         get_response('modes', 'https://valorant-api.com/v1/gamemodes')

      except requests.exceptions.HTTPError as err:
         raise SystemExit(err)

      for agent in responses['agents'].json()['data']:
         self.register_agent(agent)

      for map in responses['maps'].json()['data']:
         self.register_map(map)

      for mode in responses['modes'].json()['data']:
         self.register_mode(mode)

      self.write_assets()

   def get_asset(self, asset_type: str, key: str) -> any:
      if key is None or key == '':
         return

      if self.assets == EMPTY_ASSETS:
         self.read_assets()
      
      if not key in self.assets[asset_type].keys():
         self.bulk_download_all_assets()

      return self.assets[asset_type][key]

   def get_map_from_url(self, map_url: str) -> any:
      uuid = self.get_asset('map_urls_to_uuid', map_url)
      return uuid, self.get_asset('maps', uuid)

   def get_mode_from_url(self, mode_url: str) -> any:
      uuid = self.get_asset('mode_path_to_uuid', mode_url)
      return uuid, self.get_asset('modes', uuid)
