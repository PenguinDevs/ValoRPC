import ssl
import json
import time
import traceback
import logging

logger = logging.getLogger(__name__)

import websockets

from presences.menus import MenusPresence
from presences.pregame import PregamePresence
from presences.ingame import IngamePresence

class WebsocketListener():
   def __init__(self, vrpc_client) -> None:
      self.vrpc_client = vrpc_client

      self.party_presence = MenusPresence(vrpc_client)
      self.pregame_presence = PregamePresence(vrpc_client)
      self.ingame_presence = IngamePresence(vrpc_client)

      self.events_to_presence = {
         'Update': {
            '/chat/v5/participants/ares-pregame': self.pregame_presence,
            '/chat/v5/participants/ares-coregame': self.ingame_presence,
         },
         'Create': {

         },
         'Delete': {

         }
      }

      self.presence_last_fetched = time.time()
   
   def check_presence(self) -> None:
      self.presence_last_fetched = time.time()
      presence = self.vrpc_client.riot_client.fetch_presence()

      if not presence:
         return

      logger.debug(f'Presence session loop state: {presence["sessionLoopState"]}')

      if presence['sessionLoopState'] == 'MENUS':
         self.party_presence.update(presence)
      elif presence['sessionLoopState'] == 'PREGAME':
         self.pregame_presence.start_with_match_id()
      elif presence['sessionLoopState'] == 'INGAME':
         self.ingame_presence.start_with_match_id()

   async def start_loop(self) -> None:
      ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
      ssl_context.check_hostname = False
      ssl_context.verify_mode = ssl.CERT_NONE

      url = f'wss://127.0.0.1:{self.vrpc_client.riot_client.lockfile["port"]}'

      try:
         async with websockets.connect(url, ssl=ssl_context, extra_headers=self.vrpc_client.riot_client.local_headers, ping_interval=None) as websocket:
            await websocket.send('[5, \"OnJsonApiEvent\"]')

            self.check_presence()

            while True:
               response = await websocket.recv()
               if len(response) <= 0:
                  continue
               
               response = json.loads(response)[2]
               data = response['data']

               uri_to_presence = self.events_to_presence[response['eventType']]
               logger.debug(f'{response["eventType"]} - {response["uri"]}')
               if response['uri'] in uri_to_presence.keys():
                  uri_to_presence[response['uri']].start_with_event_data(data)

               if (time.time() - self.presence_last_fetched) >= 5:
                  self.check_presence()
      except Exception:
         logger.warning('Exception during listening to webhook connection')
         logger.error(traceback.format_exc())
