#!/usr/bin/env python3
import importlib.util
spec=importlib.util.spec_from_file_location('apply','runtime/display/apply.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
saved={'type':'nextion_mmdvm','enabled':True,'requested_layout':3}
r=m.select_persisted_modem_display({},saved,{})
assert r['class']=='nextion_mmdvm' and r['source']=='saved_user_profile' and r['physical_confirmed'] is False
assert m.select_persisted_modem_display({'class':'oled'},saved,{})=={'class':'oled'}
assert m.select_persisted_modem_display({},saved,{'enabled':False})=={}
assert m.select_persisted_modem_display({}, {'type':'nextion_mmdvm','enabled':False,'requested_layout':3}, {})=={}
assert m.select_persisted_modem_display({}, {'type':'nextion_mmdvm','enabled':True,'requested_layout':2}, {})=={}
assert m.select_persisted_modem_display({'class':'nextion_mmdvm'},saved,{})=={'class':'nextion_mmdvm'}
print('DISPLAY_PERSISTED_PROFILE_TEST_PASS')
