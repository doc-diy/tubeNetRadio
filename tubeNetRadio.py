#!/usr/bin/python2
# pyhton code for the tubeNetRadio project. tubeNetRadio is a Raspberry Pi
# based internet radio / mp3 player with a minimalistic user interface 
# consisting of just two knobs (no display)
#
# Function:
# 
# Button 1: skip to next radio station 
# Button 2: skip to next album of available mp3 archive
#
# www.doc-diy.net
#
#

import mpd
import RPi.GPIO as GPIO
import os
import time


###############################################################################
# constants for readable code
RADIO          = 0
ALBUMS         = 1
PRESSED        = 0

# name of files where the recently played track/radio is stored
lastsongfile   = "/home/pi/lastsongpos"
lastradiofile  = "/home/pi/lastradiopos"
# file with internet radio station playlist
myplaylist     = "myradiostations" # refers to "myradiostations.m3u" in playlist folder



###############################################################################
# setup GPIO
# pinout in chip nomenclature (BCM)

buttonPin0     = 2
buttonPin1     = 3

GPIO.setmode(GPIO.BCM)

GPIO.setup(buttonPin0, GPIO.IN)
GPIO.setup(buttonPin1, GPIO.IN)


##############################################################################
# connect to mpd server

client = mpd.MPDClient() # create client object (this is how mpd works with 
                         # python)

# Reconnect until successful
while 1:
    try:
        status = client.status()
        #print("Initial connect")
        break
                
    except:
        client.connect("localhost", 6600)
        #print("Initial connect failed ...")
        time.sleep(1)

###############################################################################
# set initial playmode. this setting decides if the player starts as mp3 player 
# or internet radio
playmode = RADIO

# initialize mpd
client.clear()                  # clear playlist
client.update()                 # update library
client.load(myplaylist)         # load playlist with radio stations
client.play()                   # play music
client.repeat(1)                # repeat playlist

###############################################################################
# generate 'recently played' files if missing (at first start for example)
if not os.path.exists(lastsongfile):
    with open(lastsongfile, 'w') as f:
        f.write(str(1))
if not os.path.exists(lastradiofile):
    with open(lastradiofile, 'w') as f:
        f.write(str(1))


###############################################################################
# infinite button polling loop

while True:

    input0 = GPIO.input(buttonPin0)
    input1 = GPIO.input(buttonPin1)

    # because mpd drops the connection automatically it has to be 
    # checked or restablished before any operation. otherwise the 
    # scripts stops
    while 1:
        try:
            status = client.status()
            break
        except:
            client.connect("localhost", 6600)
            print("Reconnect ...")


    ###########################################################################
    if input0 == PRESSED:  # go to album mode or skip album if already in album mode
        if playmode == RADIO: 
            playmode = ALBUMS
            client.clear()
            tracks=client.list('file')   # get all files from data base 
                                         # (doesn't load playlists with radio 
                                         # stations)
            for t in tracks:
                client.add(t)

            # play song lastly played
            with open(lastsongfile, 'r') as f:
                songpos = int(f.read())
            client.play(songpos)

        else:

            # get current song id
            songposcur = int(client.currentsong()['pos'])  # get playlist 
                                          # position of current song

            # create list of albums, replace empty entries with dummy
            plsinfo = client.playlistinfo()  # get all track information for 
                                             # playlist
            plsalbums = []
            for alb in plsinfo:
                tmp = alb.get('album','-no-')  # get albums and replace empty 
                                               # entries by -no-
                plsalbums.append(tmp)

            # get album of current song 
            songalbum = plsalbums[songposcur]

            # go through album list and search for the next song with a 
            # differing album name
            for x in range(songposcur, len(plsalbums)):
                songpos = 0 # go to start of playlist, valid only if if 
                            # statement below fails
                if plsalbums[x] != songalbum:
                    songpos = x
                    break

            client.play(songpos)  # play first song of next album

            # save current song id for next restart
            with open(lastsongfile, 'w') as f:
                f.write(str(songpos))
                f.truncate()        # cuts all previous contents like digits

    ###########################################################################
    elif input1 == PRESSED: # go to radio mode or skip station if in radio mode
        if playmode == ALBUMS: 
            playmode = RADIO
            client.clear()
            client.load(myplaylist)  # load playlist with radio stations

            with open(lastradiofile, 'r') as f: # load radio station recently 
                                                # played
                songpos = int(f.read())
            client.play(songpos)
        else:    # already in radio mode
            client.next() 

            # save current sond id for next restart
            songpos = int(client.currentsong()['pos'])
            print(str(songpos))
            with open(lastradiofile, 'w') as f:
                f.write(str(songpos))
                f.truncate()      # cuts all previous contents like digits


    time.sleep(0.1)   # results in 10 Hz polling of button



