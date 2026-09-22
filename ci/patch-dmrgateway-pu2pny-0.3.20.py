#!/usr/bin/env python3
"""Patch pinned upstream DMRGateway with PU2PNY RF group controls on either RF timeslot.

Safe scope: adds group-call aliases for the existing XLX UserControl path.
Existing private-call controls remain untouched.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
p=root/"DMRGateway.cpp"
s=p.read_text()
anchor='''			} else if ((dstId <= (m_xlxBase + 26U) || dstId == (m_xlxBase + 1000U)) && flco == FLCO::USER_USER && slotNo == m_xlxSlot && dstId >= m_xlxBase && m_xlxUserControl) {'''
if anchor not in s:
    raise SystemExit("PU2PNY DMRGateway patch anchor not found")

block='''			} else if (flco == FLCO::GROUP && (slotNo == 1U || slotNo == 2U) && m_xlxUserControl && dstId >= 4000U && dstId <= 4026U) {
				// PU2PNY easy RF control: TG4000 unlinks and TG4001..TG4026
				// select XLX modules A..Z.  Both RF timeslots may request control; only the terminator changes state,
				// so voice frames never trigger repeated relinks.
				unsigned char type = data.getDataType();
				if (type == DT_TERMINATOR_WITH_LC) {
					unsigned int room = dstId;
					if (room == 4000U) {
						if (m_xlxReflector != 4000U)
							writeXLXLink(srcId, 4000U, m_xlxNetwork);
						m_xlxReflector = 4000U;
						LogMessage("PU2PNY, XLX module control: unlinked by TG4000");
						if (m_xlxVoice != nullptr)
							m_xlxVoice->unlinked();
					} else {
						if (m_xlxReflector != 4000U && m_xlxReflector != room)
							writeXLXLink(srcId, 4000U, m_xlxNetwork);
						if (m_xlxReflector != room)
							writeXLXLink(srcId, room, m_xlxNetwork);
						m_xlxReflector = room;
						char c = ('A' + (room % 100U)) - 1U;
						LogMessage("PU2PNY, XLX module control: TG%u -> module %c", room, c);
						if (m_xlxVoice != nullptr)
							m_xlxVoice->linkedTo(m_xlxNumber, room);
					}
					if (m_xlxReflector != m_xlxRoom)
						m_xlxRelink.start();
					else
						m_xlxRelink.stop();
				}
				m_extStatus[slotNo].m_status = DMRGW_STATUS::XLXREFLECTOR;
				timer[slotNo]->setTimeout(rfTimeout);
				timer[slotNo]->start();
			} else if (flco == FLCO::GROUP && (slotNo == 1U || slotNo == 2U) && m_xlxUserControl && dstId == 4099U) {
				// PU2PNY INFO command.  Program TG4099 in the radio as "I" or
				// "INFO". The gateway speaks the current XLX/module after PTT.
				unsigned char type = data.getDataType();
				if (type == DT_TERMINATOR_WITH_LC && m_xlxVoice != nullptr) {
					if (m_xlxConnected && m_xlxReflector >= 4001U && m_xlxReflector <= 4026U)
						m_xlxVoice->linkedTo(m_xlxNumber, m_xlxReflector);
					else
						m_xlxVoice->unlinked();
					LogMessage("PU2PNY, XLX status voice requested by TG4099");
				}
				m_extStatus[slotNo].m_status = DMRGW_STATUS::XLXREFLECTOR;
				timer[slotNo]->setTimeout(rfTimeout);
				timer[slotNo]->start();
'''+anchor

s=s.replace(anchor,block,1)
p.write_text(s)
print("PU2PNY DMRGateway TG4000-4026 + TG4099 patch applied")
