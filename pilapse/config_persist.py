import os
import json

class Settings:
    def __init__(self,lastConfig,lastShot,brightness,flashOn):
        self.lastConfig=lastConfig
        self.lastShot=lastShot
        self.lastBrightness=brightness
        self.flashOn=flashOn


class Persist():

    #http://stackoverflow.com/a/10352231/810944
    @staticmethod
    def touchopen(filename, *args, **kwargs):
        # Open the file in R/W and create if it doesn't exist. *Don't* pass O_TRUNC
        fd = os.open(filename, os.O_RDWR | os.O_CREAT)

        # Encapsulate the low-level file descriptor in a python file object
        return os.fdopen(fd, *args, **kwargs)
   
    @staticmethod
    def readLastConfig(initConfig, initShot, initFlash, filename):
        with Persist.touchopen(filename, "r+") as target:
            try:
                settings = json.load(target)
            except ValueError:
                settings = {
                  "lastConfig": initConfig,
                  "lastShot":   initShot,
                  "flashOn": initFlash
                }
            return settings
   
    @staticmethod
    def writeLastConfig(lastConfig, initShot, brightness, filename, flashOn):
        with Persist.touchopen(filename, "r+") as target:
           
            settings=Settings(lastConfig, initShot, brightness, flashOn)
            json.dump(vars(settings), target, sort_keys=True, indent=4)
            #json.dump('settings': [{'lastConfig': lastConfig, 'lastShot': initShot]}, target, sort_keys=True, indent=4)
            # Write the new value and truncate
            #target.seek(0)
            #target.write(str(lastConfig))
            target.truncate()
