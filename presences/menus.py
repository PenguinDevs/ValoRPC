from .presence import BasePresence

class MenusPresence(BasePresence):
   def __init__(self, vrpc_client) -> None:
      self.vrpc_client = vrpc_client

   def update(self, presence_data: dict) -> None:
      if presence_data['sessionLoopState'] != 'MENUS':
         return

      party_info = self.get_party_info(presence_data)

      state =  (presence_data['partyState'] == 'MATCHMAKING' and 'In Queue') or\
               (presence_data['partyState'] == 'CUSTOM_GAME_SETUP' and 'Setting up Custom Game') or\
               'In Menus'

      status = {}
      status['details'] = f'{state}'
      if state == 'Setting up Custom Game':
         status['state'] = f'In Party'
      else:
         queue_type =   (presence_data['queueId'] == 'ggteam' and 'escalation') or\
                        (presence_data['queueId'] == 'onefa' and 'replication') or\
                        presence_data['queueId']
         status['state'] = f'{queue_type.capitalize()} | In Party'
      status['large_image'] = 'default'
      status['large_text'] = 'ValoRPC'
      # status['small_image'] = 'home'
      # status['small_text'] = state
      
      status['party_size'] = party_info

      self.vrpc_client.presence.update(status)
