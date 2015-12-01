import envoy
import re
import time
import os

from datetime import datetime


class Command(object):
    def call(self, cmd, ignore_errors=False):
        res = envoy.run(cmd)
        return res.status_code, res.std_out, res.std_err


class NetworkInfo(Command):

    def network_status(self):
        iwcode, iwconfig, err = self.call("iwconfig", ignore_errors=True)
        wlcode, wlan, err = self.call("ifconfig wlan0", ignore_errors=True)
        etcode, eth, err = self.call("ifconfig eth0", ignore_errors=True)
        ssid = None
        wip = None
        eip = None
        if iwcode == 0 and 'ESSID' in iwconfig:
            essid_match = re.findall('ESSID:"([^"]*)', iwconfig)
            if len(essid_match) != 0:
                ssid = essid_match[0]
        if wlcode == 0 and 'inet addr' in wlan:
            wip = re.findall('inet addr:([^ ]*)', wlan)[0]
        if etcode == 0 and 'inet addr' in eth:
            eip = re.findall('inet addr:([^ ]*)', eth)[0]
        ret = ''
        if ssid:
            ret = ssid
        if wip:
            ret = ret + '\n' + wip
        elif eip:
            ret = ret + eip
        if not ssid and not wip and not eip:
            ret = 'No Network'
        return ret


class Identify(Command):
    """ A class which wraps calls to the external identify process. """

    def __init__(self):
        self.cmd = 'identify'

    def summary(self, filepath):
        code, out, err = self.call(self.cmd + " " + filepath)
        return out

    def mean_brightness(self, filepath):
        code, out, err = self.call(self.cmd + ' -format "%[mean]" ' + filepath)
        return out

class GPhoto(Command):
    """ A class which wraps calls to the external gphoto2 process. """

    def __init__(self):
        self.cmd = '/usr/local/bin/gphoto2'
        self.shutter_choices = None
        self.iso_choices = None

    def get_camera_date_time(self):
        time_str = None
        for cmd_part in ['status', 'settings']:
            code, out, err = self.call("{0} --get-config /main/{1}/datetime"
                                       .format(self.cmd, cmd_part))
            for line in out.split('\n'):
                if not line.startswith('Current:'):
                    continue
                time_str = line.replace('Current:', '').strip()
                try:
                    return time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # The time may instead be a timestamp
                    return datetime.utcfromtimestamp(int(time_str)).timetuple()
        if not time_str:
            raise Exception('No time parsed from ' + out)


    def capture_image_and_download(self, shot=None, image_directory=None):
        code, out, err = self.call(self.cmd + " --capture-image-and-download --filename '%Y%m%d%H%M%S.JPG'")
        print(out)
        filename = None
        for line in out.split('\n'):
            if line.startswith('Saving file as '):
                filename = line.split('Saving file as ')[1]
                filenameWithCnt = "IMG_{:0>4d}.jpg".format(shot)
                os.rename(filename, filenameWithCnt)
                filename = filenameWithCnt
                if not os.path.exists(image_directory):
                  os.makedirs(image_directory)
                os.rename(filename,image_directory+filename)
        return filename

    def get_shutter_speeds(self):
        code, out, err = self.call(self.cmd + " --get-config /main/capturesettings/shutterspeed")
        choices = {}
        current = None
        for line in out.split('\n'):
            if line.startswith('Choice:'):
                choices[line.split(' ')[2]] = line.split(' ')[1]
            if line.startswith('Current:'):
                current = line.split(' ')[1]
        self.shutter_choices = choices
        return current, choices

    def set_shutter_speed(self, secs=None, index=None):
        code, out, err = None, None, None
        if secs:
            if self.shutter_choices == None:
                self.get_shutter_speeds()
            code, out, err = self.call(self.cmd + " --set-config /main/capturesettings/shutterspeed=" + str(self.shutter_choices[secs]))
        if index:
            code, out, err = self.call(self.cmd + " --set-config /main/capturesettings/shutterspeed=" + str(index))

    def get_iso(self):
        code, out, err = self.call(self.cmd + " --get-config /main/imgsettings/iso")
        choices = {}
        current = None
        for line in out.split('\n'):
            if line.startswith('Choice:'):
                choices[line.split(' ')[2]] = line.split(' ')[1]
            if line.startswith('Current:'):
                current = line.split(' ')[1]
        self.iso_choices = choices
        return current, choices

    def set_iso(self, iso=None, index=None):
        code, out, err = None, None, None
        if iso:
            if self.iso_choices == None:
                self.get_iso()
            code, out, err = self.call(self.cmd + " --set-config /main/imgsettings/iso=" + str(self.iso_choices[iso]))
        if index:
            code, out, err = self.call(self.cmd + " --set-config /main/imgsettings/iso=" + str(index))

    def get_model(self):
        code, out, err = self.call(self.cmd + " --summary")
        model = {}
        for line in out.split('\n'):
            if line.startswith('Model:'):
                model = line.split(' ')
                model.pop(0)
        return ' '.join(model)
