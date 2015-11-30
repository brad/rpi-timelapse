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
        self.assertEqual(self.identify.mean_brightness(full_path), '2563.09\n')

    @patch('envoy.run')
    def test_brightness_run(self, mock_run):
        self.identify.mean_brightness('test.jpg')
        mock_run.assert_called_once_with('identify -format "%[mean]" test.jpg')


class DatetimeMock(EnvoyMock):
    std_out = EnvoyMock.test_data('datetime')


class GetShutterSpeedMock(EnvoyMock):
    std_out = 'Label: Shutter Speed\nType: MENU\nCurrent: 30\nChoice: 0 Bulb\nChoice: 4 2'


class GPhotoTestCase(unittest.TestCase):
    def setUp(self):
        self.gphoto = GPhoto()

    @patch('envoy.run', side_effect=[GetShutterSpeedMock, DEFAULT, DEFAULT])
    def test_set_shutter_speed(self, mock_run):
        self.gphoto.set_shutter_speed(secs='2')
        for call in ['{0} --get-config /main/capturesettings/shutterspeed',
                     '{0} --set-config /main/capturesettings/shutterspeed=2']:
            mock_run.assert_any_call(call.format(self.gphoto.cmd))
        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(self.gphoto.shutter_choices, {'2': '4', 'Bulb': '0'})
        self.gphoto.set_shutter_speed(secs='2')
        self.assertEqual(mock_run.call_count, 3)

    @patch('envoy.run', new_callable=DatetimeMock)
    def test_get_camera_time(self, mock_run):
        _time = self.gphoto.get_camera_date_time()
        self.assertEqual(
            _time, time.strptime("2015-11-28 22:59:12", "%Y-%m-%d %H:%M:%S"))
        mock_run.assert_called_once_with(
            '/usr/local/bin/gphoto2 --get-config /main/status/datetime')

    @patch('envoy.run', side_effect=[DEFAULT, DatetimeMock])
    def test_get_nikon_d7000_time(self, mock_run):
        # A Nikon D7000 (for one example) has a different path for datetime
        _time = self.gphoto.get_camera_date_time()
        self.assertEqual(
            _time, time.strptime("2015-11-28 22:59:12", "%Y-%m-%d %H:%M:%S"))
        mock_run.assert_any_call(
            '/usr/local/bin/gphoto2 --get-config /main/status/datetime')
        mock_run.assert_any_call(
            '/usr/local/bin/gphoto2 --get-config /main/settings/datetime')



if __name__ == '__main__':
    unittest.main()
