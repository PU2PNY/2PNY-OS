#!/usr/bin/env python3
"""PU2PNY 0.3.16 DMRGateway voice arbiter.

Give generated connection/status voice exclusive NETWORK->RF ownership of its
slot while WAITING/SENDING. RF->network and the other slot are untouched.
Fails closed at build time if the pinned upstream anchors change.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve()
xh=root/"XLXVoice.h"; xc=root/"XLXVoice.cpp"
dh=root/"DynVoice.h"; dc=root/"DynVoice.cpp"; gw=root/"DMRGateway.cpp"
for p in (xh,xc,dh,dc,gw):
    if not p.is_file(): raise SystemExit(f"missing {p}")

def once(path,old,new):
    s=path.read_text()
    if old not in s: raise SystemExit(f"voice-arbiter anchor missing in {path.name}: {old[:80]!r}")
    if s.count(old)!=1: raise SystemExit(f"voice-arbiter non-unique anchor in {path.name}")
    path.write_text(s.replace(old,new,1))

once(xh,
"""\tbool read(CDMRData& data);

\tvoid clock(unsigned int ms);""",
"""\tbool read(CDMRData& data);
\tbool isActive() const;

\tvoid clock(unsigned int ms);""")

once(xc,
"""void CXLXVoice::clock(unsigned int ms)
{""",
"""bool CXLXVoice::isActive() const
{
\treturn m_status != XLXVOICE_STATUS::NONE;
}

void CXLXVoice::clock(unsigned int ms)
{""")

once(dh,
"""\tbool read(CDMRData& data);

\tvoid abort();""",
"""\tbool read(CDMRData& data);
\tbool isActive(unsigned int slot) const;

\tvoid abort();""")

once(dc,
"""void CDynVoice::clock(unsigned int ms)
{""",
"""bool CDynVoice::isActive(unsigned int slot) const
{
\treturn m_slot == slot && m_status != DYNVOICE_STATUS::NONE;
}

void CDynVoice::clock(unsigned int ms)
{""")

once(gw,
"""\t\tif (m_networkXlxEnabled && (m_xlxNetwork != nullptr)) {
\t\t\tret = m_xlxNetwork->read(data);
\t\t\tif (ret) {
\t\t\t\tif (m_extStatus[m_xlxSlot].m_status == DMRGW_STATUS::NONE ||
\t\t\t\t\tm_extStatus[m_xlxSlot].m_status == DMRGW_STATUS::XLXREFLECTOR
\t\t\t\t) {""",
"""\t\tif (m_networkXlxEnabled && (m_xlxNetwork != nullptr)) {
\t\t\tret = m_xlxNetwork->read(data);
\t\t\tif (ret) {
\t\t\t\t// PU2PNY-0.3.16 VOICE_PRIORITY: connection/status voice owns
\t\t\t\t// the XLX slot while queued or speaking. Drop only competing
\t\t\t\t// NETWORK->RF audio; RF->network remains untouched.
\t\t\t\tif ((m_xlxVoice != nullptr) && m_xlxVoice->isActive()) {
\t\t\t\t\tLogDebug("PU2PNY, system voice priority: suppressing XLX network audio on slot %u", m_xlxSlot);
\t\t\t\t} else if (m_extStatus[m_xlxSlot].m_status == DMRGW_STATUS::NONE ||
\t\t\t\t\tm_extStatus[m_xlxSlot].m_status == DMRGW_STATUS::XLXREFLECTOR
\t\t\t\t) {""")

once(gw,
"""\t\t\tif (m_networkEnabled[i] && (m_dmrNetworks[i] != nullptr)) {
\t\t\t\tret = m_dmrNetworks[i]->read(data);
\t\t\t\tif(m_trunkingEnabled && data.getMessageFlag()) {""",
"""\t\t\tif (m_networkEnabled[i] && (m_dmrNetworks[i] != nullptr)) {
\t\t\t\tret = m_dmrNetworks[i]->read(data);
\t\t\t\tif (ret) {
\t\t\t\t\tunsigned int voiceSlot = data.getSlotNo();
\t\t\t\t\tbool voiceBusy = (m_xlxVoice != nullptr) && (voiceSlot == m_xlxSlot) && m_xlxVoice->isActive();
\t\t\t\t\tif (!voiceBusy) {
\t\t\t\t\t\tfor (std::vector<CDynVoice*>::iterator vit = m_dynVoices.begin(); vit != m_dynVoices.end(); ++vit) {
\t\t\t\t\t\t\tif ((*vit)->isActive(voiceSlot)) { voiceBusy = true; break; }
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\tif (voiceBusy) {
\t\t\t\t\t\tLogDebug("PU2PNY, system voice priority: suppressing network audio on slot %u", voiceSlot);
\t\t\t\t\t\tret = false;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tif(m_trunkingEnabled && data.getMessageFlag()) {""")

for p,marker in (
    (xh,"bool isActive() const;"),
    (xc,"return m_status != XLXVOICE_STATUS::NONE;"),
    (dh,"bool isActive(unsigned int slot) const;"),
    (dc,"m_status != DYNVOICE_STATUS::NONE"),
    (gw,"PU2PNY-0.3.16 VOICE_PRIORITY"),
):
    if marker not in p.read_text(): raise SystemExit(f"verification failed: {marker}")

print("PATCH_DMRGATEWAY_VOICE_ARBITER_0316_OK")
