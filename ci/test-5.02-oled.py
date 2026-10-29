#!/usr/bin/env python3
"""OLED data/geometry tests with an in-memory bus substitute, never HW approval."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw, ImageFont

spec=importlib.util.spec_from_file_location('oled502',Path(__file__).resolve().parents[1]/'runtime/5.02/oled.py')
oled=importlib.util.module_from_spec(spec)
spec.loader.exec_module(oled)

class OLEDTests(unittest.TestCase):
    def test_real_values_and_missing_metrics(self):
        cfg={'callsign':'TEST123','dmr_id':'1234567','rx_hz':438125000,'tx_hz':430125000}
        live={'active':{'source':'TEST-CALL','target':'TG 91','protocol':'DMR','slot':2,'color_code':1,
                        'ber':0.4,'rssi':-103,'started_unix_ms':1000000,'operator':{'id':'7654321'}}}
        text='\n'.join(oled.rows(live,cfg,{},now=1012))
        for value in ('TEST123','1234567','438.125000','430.125000','TEST-CALL','TG 91','7654321','0.4','-103','0:12'):
            self.assertIn(value,text)
        missing='\n'.join(oled.rows({'standby':True},{},{},now=1012))
        self.assertIn('BER %: -',missing)
        self.assertIn('RSSI dBm: -',missing)

    def test_full_width_text_is_wrapped_without_loss(self):
        font=ImageFont.load_default()
        value='WWWWWWWWWWWWWWWWWWWWWWWWWWWW'
        fitted=oled.fit_rows([value],font)
        self.assertEqual(''.join(fitted),value)
        for line in fitted:
            box=font.getbbox(line)
            self.assertLessEqual(box[2]-box[0],124)

    def test_both_panel_heights_and_rotation(self):
        for height in (32,64):
            class Driver:
                h=height
                font=ImageFont.load_default()
                def show_image(self,image):self.image=image
            driver=Driver()
            driver.Image=Image;driver.ImageDraw=ImageDraw
            with patch.object(oled,'network_status',return_value={}):
                with patch.object(oled.time,'monotonic',return_value=100):
                    page,total=oled.render(driver,{'standby':True},{'callsign':'TEST'}, {})
                    self.assertEqual(page,0)
                with patch.object(oled.time,'monotonic',return_value=104):
                    page,_=oled.render(driver,{'standby':True},{'callsign':'TEST'}, {})
                    self.assertEqual(page,1)
                self.assertEqual(driver.image.size,(128,height))
                self.assertGreater(total,1)

    def test_active_protocol_is_never_guessed_from_configuration(self):
        class Driver:
            h=64
            font=ImageFont.load_default()
            def show_image(self,image):pass
        driver=Driver();driver.Image=Image;driver.ImageDraw=ImageDraw
        seen=[];original=oled.ascii_text
        def record(value):seen.append(value);return original(value)
        with patch.object(oled,'network_status',return_value={}), patch.object(oled,'ascii_text',side_effect=record):
            oled.render(driver,{'active':{'source':'TEST','mode':'tx'}},{'protocol':'DMR'}, {})
        self.assertTrue(seen[-1].startswith('- TX '),seen[-1])

if __name__=='__main__':unittest.main()
