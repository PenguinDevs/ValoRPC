import threading
import ctypes
import logging

logger = logging.getLogger(__name__)

class Thread(threading.Thread):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs, daemon=True)
          
    def get_id(self) -> None:
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
  
    def terminate(self) -> None:
        # https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/

        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            logger.warning('Exception raise failure')
