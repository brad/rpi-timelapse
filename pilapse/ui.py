from time import sleep

from .Adafruit_CharLCDPlate import Adafruit_CharLCDPlate


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class FakeCharLCDPlate(object):

    RED = "red"
    UP = "q"
    DOWN = "a"
    SELECT = "s"

    def __init__(self):
        self._getch = _GetchUnix()
        pass

    def clear(self):
        print("--LCD Cleared--")

    def message(self, msg):
        print(msg)

    def backlight(self, bl):
        print("Backlight %s" % str(bl))

    def fakeonly_getch(self):
        self._ch = self._getch()

    def buttonPressed(self, button):
        return self._ch == button



class TimelapseUi(object):

    def __init__(self):
        self._lcd = Adafruit_CharLCDPlate()
        #self._lcd = FakeCharLCDPlate()

    def update(self, text):
        self._lcd.clear()
        self._lcd.message(text)
        print(text)

    def show_config(self, configs, current):
        config = configs[current]
        self.update("Timelapse\nT: %s ISO: %s" % (config[1], config[3]))

    def show_status(self, shot, config):
        self.update("Shot %d\nT: %s ISO: %s" % (shot, config[1], config[3]))

    def show_error(self, text):
        self.update(text[0:16] + "\n" + text[16:])
        while not self._lcd.buttonPressed(self._lcd.SELECT):
            sself.backlight(self._lcd.RED)
            sleep(1)

    def main(self, configs, current, network_status):

        while not self._lcd.buttonPressed(self._lcd.SELECT):
          pass

        ready = False
        while not ready:
            while True:
                if (type(self._lcd) == type(FakeCharLCDPlate())):
                    self._lcd.fakeonly_getch()

                if self._lcd.buttonPressed(self._lcd.UP):
                    print("UP")
                    current -= 1
                    if current < 0:
                        current = 0
                    break
                if self._lcd.buttonPressed(self._lcd.DOWN):
                    print("DOWN")
                    current += 1
                    if current >= len(configs):
                        current = len(configs) - 1
                    break
                if self._lcd.buttonPressed(self._lcd.SELECT):
                    print("SELECT")
                    ready = True
                    break
            print("end")
            self.show_config(configs, current)
        return current
