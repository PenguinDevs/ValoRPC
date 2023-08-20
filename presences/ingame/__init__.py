import time
import typing as t
import logging

logger = logging.getLogger(__name__)

from ..presence import BasePresence

from riot_client.exceptions import PhaseError

class IngamePresence(BasePresence):
   def __init__(self, vrpc_client) -> None:
      self.vrpc_client = vrpc_client

      self.match_details_last_fetched = time.time()
      self.match_info = {}
      self.started = None

   def start_with_event_data(self, event_data: dict) -> None:
      match_id = super()._get_match_id_from_chat_event(event_data, 'ingame')
      if match_id:
         self.start_with_match_id(match_id)

   def start_with_match_id(self, match_id: str = None) -> None:
      try:
         match_details = self.vrpc_client.riot_client.coregame_fetch_match(match_id)
      except PhaseError:
         return

      if not match_details:
         return

      self._register_match_id(match_details['MatchID'], 'ingame')
      logger.info('CONTINUING CORE MATCH %s', match_id)

      _, mode = self.vrpc_client.assets_manager.get_mode_from_url(match_details['ModeID'])
      self.__loop(match_details['MatchID'], mode['name'])

   def update_standard_presence(self, results: t.Tuple[t.Tuple[int, int], t.Tuple[int, int], str]) -> None:
      scores, times, state = results
      b_score, r_score = scores
      start, end = times

      status = {}

      if state == 'in progress':
         state = 'Round in Progress'
      elif state == 'buy phase' or state == 'match point' or state == 'overtime' or state == 'endgame':
         state = 'Buy Phase'
      elif state == 'round won' or state == 'round lost' or state == 'clutch':
         state = 'Round Intermission'
      elif state == 'spike planted':
         state = 'Spike Planted'

      party_info = self.get_party_info()

      status['details'] = f'Playing {self.match_info["provisioning"]}{self.match_info["game_type"]} | {self.match_info["agent"]["name"]} | {self.match_info["map"]["name"]}'
      status['state'] = f'{b_score} - {r_score} | {state} | In Party'
      status['large_image'] = self.match_info['map_uuid']
      status['large_text'] = self.match_info['map']['name']
      status['small_image'] = self.match_info['agent_uuid']
      status['small_text'] = self.match_info['agent']['name']
      status['party_size'] = party_info

      if 'start' in self.vrpc_client.presence._prev_status.keys():
         if abs(start - self.vrpc_client.presence._prev_status['start']) > 2:
            status['start'] = start
            status['end'] = end
         else:
            status['start'] = self.vrpc_client.presence._prev_status['start']
            status['end'] = self.vrpc_client.presence._prev_status['end']
      else:
         status['start'] = start
         status['end'] = end

      self.vrpc_client.presence.update(status)

   def __get_match_info(self, initial_match_id: str) -> t.Tuple[bool, bool]:
      if (self.match_info == {}) or (time.time() - self.match_details_last_fetched) > 30:
         self.match_details_last_fetched = time.time()

         try:
            match_details = self.vrpc_client.riot_client.coregame_fetch_match()
         except PhaseError:
            return False, False

         if initial_match_id != match_details['MatchID']:
            return False, False

         if match_details:
            if match_details['State'] != 'IN_PROGRESS':
               return False, False

            local_player = None
            for player in match_details['Players']:
               if player['Subject'] == self.vrpc_client.riot_client.puuid:
                  local_player = player
                  break

            _, self.match_info['mode'] = self.vrpc_client.assets_manager.get_mode_from_url(match_details['ModeID'])
            self.match_info['mode'] = self.match_info['mode']['name']
            self.match_info['provisioning'] = match_details['ProvisioningFlow'] == 'CustomGame' and 'Custom ' or ''
            self.match_info['game_type'] = self.match_info['mode']
            if not match_details['ProvisioningFlow'] == 'CustomGame' and self.match_info['mode'] == 'Standard':
               if match_details['MatchmakingData']['QueueID'] == 'competitive':
                  self.match_info['game_type'] = 'Competitive'
               else:
                  self.match_info['game_type'] = 'Unrated'
            self.match_info['agent'] = self.vrpc_client.assets_manager.get_asset('agents', local_player['CharacterID'])
            self.match_info['agent_uuid'] = local_player['CharacterID']
            self.match_info['map_uuid'], self.match_info['map'] = self.vrpc_client.assets_manager.get_map_from_url(match_details['MapID'])

            return True, True
      else:
         return False, True

   def __loop(self, match_id: str, match_mode: str) -> None:
      if match_mode == 'Standard' or match_mode == 'Swiftplay':
         while True:
            time.sleep(3)
            print_screen = self.vrpc_client.screen_reader.capture_screen()
            if self.vrpc_client.score_reader.debug:
               self.vrpc_client.screen_reader.display_screen(print_screen)

            results = self.vrpc_client.screen_reader.score_reader.record_frame(print_screen)
            logger.debug(results)
            scores, timer, state = results

            match_refreshed, match_active = self.__get_match_info(match_id)

            if not match_active:
               break

            if state is None: # Assuming everything else is none in results :p
               continue

            b_score, r_score = scores
            round_no = b_score + r_score
            secs = self.__mins_secs_ms_to_secs(*timer)

            if secs < 13: # we need time for discord rpc to be updated
               continue

            start, end = self.__get_start_end_from_state(secs, state, round_no, self.match_info['mode'])

            self.start = start

            self.update_standard_presence(((b_score, r_score), (start, end), state))

      elif match_mode == 'Deathmatch':
         while True:
            match_refreshed, match_active = self.__get_match_info(match_id)

            if not match_active:
               break

            if match_refreshed:
               try:
                  presence_data = self.vrpc_client.riot_client.fetch_presence()
               except:
                  break

               if presence_data:
                  party_info = self.get_party_info(presence_data)
                  my_score = presence_data['partyOwnerMatchScoreAllyTeam']
                  opponent_score = presence_data['partyOwnerMatchScoreEnemyTeam']

                  status = {}
                  status['details'] = f'Playing {self.match_info["provisioning"]}{self.match_info["game_type"]} | {self.match_info["agent"]["name"]} | {self.match_info["map"]["name"]}'
                  if my_score < opponent_score:
                     status['state'] = f'{my_score} - {opponent_score} | In Party'
                  elif my_score >= opponent_score:
                     status['state'] = f'Leading with {my_score} kills | In Party'
                  status['large_image'] = self.match_info['map_uuid']
                  status['large_text'] = self.match_info['map']['name']
                  status['small_image'] = self.match_info['agent_uuid']
                  status['small_text'] = self.match_info['agent']['name']
                  status['party_size'] = party_info
                  status['start'], _ = self.__get_start_end_from_state(0, None, 0, match_mode)

                  self.vrpc_client.presence.update(status)
      else:
         while True:
            match_refreshed, match_active = self.__get_match_info(match_id)

            if not match_active:
               break

            if match_refreshed:
               party_info = self.get_party_info()

               status = {}
               if self.match_info["map"]["name"] == 'The Range':
                  status['details'] = f'Playing {self.match_info["provisioning"]}{self.match_info["game_type"]}'
               else:
                  status['details'] = f'Playing {self.match_info["provisioning"]}{self.match_info["game_type"]} | {self.match_info["agent"]["name"]} | {self.match_info["map"]["name"]}'
                  status['small_image'] = self.match_info['agent_uuid']
                  status['small_text'] = self.match_info['agent']['name']
               status['state'] = f'In Party'
               status['large_image'] = self.match_info['map_uuid']
               status['large_text'] = self.match_info['map']['name']
               status['party_size'] = party_info
               status['start'], _ = self.__get_start_end_from_state(0, None, 0, match_mode)

               self.vrpc_client.presence.update(status)

   def __get_start_end_from_state(self, secs: int, state: str, round_no: int, match_mode: str) -> t.Tuple[int, int]:
      def get_start_end(total_length = None):
         if total_length:
            time_now = int(time.time())
            elapsed = total_length - secs
            
            return time_now - int(elapsed), time_now - int(elapsed) + total_length
         else:
            if not self.started:
               self.started = time.time()
            return self.started, None

      if match_mode == 'Standard':
         if state == 'in progress':
            return get_start_end(100)
         elif state == 'spike planted':
            return get_start_end(0)
         else:
            extra = 0
            if state == 'round won' or state == 'round lost' or state == 'clutch':
               extra = 7
            
            if round_no == 0 or round_no == 12 or round_no == 24:
               return get_start_end(45 + extra)
            else:
               return get_start_end(30 + extra)
      elif match_mode == 'Deathmatch':
         return get_start_end() # get_start_end(9*60)
      elif match_mode == 'Escalation':
         return get_start_end() # get_start_end(12*60)
      elif match_mode == 'Replication':
         if state == 'in progress':
            return get_start_end(80)
         elif state == 'spike planted':
            return get_start_end(0)
         else:
            extra = 0
            if state == 'round won' or state == 'round lost' or state == 'clutch':
               extra = 7
            
            if round_no == 4 or round_no == 8:
               return get_start_end(45 + extra)
            else:
               return get_start_end(30 + extra)
      elif match_mode == 'Spike Rush':
         return get_start_end()
      elif match_mode == 'Swiftplay':
         if state == 'in progress':
            return get_start_end(100)
         elif state == 'spike planted':
            return get_start_end(0)
         else:
            extra = 0
            if state == 'round won' or state == 'round lost' or state == 'clutch':
               extra = 7
            
            if round_no == 4 or round_no == 8:
               return get_start_end(45 + extra)
            else:
               return get_start_end(30 + extra)
      else:
         return get_start_end()

   def __mins_secs_ms_to_secs(self, mins: int, secs: int, ms: int) -> float:
      # I know 1s = 0.001ms :(, idk what to name the smaller seconds
      return mins*60 + secs + ms*0.01
