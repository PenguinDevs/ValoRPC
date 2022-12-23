import sys
import os
import urllib.request
import progressbar

def show_download_progress():
   pbar = None

   def on_update(block_num, block_size, total_size):
      nonlocal pbar
      # logging.debug(f'{block_num}, {block_size}, {total_size}')

      if pbar is None:
         pbar = progressbar.ProgressBar(maxval=total_size, left_justify=True, widgets=[
            ' [', progressbar.Timer(), '] ',
            progressbar.Bar(),
            progressbar.Percentage(), ' at ',
            progressbar.FileTransferSpeed(),
            ' (', progressbar.ETA(), ') ',
         ])
         pbar.start()

      downloaded = block_num * block_size
      if downloaded < total_size:
         pbar.update(downloaded)
      else:
         pbar.finish()
         pbar = None

   return on_update

print(f'Downloading from {sys.argv[1]} as {sys.argv[3]}')
urllib.request.urlretrieve(sys.argv[1], sys.argv[2], show_download_progress())
os.rename(sys.argv[2], sys.argv[3])
sys.exit(0)
