from __future__ import absolute_import, unicode_literals

import imgkit
import os
from pyvirtualdisplay import Display
from django.conf import settings
import django
import sys
from PIL import Image
from io import BytesIO
sys.path.append("..")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.dev')
django.setup()
import sys
sys.path.append("")
print(settings)


display = Display(visible=0, size=(600,600))
display.start()
print('display')
img_dir = settings.MEDIA_ROOT
img_name = ''.join(['raaaaaa', '_image.png'])
full_img_path = os.path.join(img_dir, img_name)
print(full_img_path)
b = imgkit.from_url('http://google.com', 'test.png')
print(b)
bool, text, f = imgkit.from_url('http://google.com', 'test.png')
# # print(png)
print(text)
print(f)
print('----')
# im = Image.open(BytesIO(png))
# print(im)
# im.save('screenshot.png')
print('done!!')