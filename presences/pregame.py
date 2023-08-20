import time
import logging

logger = logging.getLogger(__name__)

from .presence import BasePresence

from riot_client.exceptions import PhaseError

class PregamePresence(BasePresence):
   def __init__(self, vrpc_client) -> None:
      self.vrpc_client = vrpc_client

   def start_with_event_data(self, event_data: dict) -> None:
      match_id = super()._get_match_id_from_chat_event(event_data, 'pregame')
      if match_id:
         self.start_with_match_id(match_id)

   def start_with_match_id(self, match_id: str = None) -> None:
      try:
         match_details = self.vrpc_client.riot_client.pregame_fetch_match(match_id)
      except PhaseError:
         return

      if not match_details:
         return

      self._register_match_id(match_details['ID'], 'pregame')
      logger.info('CONTINUING PRE MATCH %s', match_id)
      
      self.__loop(match_id)

   def __loop(self, match_id: str) -> None:
      self.start = int(time.time())

      while True:
         try:
            match_details = self.vrpc_client.riot_client.pregame_fetch_match(match_id)
         except PhaseError:
            break

         status = {}

         local_player = None
         locked_count = 0
         ally_count = 0
         for player in match_details['AllyTeam']['Players']:
            ally_count += 1
            if player['CharacterSelectionState'] == 'locked':
               locked_count += 1
            
            if player['Subject'] == self.vrpc_client.riot_client.puuid:
               local_player = player
         
         if not local_player:
            time.sleep(1)
            continue

         _, mode = self.vrpc_client.assets_manager.get_mode_from_url(match_details['Mode'])
         mode = mode['name']
         game_type = mode
         if not match_details['ProvisioningFlowID'] == 'CustomGame' and mode == 'Standard':
            if match_details['QueueID'] == 'competitive':
               game_type = 'Competitive'
            elif match_details['QueueID'] == 'unrated':
               game_type = 'Unrated'
         provisioning = match_details['ProvisioningFlowID'] == 'CustomGame' and 'Custom ' or ''
         state = local_player['CharacterSelectionState'] == 'locked' and 'Locked in' or 'Selecting'
         agent = self.vrpc_client.assets_manager.get_asset('agents', local_player['CharacterID'])
         map_uuid, map = self.vrpc_client.assets_manager.get_map_from_url(match_details['MapID'])
         party_info = self.get_party_info()

         status['start'] = self.start
         status['end'] = self.start + 90
         status['details'] = f'Agent Select {provisioning}{game_type}'
         if agent:
            status['state'] = f'{map["name"]} | {state} {agent["name"]} | In Party'
            status['small_text'] = agent['name']
            status['small_image'] = local_player['CharacterID']
         else:
            status['state'] = f'{map["name"]} | {state}'
         status['party_size'] = party_info
         status['large_image'] = map_uuid
         status['large_text'] = map['name']

         self.vrpc_client.presence.update(status)

         time.sleep(5)
