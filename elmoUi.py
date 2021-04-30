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

S. Mack, 29.4.21

"""

import logging
import pygame, sys, datetime, time, os
from pygame.locals import RESIZABLE, MOUSEBUTTONDOWN
from PIL import Image
from io import BytesIO
import elmoCam

# Nachfolgende Zeile für Debugmeldungen ausschalten (level=0 bedeutet alle Meldungen)
# DEBUG 10, INFO 20, WARNING 30
logging.basicConfig(level=10)
logging.basicConfig(filename='logDatei.log', level=40)

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
version = "0.1"
disp_info = pygame.display.Info()
rotate = False
rotate_90 = 0
rotate_90_changed = False
display_help = False
display_interface = True
image_res = None
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
                Show/Hide Interface: Crtl+I\n
                Toggle Fullscreen: Ctrl+F
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
        
#draw a interface with buttons on the screen        
def draw_interface(screen, screen_size, buttons, error_no_elmo, font, color_background, color_font, bold=False):
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
    buttons["interface"] = Button()
    buttons["interface"].create_button(screen, color_background, screen_size[0]-button_width, counter*button_height, button_width, button_height, 0, "Interface Off", color_font, font, font_size, bold)
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
        buttons["zoom_in"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Zoom In", color_font, font, font_size, bold)
        counter += 2
        buttons["zoom_out"] = Button()
        buttons["zoom_out"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Zoom Out", color_font, font, font_size, bold)
        counter += 2
        buttons["brightness_reset"] = Button()
        buttons["brightness_reset"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Reset Brightness", color_font, font, font_size, bold)
        counter += 2
        buttons["brightness_up"] = Button()
        buttons["brightness_up"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Brightness Up", color_font, font, font_size, bold)
        counter += 2
        buttons["brightness_down"] = Button()
        buttons["brightness_down"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Brightness Down", color_font, font, font_size, bold)
        counter += 2
        buttons["focus_auto"] = Button()
        buttons["focus_auto"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Autofocus", color_font, font, font_size, bold)
        counter += 2
        buttons["focus_macro"] = Button()
        buttons["focus_macro"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Macrofocus", color_font, font, font_size, bold)
        counter += 2
        buttons["focus_wide"] = Button()
        buttons["focus_wide"].create_button(screen, color_background, 0, counter*button_height, button_width, button_height, 0, "Widefocus", color_font, font, font_size, bold)
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
    #image_size = image.get_size()
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

#save screen from actual pygame screen
def save_screen(screen):
    is_windows = sys.platform.startswith('win')
    if is_windows:
        dir_sep = "\\"
    else:
        dir_sep = "/"
    directory = "ELMO-Screenshots"
    if not os.path.exists(directory):
        os.makedirs(directory)
    pygame.image.save(screen, "ELMO-Screenshots" + dir_sep + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png")

def save_cam(cam):
    if cam.test: return
    if cam.connect() != -1:
        is_windows = sys.platform.startswith('win')
        if is_windows:
            dir_sep = "\\"
        else:
            dir_sep = "/"
        directory = "ELMO-Screenshots"
        if not os.path.exists(directory):
            os.makedirs(directory)  
        #get the image     
        data = cam.get_image()
        compression = cam.getCompression()
        cam.setCompression(100)
        #make image to a pygame compatible
        stream = BytesIO(data)                                    
        pic = Image.open(stream)
        image = pygame.image.load(pic)
        pygame.image.save(image, "ELMO-Screenshots" + dir_sep + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png")
        cam.setCompression(compression)

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
                    #raise TextRectException, "The word " + word + " is too long to fit in the rect passed."
                    print("The word " + word + " is too long to fit in the rect passed.")
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
            #raise TextRectException, "Once word-wrapped, the text string was too tall to fit in the rect."
            print("Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width - tempsurface.get_width(), accumulated_height))
            else:
                #raise TextRectException, "Invalid justification argument: " + str(justification)
                print("Invalid justification argument: ")
        accumulated_height += font.size(line)[1]
    return surface


##########
# events #
##########
def events():
    #get global vars
    #vars are global because input and output changed too often => should be changed to input args and returns
    global elmo
    global cam
    global error_no_elmo
    global screen
    global image
    global rotate
    global rotate_90
    global display_help
    global display_interface
    global image_size
    global buttons
    global ui_running
    #button-pressed event-handling
    for event in pygame.event.get():
        #window resize event
        if event.type == pygame.VIDEORESIZE and error_no_elmo == False:
            size = event.size
            temp_width = size[0]
            temp_height = size[1]
            logging.debug('window size: {}x{}'.format(screen.get_size()[0], screen.get_size()[1]))     
            if temp_width < 480: temp_width = 480
            if temp_height < 320: temp_height = 320
            screen = pygame.display.set_mode((temp_width, temp_height),RESIZABLE)
            try:
                if image != None:
                    image_size = resize_image(image, screen)
            except NameError:
                pass                
        #close program
        if event.type == pygame.QUIT:
            ui_running = False
        #keydown-events
        if event.type == pygame.KEYDOWN:
            #close program
            if (event.key == pygame.K_q and pygame.K_LCTRL) or (event.key == pygame.K_q and pygame.K_RCTRL) or (event.key == pygame.K_F4 and pygame.K_LALT) or (event.key == pygame.K_F4 and pygame.K_RALT) or (event.key == pygame.K_ESCAPE and display_help == False):
                ui_running = False    
            #rotate display
            if (event.key == pygame.K_t and pygame.K_LCTRL) or (event.key == pygame.K_t and pygame.K_RCTRL):
                rotate = not rotate
            if (event.key == pygame.K_r and pygame.K_LCTRL) or (event.key == pygame.K_r and pygame.K_RCTRL):                    
                rotate_90 = rotate_90 + 1
                if rotate_90 == 4:
                    rotate_90 = 0
            #display help
            if (event.key == pygame.K_h and pygame.K_LCTRL) or (event.key == pygame.K_h and pygame.K_RCTRL) or event.key == pygame.K_F1:
                display_help = not display_help
            #display interface
            if (event.key == pygame.K_i and pygame.K_LCTRL) or (event.key == pygame.K_i and pygame.K_RCTRL):
                display_interface = not display_interface
            #make screenshot
            if (event.key == pygame.K_s and pygame.K_LCTRL) or (event.key == pygame.K_s and pygame.K_RCTRL):
                #save_screen(image)
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
                    cam.focus(0)
                #macro focus
                if (event.key == pygame.K_e and pygame.K_LCTRL) or (event.key == pygame.K_e and pygame.K_RCTRL):
                    cam.focus(-1)
                #wide focus
                if (event.key == pygame.K_w and pygame.K_LCTRL) or (event.key == pygame.K_w and pygame.K_RCTRL):
                    cam.focus(1)
                #quality up
                if (event.key == pygame.K_u and pygame.K_LCTRL) or (event.key == pygame.K_u and pygame.K_RCTRL):
                    cam.setCompression(5, False)
                #quality down
                if (event.key == pygame.K_z and pygame.K_LCTRL) or (event.key == pygame.K_z and pygame.K_RCTRL):
                    cam.setCompression(-5, False)
        #Button handling
        elif event.type == MOUSEBUTTONDOWN:
            if buttons['exit'].pressed(pygame.mouse.get_pos()):
                ui_running = False
            if buttons['help'].pressed(pygame.mouse.get_pos()):
                display_help = not display_help
            if buttons['interface'].pressed(pygame.mouse.get_pos()):
                display_interface = not display_interface
            if buttons['rotate'].pressed(pygame.mouse.get_pos()):
                rotate = not rotate
            if buttons['save'].pressed(pygame.mouse.get_pos()):
                #save_screen(image)
                save_cam(cam)
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
                    cam.focus(0)
                if buttons['focus_macro'].pressed(pygame.mouse.get_pos()):
                    cam.focus(-1)
                if buttons['focus_wide'].pressed(pygame.mouse.get_pos()):
                    cam.focus(1)
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
    #################################
    # initialisation of ELMO device #
    #################################
    if error_no_elmo == True:
        try:    
            logging.debug('# of displays: {}'.format(pygame.display.get_num_displays()))
            logging.debug('monitor size:{}x{}'.format(disp_info.current_w,disp_info.current_h))
            cam = elmoCam.Elmo()
            #cam_connect = cam.connect()
            #error_no_elmo = True if cam_connect == -1 else False
            error_no_elmo = False # Testbetrieb
        except:
            print('Keine Elmo gefunden...')
            error_no_elmo = True
              
    events() # check for pygame events
        
    try: #clear background
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill(BLACK)
        screen.blit(background, (0, 0))
    except:
        pass
    try: # get the image           
        data = cam.get_image() # Bilddaten als Byte Array einlesen
        error_no_elmo = False
        stream = BytesIO(data) #Byte-Stream aus data - wie eine Datei einlesbar
        error_no_image = False
        image_new = pygame.image.load(stream) # draw image on screen                                 
        
        #rotate image x-90 degree
        #long calculation phases for the pictures, deactivated at the moment
        #image_new = image_new.rotate(90*(rotate_90%4))  
        
    except:
        #ELMO-Device wont deliver a image
        print('ELMO gibt kein Bild')
        error_no_image = True
  
    #if new image update the image, else the old image will be displayed.
    if error_no_image == False:
        image = image_new

    if image != None:        
        #save of the image resolution
        image_res = image.get_size()

        #init display on startup if not set
        if screen is None:
            start_size = reduce_to_screen_size(image, disp_info)
            screen = pygame.display.set_mode(start_size,RESIZABLE, display=0) # Screen auf Monitor 1 (display=0)
            pygame.display.set_caption(str("Elmo UI v" + version)) #set msg of the window
            screen_res = screen.get_size()
            image_size = image.get_size()
            
        #rotate screen if demanded
        if rotate:
            image = pygame.transform.flip(image, True, True)
        
        #resize image to fit the screen
        image_size = resize_image(image, screen) #not sure if it must before the if
        #resize the image
        image = pygame.transform.smoothscale(image, image_size)
        screen_res = screen.get_size()

        #draw image on screen
        screen.blit(image, get_image_padding(image,screen))
        
        #display help when ctrl+h, for close ctrl+h or esc must be pressed
        #must be after screen.blit(image...
        if display_help:
            screen = draw_help(screen, screen.get_size(), version, basic_font, DGRAY, LGRAY) 
        #display button-interface and return the buttons for event handling
        if display_interface:
            buttons = draw_interface(screen, screen.get_size(), buttons, error_no_elmo, basic_font, DGRAY, LGRAY)
        #display error massage when no image is delivered
        if error_no_image:
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
        if screen_res == None:
            screen_res = [480, 320]
        screen = pygame.display.set_mode(screen_res,RESIZABLE)
        pygame.display.set_caption(str("ERROR!!! - Free ELMO Version " + version)) #set msg of the window
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
            screen.blit(rendered_text, textRect)
    pygame.display.update()
time.sleep(0.5)
pygame.quit()