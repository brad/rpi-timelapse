rpi-timelapse
=============

[![Build Status](https://travis-ci.org/brad/rpi-timelapse.svg?branch=master)](https://travis-ci.org/brad/rpi-timelapse)

[![codecov.io](https://codecov.io/github/brad/rpi-timelapse/coverage.svg?branch=master)](https://codecov.io/github/brad/rpi-timelapse?branch=master)


A timelapse camera controller for Raspberry Pi. Testet with Canon EOS 600D and Canon EOS 6D (should work with any camera supported by `gphoto2` with minor tweaks), with an optional UI and controls on the Adafruit LCD Pi plate.


Installation
------------

rpi-timelapse uses `imagemagick`.  To install these dependencies on your pi:

```
$ sudo apt-get install imagemagick
```

and for `gphoto2` see https://github.com/gonzalo/gphoto2-updater/

```
$ wget https://raw.githubusercontent.com/gonzalo/gphoto2-updater/master/gphoto2-updater.sh && chmod +x gphoto2-updater.sh && sudo ./gphoto2-updater.sh
```

for the 16x2 character lcd + keypad

```
sudo apt-get install i2c-tools
```

test the connection with

```
sudo i2cdetect -y 0 (if you are using a version 1 Raspberry Pi)
sudo i2cdetect -y 1 (if you are using a version 2 Raspberry Pi)
```

and enable the GPIO's with

```
sudo raspi-config
```

and follow the instructions in section `A7`

Run
---

python tl.py

Run on boot
-----------

Follow the instructions at <http://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/init-script> using `timelapse` file from this repo instead of `lcd`.


Post-Processing
===============

Here's how to post process the image frames (on Linux, can be run on the Pi itself, but faster on desktop).

Remove flicker if timelapse used many shutter values
----------------------------------------------------

```
for a in *; do echo $a;/usr/bin/mogrify -auto-gamma $a;done
```

Be careful with `auto-gamma` - it works extremely well for sunset / sunrise but can make very dark areas of the scene very noisy.

Convert the resulting JPEGs to a timelapse movie
------------------------------------------------

```
ffmpeg -r 18 -q:v 2 -start_number XXXX -i IMG_%d.JPG output.mp4
```



[Demo Video on YouTube (view in HD)](http://www.youtube.com/watch?v=AZbK4acS5Mc)
