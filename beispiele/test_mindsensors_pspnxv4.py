from ev3.mindsensors import PSPNxV4
import unittest
from util import get_input


class TestPSPNxV4(unittest.TestCase):
    def test_PSPNxV4(self):
        get_input('Attach a PSPNxV4 at port 3 then continue')    	
        d = PSPNxV4(3)
        print(d.version)
        print(d.vendor_id)
        print(d.device_id)
        get_input('test button_set_1')
        print(d.button_set_1)
        
        

if __name__ == '__main__':
    unittest.main()
