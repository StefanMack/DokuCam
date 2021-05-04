# -*- coding: utf-8 -*-
"""
Modul zur Steuerung der Elmo L-12 Dokumentenkamera.
Frage: Freigabe der USB-Schnittstelle am Ende bei disconnect() nötig?
Modul elmo basiert auf "freeElmo", siehe nv1t.github.io/blog/freeing-elmo
bzw. github.com/nv1t/freeElmo/blob/master/elmo.py

S. Mack, 4.5.21
"""


import usb.core
import usb.util
from io import BytesIO # für Testbild
from PIL import Image # für Testbild
import logging
#import time


class Elmo:
    def __init__(self):
        self.device = None
        self.msg = {
            'version':          [0, 0, 0, 0, 0x18, 0, 0, 0, 0x10, 0x8B, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'picture':          [0, 0, 0, 0, 0x18, 0, 0, 0, 0x8e, 0x80, 0, 0, 60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'buttons':          [0, 0, 0, 0, 24, 0, 0, 0, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'zoom_stop':        [0, 0, 0, 0, 0x18, 0, 0, 0, 0xE0, 0, 0, 0, 0x00, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'zoom_in':          [0, 0, 0, 0, 0x18, 0, 0, 0, 0xE0, 0, 0, 0, 0x01, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'zoom_out':         [0, 0, 0, 0, 0x18, 0, 0, 0, 0xE0, 0, 0, 0, 0x02, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'focus_auto':       [0, 0, 0, 0, 0x18, 0, 0, 0, 0xE1, 0, 0, 0, 0x00, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'brightness_stop':  [0, 0, 0, 0, 0x18, 0, 0, 0, 0xE2, 0, 0, 0, 0x04, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'brightness_dark':  [0, 0, 0, 0, 0x18, 0, 0, 0, 0xE2, 0, 0, 0, 0x03, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'brightness_light': [0, 0, 0, 0, 0x18, 0, 0, 0, 0xE2, 0, 0, 0, 0x02, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'brightness_auto':  [0, 0, 0, 0, 0x18, 0, 0, 0, 0xE2, 0, 0, 0, 0x05, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        }
        self.zooming = False
        self.brightnessing = False
        self.focusing = False
        self.compression = 60
        #### ACHTUNG hier False wenn Elmo-Kamera in Betrieb sons zu Testzwecken True ####
        self.test = False # Livebild via USB
        #self.test = True # Betrieb ohne Elmo und Testbild statt Livebild

    def connect(self, vendor=0x09a1, product=0x001d):
        if self.test: return
        self.device = usb.core.find(idVendor=vendor,  idProduct=product)

        if self.device is None:
            return -1
            logging.warning('Keine Elmo L-12 Kamera gefunden.')
        else:
            if self.device.is_kernel_driver_active(0):
                self.device.detach_kernel_driver(0)
                usb.util.claim_interface(self.device,  0)
        self.device.reset()
        self.device.set_configuration()

        return self

    def setCompression(self, compression, absolute=True):
        logging.debug('elmoCam: setCompression() +/-Val: {}'.format(compression))
        if absolute:
            self.compression = compression
        else:
            self.compression = self.compression+compression
        self.compression = max(10, min(100, self.compression))
        logging.debug('elmoCam: compression set to {}'.format(self.compression))

    def getCompression(self):
        return self.compression

    def zoom(self, i): # Button Press wechselt zwischen -1/+1 und 0
        if self.test: return
        if self.zooming:
            self.device.write(0x02, self.msg['zoom_stop'], 0)
            self.device.read(0x81, 32)
            self.zooming = False
            return

        if i > 0:
            self.device.write(0x02, self.msg['zoom_in'], 0)
        elif i < 0:
            self.device.write(0x02, self.msg['zoom_out'], 0)
        self.zooming = True
        self.device.read(0x81, 32)

    def brightness(self, i):
        if self.test: return
        if self.brightnessing:
            self.device.write(0x02, self.msg['brightness_stop'], 0)
            self.device.read(0x81, 32)
            self.brightnessing = False
            return

        if i > 0:
            self.device.write(0x02, self.msg['brightness_light'], 0)
        elif i < 0:
            self.device.write(0x02, self.msg['brightness_dark'], 0)
        else:
            self.autobrightness()
            return
        self.brightnessing = True
        self.device.read(0x81, 32)

    def autobrightness(self):
        if self.test: return
        self.device.write(0x02, self.msg['brightness_auto'], 0)
        self.device.read(0x81, 32)

    def autofocus(self):
        if self.test: return
        self.device.write(0x02, self.msg['focus_auto'], 0)
        self.device.read(0x81, 32)

    def version(self):
        if self.test: return
        self.device.write(0x02, self.msg['version'], 0)
        ret = self.device.read(0x81, 32)
        return ret

    def clear_device(self): # alle Bytes auslesen bis Timeout
        logging.debug('elmoCam: clear_device()...')
        if self.test: return
        '''Clear the devices memory on endpoint 0x83'''
        while True:
            try:
                self.device.read(0x83, 512, 10) # wieso 512 und (ursprünglich) Default Timeout?
            except usb.core.USBError as e: # USBError gibt Error Number und String (Fehlerbeschreibung) zurück
                logging.warning('elmoCam: clear_device() USBError No. {}: {}'.format(e[0],e[1]))
                if (e.args[0] == 110): # 110 ist pyusb Timeout exception
                    logging.debug('elmoCam: clear_device() > timeout...')
                    break

    def get_test_image(self):
        im = Image.open('testbild.jpg')
        buf = BytesIO()
        im.save(buf, format='JPEG')
        byte_im = buf.getvalue()
        return(byte_im)
    
    def get_image(self):
        logging.debug('elmoCam: get_image()...')
        if self.test: 
            im = Image.open('testbild.jpg')
            buf = BytesIO()
            im.save(buf, format='JPEG')
            byte_im = buf.getvalue()
            return(byte_im)    
        try:
            a = self.msg['picture']
            a[12] = self.compression # jpeg compression ratio
            self.device.write(0x04,  self.msg['picture'], 0) # Anforderung Bild, wieso Timeout 0?
        except:
            logging.warning('elmoCam: get_image() > device.write() exeption...')
        try:
            ret = self.device.read(0x83, 32) # Antwort auf Anforderung Bild mit # Bilddaten-Bytes in Byte 4 und 5
            logging.debug('elmoCam: get_image() poll total {} Bytes to read.'.format(256*ret[5]+ret[4]))
        except:
            logging.debug('elmoCam: get_image() poll > device.read() exception...')
            self.clear_device()
            return False
        whole_img_bytes = [] # Liste für Bytes des gesammten Bildes
        # 0xfef8 (65272) is the maximum size of a package. if it is smaller => the last package and exit
        size = 0xfef8 # Portionen von 0xfef8 (65272) Bytes (ab 8. Byte) mit Bilddaten
        while size == 0xfef8: # falls Portion kleiner, dann Rest = letzte Portion
            try:
                ret = self.device.read(0x83, 512) # Bilddaten ab dem 8. Byte hier enthalten
                size = 256*ret[5]+ret[4] # Byte-Anzahl Bilddaten in Byte 4 und 5 codiert
                logging.debug('size: {} (should be 65272)'.format(size))
                img_data = self.device.read(0x83, (size-504)) # restliche der 65272 Bytes lesen
                whole_img_bytes += ret[8:]+ img_data # gelesene Bytes an Liste anfügen 
            except: # es konnten keine 65272 Bytes gelesen werden > vermulich letzte Portion Bilddaten
                logging.warning('elmoCam: get_image() > exception reading image. Last data size: {}'.format(size))
                self.clear_device() # falls noch Daten am USB Port anliegen, diese auslesen und wegwerfen.
                return False
        return bytearray(whole_img_bytes) # Bilddaten (8-Bit Integer List) in Byte Array umwandeln       
