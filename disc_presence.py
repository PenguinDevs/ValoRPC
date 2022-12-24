import pypresence
import time
import logging

logger = logging.getLogger(__name__)

client_id = 721690501379522600

class Presence:
   def __init__(self) -> None:
      self.client = pypresence.Presence(client_id)
      self.client.connect()

      self._last_updated = time.time() - 15

      self.state = 'Waiting...'
      self.status = {}
      self._prev_status = {}

   def update(self, status: dict) -> None:
      status['buttons'] = [{'label': 'Download from GitHub', 'url': 'https://github.com/PenguinDevs/ValoRPC/releases/latest'}]
      self.status = status
      self.__check_changed()

   def __check_changed(self) -> None:
      time_now = time.time()
      if (time_now - self._last_updated) >= 15:
         logger.debug(f'Current presence is {self.status}')
         if self.status != self._prev_status:
            self._prev_status = self.status.copy()
            self.client.update(**self.status)
            self._last_updated = time_now
            logger.info('updated status')


if __name__ == '__main__':
   presence = Presence()
   presence.update()
