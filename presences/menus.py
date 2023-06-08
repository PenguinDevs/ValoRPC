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

      user_status = presence_data['isIdle'] == True and 'Idle' or 'Online'

      status = {}
      status['details'] = user_status == 'Idle' and user_status or f'{state}'
      if state == 'Setting up Custom Game':
         status['state'] = f'In Party'
         queue_type = None
      else:
         queue_type =   (presence_data['queueId'] == 'ggteam' and 'escalation') or\
                        (presence_data['queueId'] == 'onefa' and 'replication') or\
                        presence_data['queueId']
         status['state'] = f'{queue_type.capitalize()} | In Party'
      status['large_image'] = 'default'
      status['large_text'] = 'ValoRPC'
      # status['small_image'] = 'home'
      # status['small_text'] = state
      if user_status == 'Idle':
         status['small_image'] = 'idle'
         status['small_text'] = 'Idle'
      elif queue_type == 'competitive':
         competitive_data = self.vrpc_client.riot_client.fetch_competitive_updates()
         latest_update = competitive_data['Matches'][0]
         status['small_image'] = f'rank_{latest_update["TierAfterUpdate"]}'
         if latest_update['TierAfterUpdate'] < 24:
            status['small_text'] = f'Current RR: {latest_update["RankedRatingAfterUpdate"]}/100'
         else:
            status['small_text'] = f'Current RR: {latest_update["RankedRatingAfterUpdate"]}'
      
      status['party_size'] = party_info

      self.vrpc_client.presence.update(status)
