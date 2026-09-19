#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])

# Extend XLXVoice with a small AMBE-native time announcement.
h=root/"XLXVoice.h"
s=h.read_text()
if "announceTime" not in s:
    anchor="\tvoid unlinked();\n"
    if anchor not in s:
        raise SystemExit("XLXVoice.h anchor not found")
    s=s.replace(anchor,anchor+"\tvoid announceTime(unsigned int hour, unsigned int minute);\n",1)
    h.write_text(s)

cpp=root/"XLXVoice.cpp"
s=cpp.read_text()
if "CXLXVoice::announceTime" not in s:
    anchor="void CXLXVoice::unlinked()\n{\n"
    pos=s.find(anchor)
    if pos < 0:
        raise SystemExit("XLXVoice.cpp anchor not found")
    method='''void CXLXVoice::announceTime(unsigned int hour, unsigned int minute)
{
\tchar digits[5U];
\t::sprintf(digits, "%02u%02u", hour % 24U, minute % 60U);
\tstd::vector<std::string> words;
\tif (m_positions.count("time") > 0U)
\t\twords.push_back("time");
\tfor (unsigned int i = 0U; i < 4U; i++)
\t\twords.push_back(std::string(1U, digits[i]));
\tcreateVoice(words);
}

'''
    s=s[:pos]+method+s[pos:]
    cpp.write_text(s)

p=root/"DMRGateway.cpp"
s=p.read_text()
if "PU2PNY_HOURLY_VOICE" not in s:
    inc="#include <vector>\n"
    if inc not in s:
        raise SystemExit("DMRGateway include anchor not found")
    s=s.replace(inc,inc+"#include <ctime>\n",1)
    loop="\twhile (!m_killed) {"
    if loop not in s:
        raise SystemExit("DMRGateway loop anchor not found")
    s=s.replace(loop,"\t// PU2PNY_HOURLY_VOICE\n\tint pu2pnyLastHour = -1;\n\n\twhile (!m_killed) {",1)
    clock='''\t\tif (m_xlxVoice != nullptr)
\t\t\tm_xlxVoice->clock(ms);
'''
    if clock not in s:
        raise SystemExit("DMRGateway voice clock anchor not found")
    hourly=clock+'''\n\t\t// PU2PNY hourly voice uses the same selected AMBE language pack.
\t\t// The marker is managed by the local settings API.  It never
\t\t// interrupts an active RF/network slot.
\t\tif (m_xlxVoice != nullptr && ::access("/var/lib/2pny/voice-hourly.enabled", R_OK) == 0) {
\t\t\ttime_t now = ::time(nullptr);
\t\t\tstruct tm localtm;
\t\t\t::localtime_r(&now, &localtm);
\t\t\tif (localtm.tm_min == 0 && localtm.tm_hour != pu2pnyLastHour && m_extStatus[m_xlxSlot].m_status == DMRGW_STATUS::NONE) {
\t\t\t\tm_xlxVoice->announceTime((unsigned int)localtm.tm_hour, (unsigned int)localtm.tm_min);
\t\t\t\tpu2pnyLastHour = localtm.tm_hour;
\t\t\t\tLogMessage("PU2PNY, hourly time voice %02d:%02d", localtm.tm_hour, localtm.tm_min);
\t\t\t}
\t\t}
'''
    s=s.replace(clock,hourly,1)
    p.write_text(s)

print("PU2PNY hourly AMBE voice patch applied")
