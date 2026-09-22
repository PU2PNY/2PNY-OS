#!/usr/bin/env python3
"""Patch pinned F4FXL DStarGateway for SEC-025 PU2PNY RF admin requests."""
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve()
p=root/"Common/RepeaterHandler.cpp"
if not p.is_file(): raise SystemExit("missing Common/RepeaterHandler.cpp")
s=p.read_text()

def once(old,new,label):
    global s
    if old not in s: raise SystemExit("anchor missing: "+label)
    if s.count(old)!=1: raise SystemExit("anchor not unique: "+label)
    s=s.replace(old,new,1)

once('#include <cstring>\n#include <boost/algorithm/string.hpp>',
'''#include <cstring>
#include <cstdio>
#include <unistd.h>
#include <sys/stat.h>
#include <boost/algorithm/string.hpp>''',"includes")

anchor='const unsigned int  ETHERNET_ADDRESS_LENGTH = 6U;'
helper=r'''static std::string pu2pnyTrim(const std::string& value)
{
	std::string out(value);
	while (!out.empty() && out.back() == ' ')
		out.pop_back();
	while (!out.empty() && out.front() == ' ')
		out.erase(out.begin());
	return out;
}

static bool pu2pnyAdminCommand(const std::string& yourCall, std::string& action, std::string& argument)
{
	const std::string cmd = pu2pnyTrim(yourCall);
	action.clear();
	argument.clear();

	if (cmd == "PNYARM") {
		action = "ARM";
	} else if (cmd == "PNYOFF") {
		action = "OFF";
	} else if (cmd == "PNYRBT") {
		action = "REBOOT";
	} else if (cmd == "PNYDMR") {
		action = "PROFILE"; argument = "DMR";
	} else if (cmd == "PNYDST") {
		action = "PROFILE"; argument = "DSTAR";
	} else if (cmd == "PNYYSF") {
		action = "PROFILE"; argument = "YSF";
	} else if (cmd == "PNYP25") {
		action = "PROFILE"; argument = "P25";
	} else if (cmd == "PNYNXD") {
		action = "PROFILE"; argument = "NXDN";
	} else if (cmd == "PNYPOC") {
		action = "PROFILE"; argument = "POCSAG";
	} else {
		return false;
	}
	return true;
}

static bool pu2pnyWriteAdminRequest(const std::string& action, const std::string& user, const std::string& argument)
{
	const char* tmp = "/run/2pny/.radio-admin-command.tmp";
	const char* dst = "/run/2pny/radio-admin-command.request";
	FILE* fp = ::fopen(tmp, "w");
	if (fp == NULL)
		return false;

	const std::string caller = pu2pnyTrim(user);
	::fprintf(fp, "%s\t%s\t%s\n", action.c_str(), caller.c_str(), argument.c_str());
	::fflush(fp);
	::fsync(::fileno(fp));
	::fclose(fp);
	::chmod(tmp, 0600);
	if (::rename(tmp, dst) != 0) {
		::unlink(tmp);
		return false;
	}
	return true;
}

'''
once(anchor,helper+anchor,"helper insertion")

old='''	if (m_restricted) {
		sendToOutgoing(header);
		return;
	}

#ifdef USE_CCS'''
new='''	if (m_restricted) {
		sendToOutgoing(header);
		return;
	}

	// PU2PNY SEC-025: reserved URCALL commands are converted only into a
	// local request. A separate one-shot root helper validates MYCALL1 against
	// the configured owner, requires PNYARM, and executes a strict allowlist.
	std::string pu2pnyAction;
	std::string pu2pnyArgument;
	if (pu2pnyAdminCommand(m_yourCall, pu2pnyAction, pu2pnyArgument)) {
		if (pu2pnyWriteAdminRequest(pu2pnyAction, m_myCall1, pu2pnyArgument)) {
			LogInfo("PU2PNY radio admin request %s %s from %s", pu2pnyAction.c_str(), pu2pnyArgument.c_str(), m_myCall1.c_str());
			m_infoAudio->setTempStatus(m_linkStatus, m_linkRepeater, std::string("PU2PNY ") + pu2pnyAction);
			m_infoNeeded = true;
		} else {
			LogWarning("PU2PNY radio admin request could not be queued");
		}
		m_g2Status = G2_LOCAL;
		return;
	}

#ifdef USE_CCS'''
once(old,new,"command dispatch")

p.write_text(s)
for marker in (
    "PU2PNY SEC-025",
    'cmd == "PNYARM"',
    'cmd == "PNYOFF"',
    'cmd == "PNYRBT"',
    'argument = "DMR"',
    'argument = "DSTAR"',
    'radio-admin-command.request',
):
    if marker not in s: raise SystemExit("verification failed: "+marker)
print("PATCH_DSTAR_RADIO_ADMIN_0317_OK")
