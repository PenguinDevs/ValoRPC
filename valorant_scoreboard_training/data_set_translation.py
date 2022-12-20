import os
import random

import cv2
import numpy as np
from PIL import Image

directory1 = 'valorant_scoreboard_training/ocrd-testset_translated'
directory2 = 'valorant_scoreboard_training/ocrd-testset_combined'
 
for filename in os.scandir(directory2):
   if filename.is_file():
      filename = filename.name

      if filename.endswith('.png'):
         name = filename.replace('.png', '')

         with open(f'{directory1}/{name}.gt.txt', mode='w') as f1:
            with open(f'{directory2}/{name}.gt.txt', mode='r') as f2:
               f1.write(f2.read())

         image = Image.open(f'{directory2}/{name}.png')
         image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
  
         height, width = image.shape[:2]
         
         T = np.float32([[1, 0, random.randint(-2, 2)], [0, 1, random.randint(-4, 4)]])
         
         image = cv2.bitwise_not(image)
         image = cv2.warpAffine(image, T, (width, height))
         image = cv2.bitwise_not(image)
         # image = cv2.copyMakeBorder(src=image, top=2, bottom=2, left=2, right=2, borderType=cv2.BORDER_CONSTANT)
         cv2.imwrite(f'{directory1}/{name}.png', image)
