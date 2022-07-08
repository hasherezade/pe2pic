#!/usr/bin/env python3
"""pe2pic.py: Visualise raw bytes of any given file and save as a PNG. If a PE was supplied, visualizes also sections layout."""

__author__ = 'hasherezade'
__license__ = "GPL"

import sys
import os
import math, random
import argparse
import pefile
from PIL import Image, ImageColor, ImageDraw, ImageFont

def getfilebytes(filename,offset=0):
    """
        Get bytes from source file
    """
    fo = open(filename,"rb")
    fo.seek(offset,0) #seek from current file position
    data = fo.read()
    fo.close()
    return (len(data),data)

def get_raw_bytes(filename):
    filesize = os.path.getsize(filename)
    (bytesread,rawbytes) = getfilebytes(filename)
    return rawbytes

###

def sections_to_json(filename):
    sec_list = listsections(filename)
    group_obj = { "sections" : sec_list }
    return (json.dumps(group_obj, indent=1))

class ImageBuffer:
#private
    def _calcDimensions(self, size):
        #calculate pixel dimensiong for a square image
        unit = 3 #RGB
        pixelsCount = len(self.rawbytes)/unit
        # one pixel = 3 bytes
        if self.w is None:
            self.w = int(math.ceil(math.sqrt(pixelsCount)))
            self.h = self.w #sqare
        else:
            self.h = int(math.ceil(pixelsCount / self.w))
        self.padding  = int(((self.w * self.h) * unit) - size)

    def _appendPadding(self, stuffing):
        stuffingSize = len(stuffing)
        stuffingUnits = self.padding / stuffingSize
        stuffingRem = self.padding % stuffingSize
        #print("Dif = %d, stuffing size = %d * %d + %d" % (self.padding, stuffingSize, stuffingUnits, stuffingRem))
        if self.padding == 0:
            return
        i = 0
        totalStuffingSize = stuffingUnits * stuffingSize
        while totalStuffingSize:
            self.rawbytes += stuffing.encode('utf-8')
            totalStuffingSize = totalStuffingSize - 1
        if stuffingRem == 0:
           return
        stuffing = stuffing[:stuffingRem]
        self.rawbytes += stuffing

#public

    def __init__(self, rawbytes, width=None):
        self.rawbytes = rawbytes
        self.w = width
        self._calcDimensions(len(rawbytes))
        self.printInfo()
        self._appendPadding('\0')

    def printInfo(self):
        print("width: " + str(self.w))
        print("height: " + str(self.h))
        print("Padding: " + str(self.padding))
        print("Finalsize: " + str(len(self.rawbytes)))

###

def cstr_to_str(cstring):
    name_str = ""
    for c in cstring:
        if c == 0:
            break
        name_str += chr(c)
    return name_str

def random_color():
    r = random.randrange(255)
    g = random.randrange(255)
    b = random.randrange(255)
    rand_color = (r, g, b, 10)
    return rand_color

def paint_section(imc, imgBuffer, scale, sect, my_color):
    unit = 3 #RGB
    width = imgBuffer.w
    draw = ImageDraw.Draw(imc)

    sec_end = sect.PointerToRawData + sect.SizeOfRawData
    start_y = int(math.ceil((sect.PointerToRawData)/(width*unit))*scale)
    limit_y = int(math.ceil((sec_end)/(width*unit))*scale)
    
    for x in range(0, width*scale):
        for y in range(start_y, limit_y):
            try:
                imc.putpixel((x, y), my_color)
            except:
                break

def paint_section_name(imc, imgBuffer, scale, sect, num, coord):
    unit = 3 #RGB
    width = imgBuffer.w
    sec_end = sect.PointerToRawData + sect.SizeOfRawData
    start_y = int(math.ceil((sect.PointerToRawData)/(width*unit))*scale)
    sec_name = cstr_to_str(sect.Name)
    draw = ImageDraw.Draw(imc)
    text = "#" + str(num) + "[" + sec_name  + "]:"
    textwidth, textheight = draw.textsize(text)
    if coord != 0:
        coord = coord - int(textwidth/2)
    text_pos = start_y - textheight
    if text_pos < 0:
        text_pos = 0
    x, y = (coord, text_pos)
    draw.rectangle((x, y, x + textwidth, y + textheight), fill='black')
    draw.text((coord, text_pos), text, fill='white')

def fill_with_sections(imgBuffer, my_pe, color_fill, scale=1):
    if scale == 0:
        return
    if color_fill:
        imc = Image.new(mode="RGB", size=(imgBuffer.w, imgBuffer.h))
    else:
        imc = Image.frombuffer("RGB", (imgBuffer.w, imgBuffer.h), imgBuffer.rawbytes,"raw","RGB",0,1)
    if scale > 1:
        newsize = (imgBuffer.w * scale, imgBuffer.h * scale)
        imc = imc.resize(newsize, resample=Image.Resampling.BOX)

    sections_count = len(my_pe.sections)
    if sections_count == 0:
        return imc

    width, height = imc.size

    if color_fill:
        for sect in my_pe.sections:
            paint_section(imc, imgBuffer, scale, sect, random_color())
    
    coord_u = int(width/sections_count)
    num = 0
    for sect in my_pe.sections:
        coord = (coord_u * num) % width
        paint_section_name(imc, imgBuffer, scale, sect, num, coord)
        num += 1
    return imc

def make_entropy_img(imgBuffer, scale=1):
    if scale == 0:
        return
    imc = Image.frombuffer("RGB", (imgBuffer.w, imgBuffer.h), imgBuffer.rawbytes,"raw","RGB",0,1)
    if scale > 1:
        newsize = (imgBuffer.w * scale, imgBuffer.h * scale)
        imc = imc.resize(newsize, resample=Image.Resampling.BOX)
    return imc
    #imc.save(filename)

def combine_images(images):
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset,0))
        x_offset += im.size[0]
    return new_im

def save_decoded(decdata, outfile):
    fr = open(outfile, "wb")
    if fr is None:
        return False
    fr.write(decdata.encode())
    fr.close()
    return True

def make_prefixed_name(filename, prefix):
    basename = os.path.basename(filename)
    dirname = os.path.dirname(filename)

    basename = prefix + basename
    out_name = os.path.join(dirname, basename)
    print(out_name)
    return out_name

def make_images(filename, min_height, double_view):
    images = []
    rawbytes = get_raw_bytes(filename)
        
    my_pe = None
    try:
        my_pe = pefile.PE(filename, fast_load=True)
    except:
        my_pe = None

    imagebuffer = ImageBuffer(rawbytes)
    if imagebuffer.h == 0:
        return

    scale = math.ceil(min_height / imagebuffer.h)

    if my_pe is not None:
        
        img1 = fill_with_sections(imagebuffer, my_pe, double_view, scale)
        images.append(img1)
        if (not double_view):
            return images

    img2 = make_entropy_img(imagebuffer, scale)
    images.append(img2)
    return images

def visualize_file(filename, min_height, double_view, outfile, show=False):
    images = make_images(filename, min_height, double_view)
    out_img = combine_images(images)
    if show:
        out_img.show()
    if outfile is not None:
        out_img.save(outfile)

def main():
    parser = argparse.ArgumentParser(description="PE visualizer")
    parser.add_argument('--infile', dest="infile", default=None, help="Input file", required=True)
    parser.add_argument('--outfile', dest="outfile", default=None, help="Output file")
    parser.add_argument('--double', dest="double", default=False, help="double section view?", action='store_true')
    parser.add_argument('--minheight', dest="minheight", default=200, help="Min height of the output image", type=int)
    args = parser.parse_args()

    filename = args.infile
    outfile = args.outfile

    print("Input: " + filename)
    min_height = args.minheight
    visualize_file(filename, args.minheight, args.double, args.outfile, True)
    if outfile is not None:
        print("Saved to: " + args.outfile)

if __name__ == "__main__":
    main()
    
