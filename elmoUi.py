#!/usr/bin/python3

#-*- coding: utf-8 -*-
"""
Benutzeroberfläche für Elmo L-12 Dokumentenkamera:
Verbindung zur Kamara via USB herstellen, Bild aufnehmen und darstellen.

Quellcode basiert auf "freeElmo", siehe nv1t.github.io/blog/freeing-elmo
bzw. github.com/nv1t/freeElmo/blob/master/elmo.py und wurde auf Python3
adaptiert sowie restrukturiert.

Unter Linux udev-Rules Datei in /etc/udev/rules.d/  nötig für Berechtigung 
auf die Gruppe video für Zugriff auf Elmo ohne Root Rechte.

Erste funktionierende Version v1.0
Getestet nur unter Ubuntu Linux 20.04 LTS.
Unter Windoof muss mindestens die Pfadangabe in der Funktion save_to_file() 
geänder werden.´

S. Mack, 4.5.21

"""

import logging
import pygame, datetime, os #, time
from pygame.locals import RESIZABLE, MOUSEBUTTONDOWN
from PIL import Image
from io import BytesIO
import elmoCam

# Nachfolgende Zeile für Debugmeldungen ausschalten (level=0 bedeutet alle Meldungen)
# DEBUG 10, INFO 20, WARNING 30
logging.basicConfig(level=logging.WARNING)
#logging.basicConfig(filename='logDatei.log', level=logging.WARNING)

pygame.init() #init pygame

########################
# set fonts and colors #
########################
#fonts:
basic_font = ""
basic_font_size = 24
#colors:
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
LGRAY = (216, 216, 216)
DGRAY = (48, 48, 48)

###############
# global vars #
###############
version = "1.0"
disp_info = pygame.display.Info()
rotate = False
rotate_90 = 0
rotate_90_changed = False
display_help = False
display_menue = True
image_size = None
image = None
screen_res = None
screen = None
cam_connect = -1
error_no_elmo = True
error_no_image = True
buttons = {}
ui_running = True # Flag True solange UI nicht durch User beendet

#############
# functions #
#############
#draw help-window with commands on the screen 
def draw_help(screen, screen_size, version, font, color_background, color_font):
    #define string to display 
    my_string = """\n
                Help\n
                Quit: Ctrl+Q, Alt+F4, Escape\n
                Display Help: Ctrl+H, F1  
                Exit Help: Ctrl+H, F1, Escape\n
                Show/Hide Menue: Crtl+M\n
                Rotate Image 180 Degree: Ctrl+T"""
                   #Rotate Image 90 Degree: Ctrl+R\n
    my_string += """\n
                Save Image: Ctrl+S\n\n
                Camera options:\n
                Zoom in start/stop: Ctrl+C
                Zoom out start/stop: Ctrl+V\n
                Reset Brightness: Ctrl+G 
                Brightness up start/stop: Ctrl+D
                Brightness down start/stop: Ctrl+X\n
                Autofocus: Ctrl+A
                Macrofocus start/stop: Ctrl+E
                Widefocus start/stop: Ctrl+W\n
                Image Quality UP: Crtl+U
                Image Quality Down: Crtl+Z\n\n
                Elmo User Interface - Version """+version
                
    #define resolution of the rectangle
    height = screen_size[1] * 0.9
    width= (height/5)*4
    font_size = int((height/13)/2)
    #create rectangle
    textRect = pygame.Rect((0, 0, width, height))
    #set rectangle position to middle of the screen
    textRect.centerx = screen.get_rect().centerx
    textRect.centery = screen.get_rect().centery   
    fits = False
    while not fits:
        try:
            #render the text for the rectangle
            rendered_text = render_textrect(my_string, pygame.font.SysFont(font, font_size), textRect, color_font, color_background, 0)
            fits = True
        except:
            font_size = font_size - 1
            if font_size == 1:
                fits = True
    if rendered_text:
        screen.blit(rendered_text, textRect)
    return screen
        
#draw a menue with buttons on the screen        
def draw_menue(screen, screen_size, buttons, error_no_elmo, font, color_background, color_font, bold=False):
    '''the screen will be split in a relative size for the adjustable buttons size it will be the same a in help a minimum
    resolution of 200x200 pixels is standard calculate relative size of tides for the screen'''
    screen_height = screen_size[1]
    font_size = int((screen_height/20)/2)
    button_width = 7 * font_size
    button_height = 1.2 * font_size
    #Create buttons Array
    buttons = {}
    #Parameters for Buttons: surface, color, x, y, length, height, width, text, text_color, font, font_size, bold
    #buttons right side
    counter = 0
    buttons["exit"] = Button()
    buttons["exit"].create_button(screen, color_background, screen_size[0]-button_width, counter*button_height, button_width, button_height, 0, "Exit", color_font, font, font_size, bold)
    counter += 2
    buttons["help"] = Button()
    buttons["help"].create_button(screen, color_background, screen_size[0]-button_width, counter*button_height, button_width, button_height, 0, "Help", color_font, font, font_size, bold)
    counter += 2
    buttons["menue"] = Button()
    buttons["menue"].create_button(screen, color_background, screen_size[0]-button_width, counter*button_height, button_width, button_height, 0, "Menue Off Strg+M", color_font, font, font_size, bold)
    counter += 2
    counter = 0
    buttons["rotate"] = Button()
    buttons["rotate"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Rotate Image", color_font, font, font_size, bold)
    counter += 2
    buttons["save"] = Button()
    buttons["save"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Save Image", color_font, font, font_size, bold)
    counter += 2
    #Deactivation of elmo-systems-commands if the elmo-device is not connected
    if error_no_elmo == False:
        buttons["zoom_in"] = Button()
        buttons["zoom_in"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Zoom In on/off", color_font, font, font_size, bold)
        counter += 2
        buttons["zoom_out"] = Button()
        buttons["zoom_out"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Zoom Out on/off", color_font, font, font_size, bold)
        counter += 2
        buttons["brightness_reset"] = Button()
        buttons["brightness_reset"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Reset Brightness", color_font, font, font_size, bold)
        counter += 2
        buttons["brightness_up"] = Button()
        buttons["brightness_up"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Brightness + on/off", color_font, font, font_size, bold)
        counter += 2
        buttons["brightness_down"] = Button()
        buttons["brightness_down"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Brightness - on/off", color_font, font, font_size, bold)
        counter += 2
        buttons["focus_auto"] = Button()
        buttons["focus_auto"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Autofocus", color_font, font, font_size, bold)
        counter += 2
        buttons["quality_up"] = Button()
        buttons["quality_up"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Image Quality Up", color_font, font, font_size, bold)
        counter += 2
        buttons["quality_down"] = Button()
        buttons["quality_down"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Image Quality Down", color_font, font, font_size, bold)
        counter += 2
    return buttons

#get image format
def get_image_format(image):
    size = image.get_size()
    if (size[0]/4)*3*0.95 < size[1] and size[1] < (size[0]/4)*3*1.05:
        im_format = [4, 3]
    elif (size[0]/3)*4*0.95 < size[1] and size[1] < (size[0]/3)*4*1.05:
        im_format = [3, 4]
    elif (size[0]/5)*4*0.95 < size[1] and size[1] < (size[0]/5)*4*1.05:
        im_format = [5, 4]
    elif (size[0]/4)*5*0.95 < size[1] and size[1] < (size[0]/4)*5*1.05:
        im_format = [4, 5]
    elif (size[0]/16)*10*0.95 < size[1] and size[1] < (size[0]/16)*10*1.05:
        im_format = [16, 10]
    elif (size[0]/10)*16*0.95 < size[1] and size[1] < (size[0]/10)*16*1.05:
        im_format = [10, 16]
    elif (size[0]/9)*16*0.95 < size[1] and size[1] < (size[0]/9)*16*1.05:
        im_format = [9, 16]
    else:
        im_format = [16, 9]
    return im_format
        
#resize image
def resize_image(image, screen):
    #calculate actual sizes 
    im_format = get_image_format(image)
    screen_size = screen.get_size()
    #calculate the new image size
    if screen_size[0]/im_format[0] > screen_size[1]/im_format[1]:
        height = screen_size[1]
        width = (height/im_format[1])*im_format[0]
    elif screen_size[0]/im_format[0] == screen_size[1]/im_format[1]:
        width = screen_size[0]
        height = screen_size[1]
    elif screen_size[0]/im_format[0] < screen_size[1]/im_format[1]:
        width = screen_size[0]
        height = (width/im_format[0])*im_format[1]   
    return [int(width), int(height)]

#get the padding for .blit(image, (x,y))
def get_image_padding(image, screen):
    screen_size = screen.get_size()
    image_size = image.get_size()
    x = (screen_size[0]-image_size[0])/2
    y = (screen_size[1]-image_size[1])/2
    return [x, y]

def save_image_to_file(cam): # für Windows bei Pfadangabe auf Backslash ändern
    if cam.test: return
    if cam.connect() != -1:
        directory = "ElmoScreenShots" # Verzeichnis Screenshots im Arbeitsverzeichnis
        if not os.path.exists(directory):
            os.makedirs(directory) 
        compression = cam.getCompression()
        cam.setCompression(80) # jpg-Qualität erhöhen falls <80
        data = cam.get_image()
        stream = BytesIO(data)                                    
        pic = Image.open(stream)
        pic.save('ElmoScreenShots/elmo_image'+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+'.jpg')
        cam.setCompression(compression) # ursprüngliche jpg-Qualität einstellen

#reduce source to display resolution
def reduce_to_screen_size(image, disp_info):
    image_size = image.get_size()
    #compare sizes an get a little extra space for taskbars to fit the image
    if image_size[0] > disp_info.current_w:
        max_width = disp_info.current_w - 100
    else:
        max_width = image_size[0] - 100
    if image_size[1] > disp_info.current_h:
        max_height = disp_info.current_h - 100
    else:
        max_height = image_size[1] - 100
    #reduce the screen to the format of the image
    im_format = get_image_format(image)
    if max_width > (max_height/im_format[1])*im_format[0]:
        max_width = (max_height/im_format[1])*im_format[0]
    if max_height > (max_width/im_format[0])*im_format[1]:
        max_height = (max_width/im_format[0])*im_format[1]
    return [int(max_width), int(max_height)]

def render_textrect(string, font, rect, text_color, background_color, justification=0):
    """Returns a surface containing the passed text string, reformatted to fit within the given rect, word-wrapping as necessary.
    The text will be anti-aliased. Author: David Clark, siehe https://www.pygame.org/pcr/text_rect/index.php
    """
    final_lines = []
    requested_lines = string.splitlines()
    # Create a series of lines that will fit on the provided rectangle.
    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise ValueError('render_textrect: The word " + word + " is too long to fit in the rect passed.')
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit.    
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line)
                    accumulated_line = word + " "
            final_lines.append(accumulated_line)
        else:
            final_lines.append(requested_line)

    # Let's try to write the text out on the surface.
    surface = pygame.Surface(rect.size)
    surface.fill(background_color)

    accumulated_height = 0
    for line in final_lines:
        if accumulated_height + font.size(line)[1] >= rect.height:
            raise ValueError('render_textrect: Once word-wrapped, the text string was too tall to fit in the rect.')
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width - tempsurface.get_width(), accumulated_height))
            else:
                raise ValueError('render_textrect: Invalid justification argument.')
        accumulated_height += font.size(line)[1]
    return surface


##########
# events #
##########
def events():
    logging.debug('events()...')
    global elmo
    global cam
    global error_no_elmo
    global screen
    global image
    global rotate
    global display_help
    global display_menue
    global image_size
    global buttons
    global ui_running
    
    for event in pygame.event.get():        
        if event.type == pygame.QUIT: # close program event
            ui_running = False
        
        if event.type == pygame.KEYDOWN: # keydown events
            #close program
            if (event.key == pygame.K_q and pygame.K_LCTRL) or (event.key == pygame.K_q and pygame.K_RCTRL) or (event.key == pygame.K_F4 and pygame.K_LALT) or (event.key == pygame.K_F4 and pygame.K_RALT) or (event.key == pygame.K_ESCAPE and display_help == False):
                ui_running = False    
            #rotate display
            if (event.key == pygame.K_t and pygame.K_LCTRL) or (event.key == pygame.K_t and pygame.K_RCTRL):
                rotate = not rotate
            #display help
            if (event.key == pygame.K_h and pygame.K_LCTRL) or (event.key == pygame.K_h and pygame.K_RCTRL) or event.key == pygame.K_F1:
                display_help = not display_help
            #display menue
            if (event.key == pygame.K_m and pygame.K_LCTRL) or (event.key == pygame.K_m and pygame.K_RCTRL):
                display_menue = not display_menue
            #Aktuelles Bild als jpg-Datei speichern
            if (event.key == pygame.K_s and pygame.K_LCTRL) or (event.key == pygame.K_s and pygame.K_RCTRL):
                save_cam(cam)
            #exit help with escape
            if event.key == pygame.K_ESCAPE and display_help == True:
                display_help = False
            #ELMO-Functions like zoom, brightness, focus
            if error_no_elmo == False:
                #zoom in
                if (event.key == pygame.K_c and pygame.K_LCTRL) or (event.key == pygame.K_c and pygame.K_RCTRL):
                    cam.zoom(1)
                #zoom out
                if (event.key == pygame.K_v and pygame.K_LCTRL) or (event.key == pygame.K_v and pygame.K_RCTRL):
                    cam.zoom(-1)
                #brightness up
                if (event.key == pygame.K_d and pygame.K_LCTRL) or (event.key == pygame.K_d and pygame.K_RCTRL):
                    cam.brightness(1)
                #brightness down
                if (event.key == pygame.K_x and pygame.K_LCTRL) or (event.key == pygame.K_x and pygame.K_RCTRL):
                    cam.brightness(-1)                
                #reset brightness
                if (event.key == pygame.K_g and pygame.K_LCTRL) or (event.key == pygame.K_g and pygame.K_RCTRL):
                    cam.brightness(0)
                #autofocus
                if (event.key == pygame.K_a and pygame.K_LCTRL) or (event.key == pygame.K_a and pygame.K_RCTRL):
                    cam.autofocus()
                #quality up
                if (event.key == pygame.K_u and pygame.K_LCTRL) or (event.key == pygame.K_u and pygame.K_RCTRL):
                    cam.setCompression(5, False)
                #quality down
                if (event.key == pygame.K_z and pygame.K_LCTRL) or (event.key == pygame.K_z and pygame.K_RCTRL):
                    cam.setCompression(-5, False)
        
        elif event.type == MOUSEBUTTONDOWN: # Bei Mausklick
            # prüfen ob Mauszeiger im entsprechenden Button-Rechteck
            if buttons['exit'].pressed(pygame.mouse.get_pos()):
                ui_running = False
            if buttons['help'].pressed(pygame.mouse.get_pos()):
                display_help = not display_help
            if buttons['menue'].pressed(pygame.mouse.get_pos()):
                display_menue = not display_menue
            if buttons['rotate'].pressed(pygame.mouse.get_pos()):
                rotate = not rotate
            if buttons['save'].pressed(pygame.mouse.get_pos()):
                save_image_to_file(cam)
            #ELMO-Functions like zoom, brightness, focus
            if error_no_elmo == False:
                if buttons['zoom_in'].pressed(pygame.mouse.get_pos()):
                    cam.zoom(1)
                if buttons['zoom_out'].pressed(pygame.mouse.get_pos()):
                    cam.zoom(-1)
                if buttons['brightness_reset'].pressed(pygame.mouse.get_pos()):
                    cam.brightness(0)
                if buttons['brightness_up'].pressed(pygame.mouse.get_pos()):
                    cam.brightness(1)
                if buttons['brightness_down'].pressed(pygame.mouse.get_pos()):
                    cam.brightness(-1)
                if buttons['focus_auto'].pressed(pygame.mouse.get_pos()):
                    cam.autofocus()
                if buttons['quality_up'].pressed(pygame.mouse.get_pos()):
                    cam.setCompression(5, False)
                if buttons['quality_down'].pressed(pygame.mouse.get_pos()):
                    cam.setCompression(-5, False)



###########
# classes #
##########

class Button:
    ''' Creating and handling buttons. Author: Simon H. Larsen, siehe https://simonhl.dk/button-drawer-python-2-6/'''
    def create_button(self, surface, color, x, y, length, height, width, text, text_color, font, font_size, bold=False):
        surface = self.draw_button(surface, color, length, height, x, y, width)
        surface = self.write_text(surface, text, text_color, length, height, x, y, font, font_size, bold)
        self.rect = pygame.Rect(x,y, length, height)
        return surface

    def write_text(self, surface, text, text_color, length, height, x, y, font, font_size, bold):
        myFont = pygame.font.SysFont(font, font_size)
        if bold:
            myFont.set_bold(1)
        else:
            myFont.set_bold(0)
        myText = myFont.render(text, 1, text_color)
        surface.blit(myText, ((x+length/2) - myText.get_width()/2, (y+height/2) - myText.get_height()/2))
        return surface

    def draw_button(self, surface, color, length, height, x, y, width):           
        for i in range(1,10):
            s = pygame.Surface((length+(i*2),height+(i*2)))
            s.fill(color)
            alpha = (255/(i+2))
            if alpha <= 0:
                alpha = 1
            s.set_alpha(alpha)
            pygame.draw.rect(s, color, (x-i,y-i,length+i,height+i), width)
            surface.blit(s, (x-i,y-i))
        pygame.draw.rect(surface, color, (x,y,length,height), 0)
        pygame.draw.rect(surface, (190,190,190), (x,y,length,height), 1)  
        return surface

    def pressed(self, mouse):
        if mouse[0] > self.rect.topleft[0]:
            if mouse[1] > self.rect.topleft[1]:
                if mouse[0] < self.rect.bottomright[0]:
                    if mouse[1] < self.rect.bottomright[1]:
                        return True
                    else: return False
                else: return False
            else: return False
        else: return False


#################
# main-function #
#################
while ui_running:
    logging.debug('new frame...')
    #################################
    # initialisation of ELMO device #
    #################################
    if error_no_elmo == True:
        try:    
            logging.debug('# of displays: {}'.format(pygame.display.get_num_displays()))
            logging.debug('display size:{}x{}'.format(disp_info.current_w,disp_info.current_h))
            cam = elmoCam.Elmo()
            cam_connect = cam.connect() # bei Testbetrieb auskommentieren
            if cam_connect == -1:
                error_no_elmo = True
            else:
                error_no_elmo = False
            #error_no_elmo = False # Testbetrieb
        except:
            logging.warning('No Elmo camera found...')
            error_no_elmo = True
              
    events() # check for pygame events (evtl. wegen pyGame 2 noch ändern)
        
    try: #clear background
        logging.debug('clear background...')
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill(BLACK)
        screen.blit(background, (0, 0))
    except:
        pass
    
    try: # Bild via USB einlesen und umformen
        logging.debug('get new image...')
        data = cam.get_image() # Bilddaten als Byte Array einlesen
        error_no_elmo = False
        stream = BytesIO(data) # Byte-Stream aus data erzeugen - wie eine Datei einlesbar
        error_no_image = False
        image_new = pygame.image.load(stream) # neues Bild in pyGame einlesen                                      
    except:
        logging.warning('exeption get new image...')
        error_no_image = True
  
    if error_no_image == False: # falls kein neues Bild, das vorherige verwenden
        image = image_new

    if image != None:            
        if screen is None: # init display on startup if not set
            start_size = reduce_to_screen_size(image, disp_info)
            screen = pygame.display.set_mode(start_size,RESIZABLE, display=0) # Screen auf Monitor 1 (display=0)
            pygame.display.set_caption(str("Elmo UI v" + version)) #set msg of the window
            image_size = image.get_size()
            
        if rotate: # Bild 180° rotieren falls Flag durch Rotate Button gesetzt
            logging.debug('rotate image...')
            image = pygame.transform.flip(image, True, True)
        
        # Bei Änderung Fenstergröße Bild entsprechend skalieren
        image_size = resize_image(image, screen) # Bildgröße berechnen
        image = pygame.transform.smoothscale(image, image_size) # Bild skalieren
        logging.debug('Image resized...')
        screen.blit(image, get_image_padding(image,screen)) # Bild im pyGame-Fenster darstellen
        
        if display_help: # help-Fenster anzeigen
            screen = draw_help(screen, screen.get_size(), version, basic_font, DGRAY, LGRAY) 
        
        if display_menue: # Menü anzeigen
            buttons = draw_menue(screen, screen.get_size(), buttons, error_no_elmo, basic_font, DGRAY, LGRAY)
        
        if error_no_image: # display error massage when no image is delivered
            logging.warning('error_no_image...')
            string = "\n  Can't get a new image.  "
            #calculating the box size
            temp_font_size = int((screen.get_size()[0]/12)/2)
            temp_width = temp_font_size * 3
            temp_height = temp_font_size * 0.75
            #print the boy on the screen
            fits=False
            rendered_text = False
            while not fits:
                try:
                    textRect = pygame.Rect((0, 0, temp_width, temp_height))
                    textRect.centerx = screen.get_rect().centerx
                    rendered_text = render_textrect(string, pygame.font.SysFont(basic_font, temp_font_size-1), textRect, LGRAY, DGRAY, 0)
                    fits = True
                except:
                    temp_font_size = temp_font_size - 1
                    if temp_font_size == 0: fits = True
            if rendered_text:
                screen.blit(rendered_text, textRect)        
    
    if error_no_elmo == True or image == None:
        logging.warning('error_no_elmo...')
        if screen_res == None:
            screen_res = [480, 320]
        screen = pygame.display.set_mode(screen_res,RESIZABLE)
        pygame.display.set_caption(str("ERROR!!! - elmoUi Version " + version)) #set msg of the window
        #define string to display
        error_string = ""
        if error_no_elmo:
            error_string = error_string + "\n\n    No Camera found    "
        if error_no_image:
            error_string = error_string + "\n\n    Can't get a Image "
        #create rectangle
        textRect = pygame.Rect((0, 0, screen_res[0], screen_res[1]))
        #set rectangle position to middle of the screen
        textRect.centerx = screen.get_rect().centerx
        textRect.centery = screen.get_rect().centery  
        
        #render the text for the rectangle
        rendered_text = render_textrect(error_string, pygame.font.SysFont("", 24), textRect, LGRAY, DGRAY, 0)
        if rendered_text:
            logging.debug('rendered text...')
            screen.blit(rendered_text, textRect)
    pygame.display.update()
pygame.quit()