import regex
import logging

logger = logging.getLogger(__name__)

cached_match_ids = []

class BasePresence():
   def __init__(self) -> None:
      pass

   def _get_match_id_from_chat_event(self, event_data: dict, match_type: str) -> str:
      if not 'participants' in event_data.keys():
         return
      
      example_participant = event_data['participants'][0]
      cid = example_participant['cid']
      match_id = regex.match('[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}', cid)
      match_id = match_id.group(0)

      match_key = f'{match_type}_{match_id}'

      if not match_key in cached_match_ids:
         cached_match_ids.append(match_key)
         logger.info('FOUND MATCH %s', match_id)

         return match_id

   def _register_match_id(self, match_id: str, match_type: str) -> None:
      match_key = f'{match_type}_{match_id}'

      if not match_key in cached_match_ids:
         cached_match_ids.append(match_key)

   def get_party_info(self, presence_data: dict = None) -> dict:
      presence_data = presence_data or self.vrpc_client.riot_client.fetch_presence()

      if not presence_data:
         return

      info = {}
      info['size'] = presence_data['partySize']
      info['max_size'] = presence_data['maxPartySize']

      return [info['size'], info['max_size']]
