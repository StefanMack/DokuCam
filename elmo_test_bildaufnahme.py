# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
Elmo L-12 Dokumentenkamera:
Verbindung zur Kamara via USB herstellen, Bild aufnehmen und darstellen.
Frage: Freigabe der USB-Schnittstelle am Ende nötig?
Modul elmo basiert auf "freeElmo", siehe nv1t.github.io/blog/freeing-elmo
bzw. github.com/nv1t/freeElmo/blob/master/elmo.py

S. Mack, 4.5.21

"""

import elmoCam
from io import BytesIO
from PIL import Image
import time

cam = elmoCam.Elmo()
cam_connect = cam.connect()
cam.autofocus()
time.sleep(1)
data = cam.get_image()
stream = BytesIO(data)              
pic = Image.open(stream)
pic.show()
#pic.save('testbild.jpg')
