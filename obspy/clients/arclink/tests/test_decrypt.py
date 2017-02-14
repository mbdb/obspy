# -*- coding: utf-8 -*-
"""
The obspy.clients.arclink.client test suite.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA

import os
import unittest

import numpy as np

from obspy.clients.arclink import Client
from obspy.clients.arclink.client import DCID_KEY_FILE, ArcLinkException
from obspy.clients.arclink.decrypt import hasM2Crypto, hasPyCrypto
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.util import NamedTemporaryFile

HAS_CRYPTO = hasM2Crypto or hasPyCrypto


@unittest.skipIf(not HAS_CRYPTO, 'm2crypto or pycrypto required')
class ClientTestCase(unittest.TestCase):
    """
    Test cases for L{obspy.clients.arclink.client.Client}.
    """
    def test_get_waveform_with_dcid_key(self):
        """
        """
        # test server for encryption
        client1 = Client(host="webdc.eu", port=36000, user="test@obspy.org",
                         dcid_keys={'BIA': 'OfH9ekhi'})
        # public server
        client2 = Client(host="webdc.eu", port=18001, user="test@obspy.org")
        # request data
        start = UTCDateTime(2010, 1, 1, 10, 0, 0)
        end = start + 100
        stream1 = client1.get_waveforms('GE', 'APE', '', 'BHZ', start, end)
        stream2 = client2.get_waveforms('GE', 'APE', '', 'BHZ', start, end)
        # compare results
        np.testing.assert_array_equal(stream1[0].data, stream2[0].data)
        self.assertEqual(stream1[0].stats, stream2[0].stats)

    def test_get_waveform_with_dcid_key_file(self):
        """
        Tests various DCID key file formats (with space or equal sign). Also
        checks if empty lines or comment lines are ignored.
        """
        # 1 - using = sign between username and password
        with NamedTemporaryFile() as tf:
            dcidfile = tf.name
            with open(dcidfile, 'wt') as fh:
                fh.write('#Comment\n\n\nTEST=XYZ\r\nBIA=OfH9ekhi\r\n')
            # test server for encryption
            client1 = Client(host="webdc.eu", port=36000,
                             user="test@obspy.org", dcid_key_file=dcidfile)
            # public server
            client2 = Client(host="webdc.eu", port=18001,
                             user="test@obspy.org")
        # request data
        start = UTCDateTime(2010, 1, 1, 10, 0, 0)
        end = start + 100
        stream1 = client1.get_waveforms('GE', 'APE', '', 'BHZ', start, end)
        stream2 = client2.get_waveforms('GE', 'APE', '', 'BHZ', start, end)
        # compare results
        np.testing.assert_array_equal(stream1[0].data, stream2[0].data)
        self.assertEqual(stream1[0].stats, stream2[0].stats)
        # 2 - using space between username and password
        with NamedTemporaryFile() as tf:
            dcidfile = tf.name
            with open(dcidfile, 'wt') as fh:
                fh.write('TEST XYZ\r\nBIA OfH9ekhi\r\n')
            # test server for encryption
            client1 = Client(host="webdc.eu", port=36000,
                             user="test@obspy.org", dcid_key_file=dcidfile)
            # public server
            client2 = Client(host="webdc.eu", port=18001,
                             user="test@obspy.org")
        # request data
        start = UTCDateTime(2010, 1, 1, 10, 0, 0)
        end = start + 100
        stream1 = client1.get_waveforms('GE', 'APE', '', 'BHZ', start, end)
        stream2 = client2.get_waveforms('GE', 'APE', '', 'BHZ', start, end)
        # compare results
        np.testing.assert_array_equal(stream1[0].data, stream2[0].data)
        self.assertEqual(stream1[0].stats, stream2[0].stats)

    @unittest.skipIf(os.path.isfile(DCID_KEY_FILE),
                     '$HOME/dcidpasswords.txt already exists')
    def test_get_waveform_with_default_dcid_key_file(self):
        """
        Use $HOME/dcidpasswords.txt.
        """
        dcidfile = DCID_KEY_FILE
        fh = open(dcidfile, 'wt')
        fh.write('TEST=XYZ\r\nBIA=OfH9ekhi\r\n')
        fh.close()
        # test server for encryption
        client1 = Client(host="webdc.eu", port=36000, user="test@obspy.org")
        # public server
        client2 = Client(host="webdc.eu", port=18001, user="test@obspy.org")
        # clean up dcid file
        os.remove(dcidfile)
        # request data
        start = UTCDateTime(2010, 1, 1, 10, 0, 0)
        end = start + 100
        stream1 = client1.get_waveforms('GE', 'APE', '', 'BHZ', start, end)
        stream2 = client2.get_waveforms('GE', 'APE', '', 'BHZ', start, end)
        # compare results
        np.testing.assert_array_equal(stream1[0].data, stream2[0].data)
        self.assertEqual(stream1[0].stats, stream2[0].stats)

    def test_get_waveform_unknown_user(self):
        """
        Unknown user raises an ArcLinkException: DENIED.
        """
        client = Client(host="webdc.eu", port=36000, user="unknown@obspy.org")
        # request data
        start = UTCDateTime(2010, 1, 1, 10, 0, 0)
        end = start + 100
        self.assertRaises(ArcLinkException, client.get_waveforms, 'GE', 'APE',
                          '', 'BHZ', start, end)

    def test_get_waveform_wrong_password(self):
        """
        A wrong password password raises a "EVPError: bad decrypt".
        """
        client = Client(host="webdc.eu", port=36000, user="test@obspy.org",
                        dcid_keys={'BIA': 'WrongPassword'})
        # request data
        start = UTCDateTime(2010, 1, 1, 10, 0, 0)
        end = start + 100
        self.assertRaises(EVPError, client.get_waveforms, 'GE', 'APE', '',
                          'BHZ', start, end)

    def test_get_waveform_no_password(self):
        """
        No password raises a "EVPError: bad decrypt".
        """
        client = Client(host="webdc.eu", port=36000, user="test@obspy.org",
                        dcid_keys={'BIA': ''})
        # request data
        start = UTCDateTime(2010, 1, 1, 10, 0, 0)
        end = start + 100
        self.assertRaises(EVPError, client.get_waveforms, 'GE', 'APE', '',
                          'BHZ', start, end)


def suite():
    return unittest.makeSuite(ClientTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
