# 쓰레기 코드

import ctypes
import os
from datetime import datetime
import typing as t

import cv2
import numpy as np
import pytesseract
import win32api
from PIL import Image, ImageGrab

from .pixel_list import (buy_phase_bwpixel_list, match_point_bwpixel_list,
                         match_point_ot_pixel_list, round_lost_bwpixel_list,
                         round_won_bwpixel_list, ot_pixel_list, endgame_pixel_list)

user32 = ctypes.windll.user32
screen_size = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

recording_key_presses_to_text = {
   0xDC: '', # \| key
   0x30: '0',
   0x31: '1',
   0x32: '2',
   0x33: '3',
   0x34: '4',
   0x35: '5',
   0x36: '6',
   0x37: '7',
   0x38: '8',
   0x39: '9',
   0xDD: '10', # ]} key
   0xDB: '11', # [{ key
   0x50: '12', # P key
   0x4F: '13', # O key
   0x49: '14', # I key
   0x55: '15', # U key
   0x59: '16', # Y key
   0x54: '17', # T key
   0x52: '18', # R key
   0x45: '19', # E key
}

score_tes_config = (
   "-c tessedit"
   "_char_whitelist=0123456789"
   " --psm 8"
   " -l val4"
   " "
)
timer_tes_config = (
   "-c tessedit"
   "_char_whitelist=0123456789.:"
   " -l eng"
   " "
)

window_y = -500

class TopBarReader():
   def __init__(self, record: bool, debug: bool, tess_path: str) -> None:
      self.record = record
      self.debug = debug
      pytesseract.pytesseract.tesseract_cmd = tess_path

   def record_frame(self, print_screen: Image.Image) -> t.Tuple[t.Tuple[int, int], t.Tuple[int, int, int], str]:
      scores = self.get_scores(print_screen)
      timer = self.get_timer(print_screen)
      if scores == (None, None) or timer == (None, None, None):
         scores = (None, None)
         timer = (None, None, None)
         status = None
      else:
         pass
         # timer = self.get_timer(print_screen)
         # status = self.get_match_status(print_screen)
         status = self.get_match_status(print_screen)
      return scores, timer, status

   def get_match_status(self, print_screen: Image.Image) -> str:
      image_size = print_screen.size

      state_crop = Image.fromarray(self._erode(self._get_white_pixels(print_screen.crop((
         round(image_size[0]*0.15), round(image_size[1]*0.59),
         round(image_size[0]*0.85), round(image_size[1]*0.82)
      )), 235), 6))

      # spike_crop = print_screen.crop((
      #    round(image_size[0]*0.38), round(image_size[1]*0.06),
      #    round(image_size[0]*0.62), round(image_size[1]*0.325)
      # ))
      # cv2.imshow('spike', cv2.cvtColor(np.array(spike_crop),
      # cv2.COLOR_BGR2RGB))

      status = 'in progress'

      if self._check_bwpixel_list(state_crop, buy_phase_bwpixel_list, False):
         status = 'buy phase'
      elif self._check_bwpixel_list(state_crop, match_point_bwpixel_list, False) or self._check_bwpixel_list(state_crop, match_point_ot_pixel_list, False):
         status = 'match point'
      elif self._check_bwpixel_list(state_crop, round_won_bwpixel_list, False):
         status = 'round won'
      elif self._check_bwpixel_list(state_crop, round_lost_bwpixel_list, False):
         status = 'round lost'
      elif self._check_bwpixel_list(state_crop, ot_pixel_list, False):
         status = 'overtime'
      elif self._check_bwpixel_list(state_crop, endgame_pixel_list, True):
         status = 'endgame'
      else:
         selected_pos = (round(image_size[0]*0.52), round(image_size[1]*0.08))
         selected_pixel = print_screen.getpixel(selected_pos)
         # print_screen.putpixel(selected_pos, (255, 0, 255))
         
         if (selected_pixel[0] > 120) and (selected_pixel[1] < 5) and (selected_pixel[2] < 5):
            status = 'spike planted'

      if self.debug:
         size_scale = 4
         # state_crop.thumbnail(
         #    (
         #       round(state_crop.width*size_scale),
         #       round(state_crop.height*size_scale)
         #    ),
         #    Image.Resampling.LANCZOS
         # )
         cv2.imshow(
            'status',
            cv2.resize(
               cv2.cvtColor(
                  np.array(state_crop),
                  cv2.COLOR_BGR2RGB
               ),
               (
                  round(state_crop.width * size_scale),
                  round(state_crop.height * size_scale)
               ),
               interpolation = cv2.INTER_AREA
            )
         )
         cv2.moveWindow('status', round(-1080/2)-round(state_crop.width*size_scale*0.5), window_y + print_screen.height + 100)

      return status

   def get_timer(self, print_screen: Image.Image) -> t.Tuple[int, int, int]:
      image_size = print_screen.size

      timer_crop = print_screen.crop((
         round(image_size[0]*0.3), round(image_size[1]*0.1),
         round(image_size[0]*0.7), round(image_size[1]*0.24)
      ))

      timer_white = self._get_white_pixels(timer_crop.copy())
      timer_red = self._get_red_pixels(timer_crop.copy())

      timer_white = self._dilate(timer_white, 2)
      timer_red = self._dilate(timer_red, 3)
      
      if self.debug:
         cv2.imshow('timer_w', timer_white)
         cv2.moveWindow('timer_w', round(-1080/2)-round(timer_crop.width*0), window_y + print_screen.height)
         cv2.imshow('timer_r', timer_red)
         cv2.moveWindow('timer_r', round(-1080/2)-round(timer_crop.width*1), window_y + print_screen.height)

      mins = 0
      secs = 0
      ms = 0

      if not self._check_empty_image(Image.fromarray(timer_white)):
         reading = pytesseract.image_to_string(
            timer_white,
            config = timer_tes_config
         ).strip()
         
         try:
            mins, secs = reading.split(':')
         except:
            return None, None, None
      elif not self._check_empty_image(Image.fromarray(timer_red)):
         reading = pytesseract.image_to_string(
            timer_red,
            config = timer_tes_config
         ).strip()
         
         try:
            secs, ms = reading.split('.')
         except:
            return None, None, None
      else:
         return None, None, None

      try:
         mins = int(mins)
         secs = int(secs)
         ms = int(ms)
      except:
         mins = None
         secs = None
         ms = None

      return mins, secs, ms

   def get_scores(self, print_screen: Image.Image) -> t.Tuple[int, int]:
      image_size = print_screen.size

      b_crop = self._get_white_pixels(print_screen.crop((
         round(image_size[0]*0.1), round(image_size[1]*0.1),
         round(image_size[0]*0.188), round(image_size[1]*0.24)
      )))
      r_crop = self._get_white_pixels(print_screen.crop((
         round(image_size[0]*0.812), round(image_size[1]*0.1),
         round(image_size[0]*0.9), round(image_size[1]*0.24)
      )))

      if self.debug:
         cv2.imshow('blue', cv2.cvtColor(np.array(b_crop), cv2.COLOR_BGR2RGB))
         cv2.moveWindow('blue', -1080, window_y)
         cv2.imshow('red', cv2.cvtColor(np.array(r_crop), cv2.COLOR_BGR2RGB))
         cv2.moveWindow('red', -130, window_y)

      if self._check_empty_image(b_crop) or self._check_empty_image(r_crop):
         return None, None

      b_score = pytesseract.image_to_string(
         b_crop,
         config=score_tes_config
      ).strip()
      r_score = pytesseract.image_to_string(
         r_crop,
         config=score_tes_config
      ).strip()

      b_score = int(b_score)
      r_score = int(r_score)

      if self.record:
         self._prompt_record(r_crop)

      return b_score, r_score

   def _check_bwpixel_list(self, image: Image.Image, bwpixel_list: list, debug: bool = False) -> bool:
      for pixel_check in bwpixel_list:
         pos = (
            round(pixel_check[0][0] * image.width),
            round(pixel_check[0][1] * image.height)
         )
         pixel = image.getpixel(pos)

         if debug:
            image.putpixel(pos, (255-pixel_check[1], pixel_check[1], 0))
         
         if (sum(pixel)/3 != pixel_check[1]):
            return False

      return True

   def _dilate(self, image: Image.Image, dilation: int) -> np.ndarray:
      image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
      kernel = np.ones((dilation, dilation), np.uint8)
      return cv2.erode(image, kernel, iterations=1)
      
   def _erode(self, image: Image.Image, dilation: int) -> np.ndarray:
      image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
      kernel = np.ones((dilation, dilation), np.uint8)
      return cv2.dilate(image, kernel, iterations=1)

   def _check_empty_image(self, image: Image.Image) -> bool:
      extrema = image.convert("L").getextrema()
      if extrema == (255, 255):
         return True
      else:
         return False

   def _prompt_record(self, image: Image.Image) -> None:
      def record(text):
         name = datetime.now().strftime(f"{text}_%m_%d_%Y_%H_%M_%S")

         path = 'valorant_scoreboard_training/ocrd-testset'

         with open(f'{path}/{name}.gt.txt', mode='w') as f:
            f.write(text)
         image.save(f'{path}/{name}.png')

         print('recorded', name)

      for key, text in recording_key_presses_to_text.items():
         if win32api.GetKeyState(key) < 0:
            while win32api.GetKeyState(key) < 0:
               pass
            record(text)

      # text = input('Text: ')
      # if text == '':
      #    return
      # else:
      #    record(text)

   def _get_white_pixels(self, image: Image.Image, min_threshold: int = 255) -> Image.Image:
      for x in range(image.width):
         for y in range(image.height):
            pixel = image.getpixel((x, y))

            if sum(pixel)/3 >= min_threshold:
               image.putpixel((x, y), (0, 0, 0))
            else:
               image.putpixel((x, y), (255, 255, 255))

      return image

   def _get_red_pixels(self, image: Image.Image) -> Image.Image:
      for x in range(image.width):
         for y in range(image.height):
            pixel = image.getpixel((x, y))

            if pixel[0] > 253 and pixel[1] < 3 and pixel[2] < 3:
               image.putpixel((x, y), (0, 0, 0))
            else:
               image.putpixel((x, y), (255, 255, 255))

      return image


class ScreenReader():
   def __init__(self, score_reader: TopBarReader) -> None:
      self.score_reader = score_reader

   def display_screen(self, print_screen: Image.Image) -> None:
      cv2.imshow('top bar', cv2.cvtColor(np.array(print_screen), cv2.COLOR_BGR2RGB))
      cv2.moveWindow('top bar', round(-1080/2)-round(print_screen.width/2), window_y)

      if cv2.waitKey(25) & 0xFF == ord('q'):
         cv2.destroyAllWindows()

   def capture_screen(self) -> Image.Image:
      # image = Image.open('captures/full_cap1.png')
      # screen_size = (image.width, image.height)
      # print_screen = image.crop(box=(screen_size[0]*0.4, 0, screen_size[0]*0.6, screen_size[0]*0.15))

      # print_screen = Image.open('captures/capture9.png')
      print_screen = ImageGrab.grab(bbox=(screen_size[0]*0.4, 0, screen_size[0]*0.6, screen_size[0]*0.15))
      # print_screen.save('captures/capture9.png')

      return print_screen


if __name__ == '__main__':
   score_reader = TopBarReader(False, True)
   screen_reader = ScreenReader(score_reader)

   # from multiprocessing import Process
   # p = Process(target=screen_reader.start_screen_record)
   # p.start()

   while True:
      print_screen = screen_reader.capture_screen()
      screen_reader.display_screen(print_screen)
      print(screen_reader.score_reader.record_frame(print_screen))
