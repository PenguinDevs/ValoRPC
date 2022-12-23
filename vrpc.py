import asyncio
import datetime
import json
import os
import time
import regex
import sys
import psutil
import ctypes
from thread import Thread
import traceback
import logging
import win32com.client
from win32event import CreateMutex
from win32api import GetLastError
from winerror import ERROR_ALREADY_EXISTS
from pathlib import Path

import nest_asyncio

from versioning import VersioningHandler
from sys_tray import SystemTrayApp
from assets.assets_manager import AssetsManager
from disc_presence import Presence
from presences.ingame.reader_util import ScreenReader, TopBarReader
from riot_client import Client as RiotClient
from riot_client import resources as riot_client_resources
from presences.websocket_listener import WebsocketListener


class VRPCClient:
   def __init__(self, appdata_path: str, presence: Presence) -> None:
      self.appdata_path = appdata_path

      self.score_reader = TopBarReader(False, False, os.path.abspath(os.path.join(os.path.dirname(__file__), 'Tesseract-OCR/tesseract.exe')))
      self.screen_reader = ScreenReader(self.score_reader)

      self.riot_client = RiotClient()
      self.riot_client.activate()
      self.riot_client.region = self.get_region()
      self.riot_client.shard = self.get_region()
      if self.riot_client.region in riot_client_resources.region_shard_override.keys():
         self.riot_client.shard = riot_client_resources.region_shard_override[self.riot_client.region]
      if self.riot_client.shard in riot_client_resources.shard_region_override.keys():
         self.riot_client.region = riot_client_resources.shard_region_override[self.riot_client.shard]
      self.riot_client.base_url, self.riot_client.base_url_glz, self.riot_client.base_url_shared = self.riot_client._build_urls()

      self.assets_manager = AssetsManager(self.appdata_path)
      self.assets_manager.bulk_download_all_assets()

      self.presence = presence

      self.websocket = WebsocketListener(self)

   def get_region(self) -> str:
      val_proc_info = json.dumps(self.riot_client.riotclient_session_fetch_sessions())
      return regex.search('"-ares-deployment=(.*)", "-config-endpoint', val_proc_info).group(1)

   def loop(self) -> None:
      asyncio.run(self.websocket.start_loop())

class VRPCMaster:
   def __init__(self) -> None:
      self.get_appdata_location()
      self.logs_dir = os.path.join(self.appdata_path, 'logs/')
      self.setup_logger()

      if getattr(sys, 'frozen', False):
         self.application_path = os.path.dirname(sys.executable)
      elif __file__:
         self.application_path = os.path.dirname(__file__)

      with open(os.path.join(self.application_path, 'info.json'), mode='r') as f:
         self.info = json.load(f)

      self.presence = None
      # self.client_thread = None
      self.asyncio_loop = asyncio.new_event_loop()

      self.setup_system_tray()
      # Thread(target=self.system_tray_icon.loop).start()

      self.check_startup_shortcut()
      # self.check_program_shortcut()

      self.versioning_handler = VersioningHandler(self.info['version'], self.info['git_repo'], self.appdata_path, self.application_path)
      self.versioning_handler.check_update()

      self.logger.info(f'ValoRPC {self.info["version"]} - Valorant Rich Presence for Discord is running!')
      if not '--nonotif' in sys.argv:
         self.system_tray_app.win_notify(f'ValoRPC {self.info["version"]} is running!', 'Discord rich presence will be automatically shown on your profile whenever the Valorant application is running.')
      # if self.is_frozen():
      #    self.logger.info('Hiding this window in 5 seconds.')
      #    time.sleep(5)
      #    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
      
   def start_main_thread(self) -> None:
      self.main_thread = Thread(target=vrpc_master.loop)
      self.main_thread.start()

   def loop(self) -> None:
      asyncio.set_event_loop(self.asyncio_loop)
      # # required for stupid pypresence to work inside an already existing asyncio
      # # loop. :(
      nest_asyncio.apply(self.asyncio_loop)
      
      while True:
         processes = [] # (p.name() for p in psutil.process_iter())
         installers_count = 0 # len([p for p in processes if (('ValoRPC' in p) and ('installer' in p))])
         valorant_exists = False

         for p in psutil.process_iter():
            name = p.name()
            processes.append(name)
            if 'VALORANT.exe' == name:
               valorant_exists = True
            elif ('ValoRPC' in name) and ('installer' in name):
               installers_count += 1
            
            if valorant_exists and installers_count > 0:
               break

         if installers_count > 0:
            self.system_tray_app.win_notify('ValoRPC Installer Detected!', f'ValoRPC {self.info["version"]} has exited as it was running in the background whilst the installer was open.')
            os.system('taskkill /IM ValoRPC.exe')
         elif valorant_exists: # self.process_exists('VALORANT.exe'):
            # if not self.client_thread:
            self.logger.info('vrpc started')
            try:
               self.presence = Presence()

               self.client_loop(self.presence)
               self.presence.client.close()
               self.logger.info('vrpc ended')
               # self.client_thread = Thread(target=self.client_loop, args=(self.presence,))
               # self.client_thread.start()
            except Exception:
               self.logger.warning('vrpc closed when attempting to start with exception:')
               self.logger.error(traceback.format_exc())
         else:
            # if self.client_thread:
            #    self.client_thread.terminate()
            #    self.client_thread = None
            #    self.presence.client.close()
            #    self.logger.info('vrpc ended')
            pass

         time.sleep(6)

   def client_loop(self, presence: Presence) -> None:
      # asyncio.set_event_loop(self.asyncio_loop)
      client = VRPCClient(self.appdata_path, presence)
      client.loop()

   def process_exists(self, process_name: str) -> bool:
      # This method flashes window when running py in no console mode
      # progs = str(subprocess.check_output('tasklist'))
      # if process_name in progs:
      #    return True
      # else:
      #    return False
      if process_name in (p.name() for p in psutil.process_iter()):
         return True
      else:
         return False

   def setup_logger(self) -> None:
      if not os.path.exists(self.logs_dir):
         os.makedirs(self.logs_dir)

      now = datetime.datetime.now()
      self.log_file = os.path.join(self.logs_dir, Rf'{now.strftime("%m_%d_%Y_%H_%M_%S")}.log')
      if self.is_frozen():
         logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
            filename=self.log_file,
            filemode='a'
         )
      else:
         logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
         )
      self.logger = logging.getLogger()
      # if not getattr(sys, 'frozen', False) and not hasattr(sys, '_MEIPASS'):
      #    sys.stderr.write = self.logger.error
      #    sys.stdout.write = self.logger.info

   def setup_system_tray(self) -> None:
      self.system_tray_app = SystemTrayApp(
         os.path.join(self.application_path, 'favicon.ico'),
         'ValoRPC',
         [
            ('Logs', [
               ('View latest', self.view_latest_log),
               ('Open folder', self.open_logs_folder)
            ])
         ],
         'ValoRPC_Tray'
      )

   def view_latest_log(self, system_tray_app: SystemTrayApp) -> None:
      with open(self.log_file, mode='r') as f:
         # echo = [sys.executable, "-c",
         #       "import sys; print(sys.argv[1]); input('Press Enter..')"]
         # subprocess.Popen("cmd.exe /c start".split() + echo + [f.read()])
         os.system(f'notepad.exe {self.log_file}')

   def open_logs_folder(self, system_tray_app: SystemTrayApp) -> None:
      with open(self.log_file, mode='r') as f:
         os.system(f'explorer "{os.path.abspath(self.logs_dir)}"')

   def is_frozen(self) -> bool:
      if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
         return True
      else:
         return False

   def __create_shortcut(self, target: str, args: str = None) -> None:
      shell = win32com.client.Dispatch("WScript.Shell")
      shortcut = shell.CreateShortCut(target)

      shortcut.Targetpath = os.path.join(self.application_path, 'ValoRPC.exe')
      shortcut.IconLocation = os.path.join(self.application_path, 'favicon.ico')
      shortcut.Arguments = args
      shortcut.save()

   def check_startup_shortcut(self) -> None:
      target = os.path.join(Path.home(), 'AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/ValoRPC.lnk')
      self.__create_shortcut(target, '--nonotif')

   def check_program_shortcut(self) -> None:
      target = os.path.join(Path.home(), 'AppData/Roaming/Microsoft/Windows/Start Menu/Programs/ValoRPC.lnk')
      self.__create_shortcut(target)

   def get_appdata_location(self) -> None:
      path = os.path.join(Path.home(), 'AppData\\Roaming\\PenguinDevs\\ValoRPC\\')

      self.appdata_path = path

if __name__ == '__main__':
   handle = CreateMutex(None, 1, 'ValoRPC')

   if GetLastError() == ERROR_ALREADY_EXISTS:
      response = ctypes.windll.user32.MessageBoxW(0, 'ValoRPC is already running!', 'ValoRPC', 0) # 5)
      sys.exit(0)
   else:
      vrpc_master = VRPCMaster()
      vrpc_master.start_main_thread()
      vrpc_master.system_tray_app.loop()
