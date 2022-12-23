import os
import regex
import requests
import traceback
import logging
import ctypes
import sys
import shutil

logger = logging.getLogger(__name__)

class VersioningHandler:
   def __init__(self, current_version: str, git_repo: str, appdata_path: str, application_path: str) -> None:
      self.current_version = current_version
      self.git_repo = git_repo
      self.latest_endpoint = f'https://api.github.com/repos/{self.git_repo}/releases/latest'
      self.appdata_path = appdata_path
      self.application_path = application_path
      self.installers_path = os.path.join(self.appdata_path, 'installers\\')
      
      self.current_tupled_version = self.version_to_tuple(self.current_version)

   def version_to_tuple(self, version: str) -> tuple:
      tupled_version = tuple([int(d) for d in regex.findall('\d+.\d+.\d+' ,version)[0].split('.')])

      return tupled_version

   def check_update(self) -> None:
      try:
         web_response = requests.get(self.latest_endpoint).json()
         latest_version = web_response['tag_name']
         latest_tupled_version = self.version_to_tuple(latest_version)

         logger.debug(f'Found latest version {latest_version}')

         if latest_tupled_version > self.current_tupled_version:
            logger.info('Later version of ValoRPC found')

            user_response = ctypes.windll.user32.MessageBoxW(0, f'An update for ValoRPC from {self.current_version} to {latest_version} is available! Would you like to update?', 'ValoRPC', 4)
            if user_response == 6:
               self.__run_installer(web_response)
            elif user_response == 7:
               return
         elif latest_version != self.current_version:
            logger.warning(f'A different version of ValoRPC was found {latest_version}, currently {self.current_version}')
            self.__delete_installer_dir()
         else:
            logger.info('ValoRPC is already updated to the latest')
            self.__delete_installer_dir()
      except SystemExit:
         sys.exit(0)
      except:
         logger.warning('Something went wrong when attempting to check for updates')
         logger.error(traceback.format_exc())

   def __delete_installer_dir(self):
      if os.path.exists(self.installers_path):
         logger.info(f'Deleting {self.installers_path}')
         shutil.rmtree(self.installers_path)
      else:
         logger.info(f'Attempted to delete {self.installers_path} but did not exist, skipping...')

   def __run_installer(self, web_response: dict) -> None:
      latest_version = web_response['tag_name']

      if not os.path.exists(self.installers_path):
         os.makedirs(self.installers_path)

      installer_file = None

      for file_name in os.listdir(self.installers_path):
         f = os.path.abspath(os.path.join(self.installers_path, file_name))

         if os.path.isfile(f):
            if latest_version in file_name:
               installer_file = f
               logging.debug('Cached installer file found')
               break

      if not installer_file:
         asset = web_response['assets'][0]
         installer_file = os.path.join(self.installers_path, asset['name'])
         temp_file = os.path.join(self.installers_path, 'TEMP')
         logging.debug('Downloading latest version')
         import subprocess
         # p = subprocess.Popen('start /wait cmd /C'.split() + [os.path.join(self.application_path, 'ValoRPC Web Downloader.exe'), asset['browser_download_url'], temp_file, installer_file], shell=True)
         web_downloader_exe = os.path.join(self.application_path, 'ValoRPC Web Downloader.exe')
         web_downloader_exe = f'"{web_downloader_exe}"'
         # command = 'start /wait cmd /c ' + ' '.join([web_downloader_exe, asset['browser_download_url'], temp_file, installer_file])
         command = ' '.join([web_downloader_exe, asset['browser_download_url'], temp_file, installer_file])
         os.system(command)

         if os.path.exists(installer_file):
            logging.debug(f'Latest installer downloaded and cached')
         else:
            logging.warning(f'Missing installer file at {installer_file}')
            ctypes.windll.user32.MessageBoxW(0, f'Could not find installer executable at {installer_file} Did you cancel the download?', 'ValoRPC', 0)
            sys.exit(0)

      logging.info(f'Using installer executable located at {installer_file}')
      os.system(f'start {installer_file}')
      # subprocess.Popen(['start'] + [installer_file] + ['/S'])

      sys.exit(0)

if __name__ == '__main__':
   versioning_handler = VersioningHandler('v0.2.0-alpha', 'penguindevs/valorpc', 'C:\\Users\\Jason\\AppData\\Roaming\\PenguinDevs\\ValoRPC')
   print(versioning_handler.version_to_tuple('v0.2.0-alpha') > versioning_handler.version_to_tuple('v0.2.5-alpha'), False)
   print(versioning_handler.version_to_tuple('v0.2.0-alpha') > versioning_handler.version_to_tuple('v0.2.4213-alpha'), False)
   print(versioning_handler.version_to_tuple('v0.2.0-beta') < versioning_handler.version_to_tuple('v0.2.4213-alpha'), True)
   print(versioning_handler.version_to_tuple('v214.2.3') > versioning_handler.version_to_tuple('v2.2.9999999-alpha'), True)
   print(versioning_handler.version_to_tuple('v2.2.9999999-alpha'))
   # .version_to_update() is working first try :)
