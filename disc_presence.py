import pypresence
import time

client_id = 721690501379522600

class Presence:
   def __init__(self) -> None:
      self.client = pypresence.Presence(client_id)
      self.client.connect()

      self._last_updated = time.time() - 15

      self.state = 'Waiting...'
      self.status = {}
      self._prev_status = {}

   def update(self, status: str) -> None:
      status['buttons'] = [{'label': 'Download from GitHub', 'url': 'https://github.com/PenguinDevs/ValoRPC/releases'}]
      self.status = status
      self.__check_changed()

   def __check_changed(self) -> None:
      time_now = time.time()
      if (time_now - self._last_updated) >= 15:
         if self.status != self._prev_status:
            self._prev_status = self.status.copy()
            self.client.update(**self.status)
            self._last_updated = time_now
            print('updated status')


if __name__ == '__main__':
   presence = Presence()
   presence.update()
