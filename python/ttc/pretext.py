#! /usr/bin/python
# -*- coding: utf-8 -*-

import math
import Image
import subprocess

fps = 25
logf = open('ttpretext.log','w')


def makeMP4Pretext(root,duration,filename,soundname,target,vbitrate,abitrate,tw,th):
# Compute number of frame in shortest sequence
  primes = [2,3,5,7,11,13,17,19,23,29,31]
  totalFrames = math.ceil(fps * duration)

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
  command = "ffmpeg -i %s/img%%02d.png -vb %d -ab %d -s %dx%d -r %d %s/tmpmp4.mp4" % (root,(vbitrate*1000),(abitrate*1000),tw,th,fps,root)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Create complete video sequence
  print >> logf, "Concat %d times" % numberOfSeq
  command = "MP4Box -fps %d -cat %s/tmpmp4.mp4 %s/vtot.mp4" % (fps,root,root)
  print >> logf, command
  logf.flush()
  for i in range(numberOfSeq): subprocess.call(command, shell=True, stdout=logf, stderr=logf)

# Create complete sound sequence
  secs = int(duration)
  print >> logf, "Concat %d times" % secs
  command = "MP4Box -cat %s %s/atot.mp4" % (soundname,root)
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


  command = "mv %s/resmp4.mp4 %s  " % (root,target)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)



def makeOGGPretext(source,target):
# Convert mp4 to ogg
  command = 'ffmpeg2theora %s -o %s -c 2 -H 24000 -F 25' % (source,target)
  print >> logf, command
  logf.flush()
  subprocess.call(command, shell=True, stdout=logf, stderr=logf)

def glueMP4Pretext(root,sources,target):
# Remove old temporaries
  command = "rm %s/resmp4.mp4" % root
  print >> logf, command
  logf.flush()
  pid = subprocess.call(command, shell=True, stdout=logf, stderr=logf)
  for s in sources:
    command = "MP4Box -fps %d -force-cat -cat %s %s/resmp4.mp4" % (fps,s,root)
    print command
    logf.flush()
    subprocess.call(command, shell=True, stderr=logf)
  command = "mv %s/resmp4.mp4 %s  " % (root,target)
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

