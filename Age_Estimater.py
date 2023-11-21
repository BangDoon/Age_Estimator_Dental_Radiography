#!/usr/bin/env python
'''
photo_spliter.py - Provides a simple method to split a single image containing
multiple images into individual files.

Created by Greg Lavino
03.16.2010


Note the following packages are required:
 python-tk
 python-imaging
 python-imaging-tk
'''

from re import T
import tensorflow as tf
from PIL import Image
from PIL import ImageTk
import tkinter
from tkinter import ttk
from tkinter import filedialog
import sys
import os
import PIL.Image as pilimg

import numpy as np
from tensorflow.keras import models

#physical_devices = tf.config.list_physical_devices('GPU') 
#tf.config.experimental.set_memory_growth(physical_devices[0], True)

global text


thumbsize = 1200, 1200

class Application(tkinter.Frame):              
    def __init__(self, master=None,filename=None):
        
        tkinter.Frame.__init__(self, master)   
        self.grid()                    

        style = ttk.Style()
        style.configure("Label", foreground="black", background="white")

        self.text = tkinter.StringVar()
        self.text.set('')
        self.label = ttk.Label ( self, textvariable = self.text ,style="Label")

        self.createWidgets()


        self.croprect_start=None
        self.croprect_end=None
        self.crop_count=0
        self.age_sum = 0
        self.canvas_rects=[]
        self.crop_rects=[] 
        self.current_rect=None
        self.model = models.load_model("./model/20_70_72")
        
        if filename:
            self.filename=filename
            self.loadimage()
        
        
    def createWidgets(self):
        self.canvas = tkinter.Canvas(self,height = 1, width = 1,relief=tkinter.SUNKEN,cursor="tcross")
        self.canvas.bind("<Button-1>",self.canvas_mouse1_callback)
        self.canvas.bind("<ButtonRelease-1>",self.canvas_mouseup1_callback)
        self.canvas.bind("<B1-Motion>",self.canvas_mouseb1move_callback)
        
        

        self.fileButton = tkinter.Button ( self, text='file',
            command=self.file_lst )

        self.quitButton = tkinter.Button ( self, text='Quit',
            command=self.quit )
        self.resetButton = tkinter.Button ( self, text='Reset',
            command=self.reset )
        
        self.undoButton = tkinter.Button ( self, text='Undo',
            command=self.undo_last )
        
        self.goButton = tkinter.Button ( self, text='Estimate',
            command=self.start_cropping )
        

        self.canvas.grid(row=0,columnspan=3)

        self.fileButton.grid(row=1,column=0)
        self.goButton.grid(row=1,column=1)
        self.label.grid(row=1,column=2,sticky=tkinter.W)
               
        self.resetButton.grid(row=3,column=0)
        self.undoButton.grid(row=3,column=1) 
        self.quitButton.grid(row=3,column=2)

        
        


    def canvas_mouse1_callback(self,event):
        self.croprect_start=(event.x,event.y)

    def canvas_mouseb1move_callback(self,event):
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        x1=self.croprect_start[0]
        y1=self.croprect_start[1]
        x2=event.x
        y2=event.y
        bbox = (x1,y1,x2,y2)
        cr = self.canvas.create_rectangle(bbox )
        self.current_rect=cr
    
    def canvas_mouseup1_callback(self,event):
        self.croprect_end=(event.x,event.y)
        self.set_crop_area()
        self.canvas.delete(self.current_rect)
        self.current_rect=None
        

    def set_crop_area(self):
        r=Rect( self.croprect_start ,self.croprect_end )
        
        
        # adjust dimensions
        r.clip_to(self.image_thumb_rect)
        
        # ignore rects smaller than this size
        if min(r.h,r.w) < 10:
            return
        
        self.drawrect(r)
        self.crop_rects.append(r.scale_rect(self.scale) )

    
    
    def undo_last(self):
        if self.canvas_rects:
            r = self.canvas_rects.pop()
            self.canvas.delete(r)
        
        if self.crop_rects:
            self.crop_rects.pop()    
        
    def drawrect(self,rect):
        bbox=(rect.left, rect.top,rect.right, rect.bottom)
        cr = self.canvas.create_rectangle(bbox , activefill="",fill="red",stipple="gray25" )
        self.canvas_rects.append(cr)
    
    def displayimage(self):
        self.photoimage=ImageTk.PhotoImage(self.image_thumb)
        w,h = self.image_thumb.size
        self.canvas.configure(width=w,height=h)

        self.canvas.create_image(0,0,anchor=tkinter.NW,image=self.photoimage)         
    
    def reset(self):
        self.canvas.delete(tkinter.ALL)
        self.canvas_rects=[]
        self.crop_rects=[]
        
        self.text.set('')
        self.crop_count=0
        self.age_sum = 0
        self.displayimage()

    def loadimage(self):
        

        self.image = Image.open(self.filename)
        print(self.image.size)
        self.image_rect = Rect(self.image.size)
        
        self.image_thumb=self.image.copy()
        self.image_thumb.thumbnail(thumbsize)
        
        self.image_thumb_rect = Rect(self.image_thumb.size)
        
        #imt.thumbnail(thumbsize, Image.ANTIALIAS)
        self.displayimage()
        x_scale  = float(self.image_rect.w) / self.image_thumb_rect.w
        y_scale  = float(self.image_rect.h) / self.image_thumb_rect.h
        self.scale=(x_scale,y_scale)

    def newfilename(self,filenum):
        f,e = os.path.splitext(self.filename)
        return './crop/crop_%s%s'%(filenum, e)


    def file_lst(self):

        self.reset()
        file = filedialog.askopenfilenames(initialdir="./",\
                 title = "파일을 선택 해 주세요",\
                    filetypes = (("*.bmp","*bmp"),("*.jpg","*jpg"),("*.png","*png")))

        file= file[0] 
        self.filename=file
        self.loadimage()



    def start_cropping(self):
        cropcount = 0
        for croparea in self.crop_rects:
            cropcount+=1
            f = self.newfilename(cropcount)
            print(f,croparea)
            self.crop(croparea,f)
        
        if cropcount != 0:
            age_mean = self.age_sum / cropcount
            
        
        print(age_mean[0])
       
        self.text.set(f'{str(age_mean[0])}세') 
        #self.reset()

    def crop(self,croparea,filename):
        ca=(croparea.left,croparea.top,croparea.right,croparea.bottom)
        newimg = self.image.crop(ca)
        print(newimg)
        newimg.save(filename)
        pix = self.img_process(filename)

        age = self.model.predict(pix)*60+20
        age = age.reshape(-1,)
        print(age)
        self.age_sum += age
        
        
    
    def img_process(self,filename):
        im = pilimg.open(filename).convert('L')
        im = im.resize((150,150))
        pix = np.array(im,dtype=int)
        pix = pix/255
        pix = np.expand_dims(pix, -1)
        pix = np.expand_dims(pix, 0)
        #print(pix.shape)
        return pix
        
    




class Rect(object):
    def __init__(self, *args):
        self.set_points(*args)

    def set_points(self, *args):
        if len(args)==2:
            pt1 = args[0]
            pt2 = args[1]
        elif len(args) == 1:
            pt1 = (0,0)
            pt2 = args[0]
        elif len(args)==0:
            pt1 = (0,0)
            pt2 = (0,0)
        

        x1, y1 = pt1
        x2, y2 = pt2
        
        self.left = min(x1, x2)
        self.top = min(y1, y2)
        self.right = max(x1, x2)
        self.bottom = max(y1, y2)
        
        self._update_dims()


    def clip_to(self,containing_rect):
        cr = containing_rect
        self.top    = max(self.top , cr.top)
        self.bottom = min(self.bottom, cr.bottom)
        self.left   = max(self.left , cr.left)
        self.right  = min(self.right, cr.right)
        self._update_dims()
            
    def _update_dims(self):
        '''added to provide w and h dimensions'''
       
        self.w = self.right - self.left
        self.h = self.bottom - self.top
        
    def scale_rect(self,scale):
        x_scale  = scale[0]
        y_scale  = scale[1]
        
        r=Rect()
        r.top = int(self.top * y_scale)
        r.bottom = int(self.bottom * y_scale)
        r.right = int(self.right * x_scale)
        r.left = int(self.left * x_scale)
        r._update_dims()
        
        return r

    def __repr__(self):
        return '(%d,%d)-(%d,%d)'%(self.left,self.top,self.right,self.bottom)



def main():
    # if len(sys.argv)>1:
    #     filename=sys.argv[1]
    # else:
    #     print("Need a filename")
    #     return
    filename = filedialog.askopenfilenames(initialdir="./",\
                title = "파일을 선택 해 주세요",\
                filetypes=(("Image files", "*.bmp;*.jpg;*.png"), ("All files", "*.*")))

    filename= filename[0]  
    app = Application(filename=filename)                    
    app.master.title("Age_Estimater") 
    app.mainloop()                  

if __name__=='__main__':main()



