#! /usr/bin/python
# -*- coding: utf-8 -*-

import math
import Image
import subprocess

fps = 25
logf = open('ttpretext.log','a')


def makeMP4Pretext(root,duration,filename,soundname,target,vbitrate,abitrate,width,height,fps=25):
# Compute number of frame in shortest sequence
  if fps < 25: fps = 25
  secs = int(duration)
  tw   = int(width)
  th   = int(height)
  vb   = float(vbitrate)
  ab   = float(abitrate)
  primes = [2,3,5,7,11,13,17,19,23,29,31]
  totalFrames = math.ceil(fps * secs)

  smallestDiff = 100.0
  for p in primes:
    totalSeq = math.ceil(totalFrames / p)
    actualFrames = totalSeq * p
    actualDuration = actualFrames / fps  
    diff = actualDuration - duration
    if(diff < smallestDiff) :
      smallestDiff = diff
      smallestPrime = p
    if(smallestDiff == 0): 
      break

  framesInSeq = smallestPrime
  numberOfSeq = int(math.ceil(totalFrames / framesInSeq))

# Compute cropping or padding
  if(filename and filename != 'black'):
    im = Image.open(filename)
    sw = im.size[0]
    sh = im.size[1]
    print >> logf, "Size of base image : ",im.size 
    nh = int(th * (float(sw) / tw))
    print >> logf, "Height of cropped/padded image : ",nh
  if(not filename or (filename == 'black')):
    imNew = Image.new("RGB",(tw,th))
  elif(nh < sh):
    ch = sh - nh
    ct = ch / 2
    cb = ch - ct
    imNew = im.crop((0,ct,sw,sh-cb))
  elif(nh > sh):
    ph = nh - sh
    pt = ph / 2
    imNew = Image.new("RGB",(sw,nh))
    imNew.paste(im,(0,pt))
  else:
    imNew = im.copy()
  print >> logf, "Size of adjusted image : ",imNew.size

# Remove old temporaries
  command = "rm %s/img*.png" % root
  print >> logf, command
  logf.flush()
  pid = subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/tmpmp4.mp4" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/sound.mp4" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/resmp4.mp4" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/atot.mp4" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/vtot.mp4" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Duplicate images
  for i in range(framesInSeq):
    pngtarget = "%s/img%02d.png" % (root,i)
    imNew.save(pngtarget)
  
# Create shortest video sequence
  command = "ffmpeg -i %s/img%%02d.png -vb %f -s %dx%d -r %d %s/tmpmp4.mp4" % (root,(vb*1000),tw,th,fps,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Create complete video sequence
  print >> logf, "Concat %d times" % numberOfSeq
  command = "MP4Box -fps %d -cat %s/tmpmp4.mp4 %s/vtot.mp4" % (fps,root,root)
  print >> logf, command
  logf.flush()
  for i in range(numberOfSeq): subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  
# Create short sound sequence
  command = "MP4Box -add %s %s/sound.mp4" % (soundname,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "MP4Box -splitx 0:%d %s/sound.mp4" % (1,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Create complete sound sequence
  print >> logf, "Concat %d times" % secs
  command = "MP4Box -cat %s/sound.mp4 %s/atot.mp4" % (root,root)
  print >> logf, command
  logf.flush()
  for i in range(secs): subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Add sound and video
  command = "MP4Box -add %s/vtot.mp4 -add %s/atot.mp4 %s/resmp4.mp4" % (root,root,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Clip to the wanted length
  command = "MP4Box -splitx 0:%d %s/resmp4.mp4 -out %s/resmp4.mp4" % (secs,root,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  
  """
# Clip to the wanted length au
  command = "MP4Box -splitx 0:%d %s/atot.mp4 -out %s/atot.mp4" % (secs,root,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Clip to the wanted length vi
  command = "MP4Box -splitx 0:%d %s/vtot.mp4 -out %s/vtot.mp4" % (secs,root,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  """

  command = "mv %s/resmp4.mp4 %s  " % (root,target)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

  command = "ffmpeg2theora --info %s  " % (target,)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

def makeTSPretext(root,duration,filename,soundname,target,vbitrate,abitrate,tw,th,framerate='25:1'):
# Compute number of frame in shortest sequence
  teller = int(framerate.partition(':')[0])
  nevner = int(framerate.partition(':')[2])
  fps = float(teller / nevner)
  if fps < 25: fps = 25
  secs = int(duration)

  totalFrames = math.ceil(fps * secs)

  framesInSeq = fps
  numberOfSeq = int(math.ceil(totalFrames / framesInSeq))

  print >> logf, "Frames in short seq ",framesInSeq, " * number of sequences ", numberOfSeq, " = total frames  ", totalFrames," / fps ", fps, " = seconds ", secs  

# Compute cropping or padding
  if(filename and filename != 'black'):
    im = Image.open(filename)
    sw = im.size[0]
    sh = im.size[1]
    print >> logf, "Size of base image : ",im.size 
    nh = int(th * (float(sw) / tw))
    print >> logf, "Height of cropped/padded image : ",nh
  if(not filename or (filename == 'black')):
    imNew = Image.new("RGB",(tw,th))
  elif(nh < sh):
    ch = sh - nh
    ct = ch / 2
    cb = ch - ct
    imNew = im.crop((0,ct,sw,sh-cb))
  elif(nh > sh):
    ph = nh - sh
    pt = ph / 2
    imNew = Image.new("RGB",(sw,nh))
    imNew.paste(im,(0,pt))
  else:
    imNew = im.copy()
  print >> logf, "Size of adjusted image : ",imNew.size

# Remove old temporaries
  command = "rm %s/img*.png" % root
  print >> logf, command
  logf.flush()
  pid = subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/vts" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/ats" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/rests" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/totts" % root
  print >> logf, command
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)


# Duplicate images
  for i in range(int(math.ceil(framesInSeq))):
    pngtarget = "%s/img%02d.png" % (root,i)
    imNew.save(pngtarget)
  
# Create short sequence
  command = "ffmpeg -r %d -i %s/img%%02d.png -r %d -i %s -vb %d -s %dx%d -t 1 -r %d -f mpegts %s/rests" % (fps,root,fps,soundname,(vbitrate*1000),tw,th,fps,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Create complete sequence
  print >> logf, "Concat sound and video %d times" % secs
  command = "cat %s/rests >>%s/totts" % (root,root)
  print >> logf, command
  logf.flush()
  for i in range(secs): subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Move to target
  command = "mv %s/totts %s  " % (root,target)
  print >> logf,  command
  logf.flush()
  subprocess.call(command, shell=True, stderr=logf)

  #command = "ffmpeg2theora --info %s  " % (target,)
  #print >> logf, command
  #logf.flush()
  #subprocess.call(command, shell=True, stdout=logf, stderr=logf)



def makeOGGPretext(source,target):
# Convert mp4 to ogg
  command = 'ffmpeg2theora %s -o %s -c 2 -H 24000 -F 25' % (source,target)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

def glueMP4Pretext(root,sources,target):

# Remove old temporaries
  command = "rm %s/resmp4" % root
  print >> logf, command
  logf.flush()
  pid = subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  i = 0
  for s in sources:
    command = "MP4Box -fps %d -force-cat -cat %s %s/resmp4" % (fps,s,root)
    print command
    logf.flush()
    subprocess.call(command, shell=True, stderr=logf)
  command = "mv %s/resmp4 %s  " % (root,target)
  print command
  logf.flush()
  subprocess.call(command, shell=True, stderr=logf)


def glueOGGPretext(root,sources,target):
# Remove old temporaries
  command = "rm %s/resogg.ogg" % root
  print >> logf, command
  logf.flush()
  pid = subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  t = " ".join(sources)
  #for s in sources:
  command = "oggCat %s/resogg.ogg %s" % (root,t)
  print command
  logf.flush()
  subprocess.call(command, shell=True, stderr=logf)
  command = "mv %s/resogg.ogg %s  " % (root,target)
  print command
  logf.flush()
  subprocess.call(command, shell=True, stderr=logf)

def glueTSPretext(root,sources,target,framerate):
  teller = int(framerate.partition(':')[0])
  nevner = int(framerate.partition(':')[2])
  fps = float(teller / nevner)
  if fps < 25: fps = 25
  if fps < 25: fps = 25
# Remove old temporaries
  command = "rm %s/rests" % root
  print >> logf, command
  logf.flush()
  pid = subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  command = "rm %s/catts" % root
  print >> logf, command
  logf.flush()
  pid = subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  i = 0
  for s in sources:
    command = "cat %s >>%s/catts" % (s,root)
    print >> logf, command
    logf.flush()
    subprocess.call(command, shell=True, stderr=logf)
  command = "ffmpeg -r %d -i %s/catts -f mpegts -r %d %s/rests" % (fps,root,fps,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stderr=logf)
  command = "mv %s/rests %s  " % (root,target)
  print >> logf,  command
  logf.flush()
  subprocess.call(command, shell=True, stderr=logf)



