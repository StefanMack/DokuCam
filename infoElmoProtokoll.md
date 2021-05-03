Quelle: Jan Hoersch , https://github.com/nv1t/freeElmo/, siehe auch https://nv1t.github.io/blog/freeing-elmo

freeElmo
========

MultiOS Client for Elmo Document Camera based on libusb (pyusb) and pygame.

[Elmo](http://www.elmo-germany.de) is a company which sells high res document viewer 
and other education based equipment, like voting systems and similar.

We are currently only focused on the document camera itself.
The only camera we have on hand is a L-12 (predecessor of TT-12)


Install
-------
At the moment we are testing on linux devices. 

You'll need: pygame, pil and pyusb.

you have to start ./start.sh

Communication between ImageMate and Elmo
----------------------------------------

1. Version
2. Sync1
3. Sync2
4. Sync3
5. Picture
6. Version
7. Picture
8. Version
...

As far as we know, the syncs are not needed. We are not quite sure why they are
there, and what these numbers are, but the original software asks for it.

Command-Glossary
----------------

        self.msg = {                                                            
             'version':         [0,0,0,0,0x18,0,0,0,0x10,0x8B,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'picture':         [0,0,0,0,0x18,0,0,0,0x8e,0x80,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'buttons':         [0,0,0,0,0x18,0,0,0,0,15,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
                                                                                
            ,'zoom_stop':       [0,0,0,0,0x18,0,0,0,0xE0,0,0,0,0x00,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'zoom_in':         [0,0,0,0,0x18,0,0,0,0xE0,0,0,0,0x01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'zoom_out':        [0,0,0,0,0x18,0,0,0,0xE0,0,0,0,0x02,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'focus_auto':      [0,0,0,0,0x18,0,0,0,0xE1,0,0,0,0x00,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'brightness_stop': [0,0,0,0,0x18,0,0,0,0xE2,0,0,0,0x04,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'brightness_dark': [0,0,0,0,0x18,0,0,0,0xE2,0,0,0,0x03,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'brightness_light':[0,0,0,0,0x18,0,0,0,0xE2,0,0,0,0x02,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'brightness_auto': [0,0,0,0,0x18,0,0,0,0xE2,0,0,0,0x05,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'focus_wide':      [0,0,0,0,0x18,0,0,0,0xEA,0,0,0,0x00,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'focus_near':      [0,0,0,0,0x18,0,0,0,0xEA,0,0,0,0x01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            ,'focus_stop':      [0,0,0,0,0x18,0,0,0,0xEA,0,0,0,0x02,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        } 

The answers are provided below. Unfortunately the focus and the brightness have to be started
and stopped. That's why there is a stop command.

**Version**

(IN 01:00:81, OUT 01:00:02)

    << 0000 0000 1800 0000 108B 0000 0000 0000 
    << 0000 0000 0000 0000 0000 0000 0000 0000
    >> 0100 0000 1800 0000 0000 0000 4C2D 3132  ............L-12
    >> 0000 0000 0000 0000 0000 0000 0000 0000  ................

**Sync1**

(IN 01:00:81, OUT 01:00:02)

    << 0000 0000 1800 0000 118B 0000 0000 0000
    << 0000 0000 0000 0000 0000 0000 0000 0000
    >> 0100 0000 1800 0000 0000 0000 5741 2E31  ............WA.1
    >> 2E30 3034 0000 0000 0000 0000 0000 0000  .004............

**Sync2**

(IN 01:00:81, OUT 01:00:02)

    << 0000 0000 1800 0000 118B 0000 0100 0000                                       
    << 0000 0000 0000 0000 0000 0000 0000 0000
    >> 0100 0000 1800 0000 0000 0000 5741 2E31  ............WA.1                     
    >> 2E31 3931 0000 0000 0000 0000 0000 0000  .191............

**Sync3**

(IN 01:00:81, OUT 01:00:02)

    << 0000 0000 1800 0000 118B 0000 0200 0000                                       
    << 0000 0000 0000 0000 0000 0000 0000 0000                                       
    >> 0100 0000 1800 0000 0000 0000 5741 2E31  ............WA.1
    >> 2E30 3630 0000 0000 0000 0000 0000 0000  .060............

**Picture**

(IN 01:00:83, OUT 01:00:04)

    << 0000 0000 1800 0000 8E80 0000 KK00 0000 
    << 0000 0000 0000 0000 0000 0000 0000 0000
    >> 2000 0000 1800 0000 XXXX 0000 0000 0000 
    >> 0000 0000 0000 0000 0000 0000 0000 0000 
    >> 0200 0000 DDDD 0000 PPPPPPPPPPPPPPPPPPP
    >> PPPP ....
    >> 0200 0000 DDDD 0000 PPPPPPPPPPPPPPPPPPP
    >> PPPP ....

* X : size of picture without header
* K : JPEG Compression 10-100
* P : picture as bytestream (splitted in max 65272 bytes + 8 byte header)
* D : size of packet payload, max size: 0xfef8
