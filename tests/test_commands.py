#!/usr/bin/env python

import os
import time
import unittest

from pilapse.commands import GPhoto, Identify, NetworkInfo

try:
    from unittest.mock import DEFAULT, MagicMock, patch
except ImportError:  # Fallback for Python != 3.x
    from mock import DEFAULT, MagicMock, patch


class EnvoyMock(MagicMock):
    status_code = 0
    std_err = None
    std_out = ''

    @classmethod
    def test_data(cls, test_filename):
        full_path = os.path.join(os.getcwd(), 'tests', 'files', test_filename)
        with open(full_path, 'r') as test_file:
            return ''.join(test_file.readlines())


class IWCMock(EnvoyMock):
    std_out = EnvoyMock.test_data('iwc')


class IFCWLAN0Mock(EnvoyMock):
    std_out = EnvoyMock.test_data('ifcwlan0')


class IFCETH0Mock(EnvoyMock):
    std_out = EnvoyMock.test_data('ifceth0')


class NetworkInfoTestCase(unittest.TestCase):
    def setUp(self):
        self.network_info = NetworkInfo()

    @patch('envoy.run')
    def test_no_network(self, mock_run):
        self.assertEqual(self.network_info.network_status(), 'No Network')
        mock_run.assert_any_call('iwconfig')
        mock_run.assert_any_call('ifconfig wlan0')
        mock_run.assert_any_call('ifconfig eth0')

    @patch('envoy.run', side_effect=[DEFAULT, DEFAULT, IFCETH0Mock])
    def test_ethernet(self, mock_run):
        self.assertEqual(self.network_info.network_status(), '10.1.10.15')
        mock_run.assert_any_call('iwconfig')
        mock_run.assert_any_call('ifconfig wlan0')
        mock_run.assert_any_call('ifconfig eth0')

    @patch('envoy.run', side_effect=[IWCMock, IFCWLAN0Mock, IFCETH0Mock])
    def test_wlan(self, mock_run):
        network_status = self.network_info.network_status()
        self.assertEqual('146csbr\n10.1.10.15', network_status)

        mock_run.assert_any_call('iwconfig')
        mock_run.assert_any_call('ifconfig wlan0')
        mock_run.assert_any_call('ifconfig eth0')


class IdentifyTestCase(unittest.TestCase):
    def setUp(self):
        self.identify = Identify()

    def test_identify(self):
        full_path = os.path.join(os.getcwd(), 'tests', 'files', 'test.jpg')
        self.assertTrue(self.identify.summary(full_path).startswith(
            full_path +
            ' JPEG 3696x2448 3696x2448+0+0 8-bit DirectClass 4.754MB 0.000u'))

    def test_brightness(self):
        full_path = os.path.join(os.getcwd(), 'tests', 'files', 'test.jpg')
        self.assertTrue(
            self.identify.mean_brightness(full_path).startswith('2563'))

    @patch('envoy.run')
    def test_brightness_run(self, mock_run):
        self.identify.mean_brightness('test.jpg')
        mock_run.assert_called_once_with('identify -format "%[mean]" test.jpg')


class DatetimeMock(EnvoyMock):
    std_out = EnvoyMock.test_data('datetime')


class GetShutterSpeedMock(EnvoyMock):
    std_out = EnvoyMock.test_data('get_shutter_speed')


class GetISOMock(EnvoyMock):
    std_out = EnvoyMock.test_data('get_iso')


class GPhotoTestCase(unittest.TestCase):
    def setUp(self):
        self.gphoto = GPhoto()
        self.get_choices()

    @patch('envoy.run', new_callable=GetShutterSpeedMock)
    def test_get_shutter_speed(self, mock_run):
        self.gphoto.get_shutter_speeds()
        self.assertEqual(mock_run.call_count, 1)
        mock_run.assert_called_once_with(
            self.gphoto.cmd +
            ' --get-config /main/capturesettings/shutterspeed')
        self.assertEqual(sorted(list(self.gphoto.shutter_choices.items())),
                         sorted(list(self.shutter_choices.items())))

    @patch('envoy.run', side_effect=[GetShutterSpeedMock, DEFAULT, DEFAULT])
    def test_set_shutter_speed(self, mock_run):
        self.gphoto.set_shutter_speed(secs='2.0000s')
        for call in ['{0} --get-config /main/capturesettings/shutterspeed',
                     '{0} --set-config /main/capturesettings/shutterspeed=40']:
            mock_run.assert_any_call(call.format(self.gphoto.cmd))
        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(sorted(list(self.gphoto.shutter_choices.items())),
                         sorted(list(self.shutter_choices.items())))
        self.gphoto.set_shutter_speed(index='2')
        mock_run.assert_any_call(
            self.gphoto.cmd +
            ' --set-config /main/capturesettings/shutterspeed=2')
        self.assertEqual(mock_run.call_count, 3)

    @patch('envoy.run', new_callable=GetISOMock)
    def test_get_iso(self, mock_run):
        self.gphoto.get_iso()
        self.assertEqual(mock_run.call_count, 1)
        mock_run.assert_called_once_with(
            self.gphoto.cmd + ' --get-config /main/imgsettings/iso')
        self.assertEqual(sorted(list(self.gphoto.iso_choices.items())),
                         sorted(list(self.iso_choices.items())))

    @patch('envoy.run', side_effect=[GetISOMock, DEFAULT, DEFAULT])
    def test_set_iso(self, mock_run):
        self.gphoto.set_iso(iso='200')
        for call in ['{0} --get-config /main/imgsettings/iso',
                     '{0} --set-config /main/imgsettings/iso=3']:
            mock_run.assert_any_call(call.format(self.gphoto.cmd))
        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(sorted(list(self.gphoto.iso_choices.items())),
                         sorted(list(self.iso_choices.items())))
        self.gphoto.set_iso(index='2')
        mock_run.assert_any_call(
            self.gphoto.cmd + ' --set-config /main/imgsettings/iso=2')
        self.assertEqual(mock_run.call_count, 3)

    @patch('envoy.run', new_callable=DatetimeMock)
    def test_get_camera_time(self, mock_run):
        _time = self.gphoto.get_camera_date_time()
        self.assertEqual(
            _time, time.strptime("2015-11-29 06:59:12", "%Y-%m-%d %H:%M:%S"))
        mock_run.assert_called_once_with(
            '/usr/local/bin/gphoto2 --get-config /main/status/datetime')

    @patch('envoy.run', side_effect=[DEFAULT, DatetimeMock])
    def test_get_nikon_d7000_time(self, mock_run):
        # A Nikon D7000 (for one example) has a different path for datetime
        _time = self.gphoto.get_camera_date_time()
        self.assertEqual(
            _time, time.strptime("2015-11-29 06:59:12", "%Y-%m-%d %H:%M:%S"))
        mock_run.assert_any_call(
            '/usr/local/bin/gphoto2 --get-config /main/status/datetime')
        mock_run.assert_any_call(
            '/usr/local/bin/gphoto2 --get-config /main/settings/datetime')

    def get_choices(self):
        """ Put this data at the end so it doesn't get in the way """
        self.iso_choices = {
            '100': '0',
            '125': '1',
            '160': '2',
            '200': '3',
            '250': '4',
            '320': '5',
            '400': '6',
            '500': '7',
            '640': '8',
            '800': '9',
            '1000': '10',
            '1250': '11',
            '1600': '12',
            '2000': '13',
            '2500': '14',
            '3200': '15',
            '4000': '16',
            '5000': '17',
            '6400': '18',
            '8000': '19',
            '12800': '21',
            '25600': '22',
            '10000': '20'
        }
        self.shutter_choices = {
            '0.0001s': '0',
            '0.0002s': '1',
            '0.0003s': '2',
            '0.0004s': '3',
            '0.0005s': '4',
            '0.0006s': '5',
            '0.0008s': '6',
            '0.0010s': '7',
            '0.0012s': '8',
            '0.0015s': '9',
            '0.0020s': '10',
            '0.0025s': '11',
            '0.0031s': '12',
            '0.0040s': '13',
            '0.0050s': '14',
            '0.0062s': '15',
            '0.0080s': '16',
            '0.0100s': '17',
            '0.0125s': '18',
            '0.0166s': '19',
            '0.0200s': '20',
            '0.0250s': '21',
            '0.0333s': '22',
            '0.0400s': '23',
            '0.0500s': '24',
            '0.0666s': '25',
            '0.0769s': '26',
            '0.1000s': '27',
            '0.1250s': '28',
            '0.1666s': '29',
            '0.2000s': '30',
            '0.2500s': '31',
            '0.3333s': '32',
            '0.4000s': '33',
            '0.5000s': '34',
            '0.6250s': '35',
            '0.7692s': '36',
            '1.0000s': '37',
            '1.3000s': '38',
            '1.6000s': '39',
            '2.0000s': '40',
            '2.5000s': '41',
            '3.0000s': '42',
            '4.0000s': '43',
            '5.0000s': '44',
            '6.0000s': '45',
            '8.0000s': '46',
            '10.0000s': '47',
            '13.0000s': '48',
            '15.0000s': '49',
            '20.0000s': '50',
            '25.0000s': '51',
            '30.0000s': '52',
            '429496.7295s': '53',
        }


if __name__ == '__main__':
    unittest.main()
