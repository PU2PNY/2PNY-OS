#!/usr/bin/env python3
"""PROTO-511: compatibilidade mínima com o DMR Gateway raw do host 590c531.

Upstream 7328c9e espera RPTL/RPTC antes de processar DMRD. O host pinado emite
DMRD/DMRP sem esse login. Usar o ID configurado real e remover somente a espera
pelo login local; nunca enviar uma configuração/telemetria inventada.
"""
from pathlib import Path
import subprocess
import sys
root=Path(sys.argv[1]).resolve()
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()=='7328c9e9532d29cf4d9d7d24541d57f825207be4'

def replace(p,old,new):
    text=p.read_text();assert text.count(old)==1,(p,old[:80],text.count(old));p.write_text(text.replace(old,new,1))

for name in ('DMR2YSF','DMR2NXDN'):
    directory=root/name
    old='unsigned int localPort, bool debug)'
    for filename in ('MMDVMNetwork.h','MMDVMNetwork.cpp'):
        replace(directory/filename,old,'unsigned int localPort, unsigned int id, bool debug)')
    replace(directory/'MMDVMNetwork.cpp','m_id(0U),','m_id(id),')
    replace(directory/'MMDVMNetwork.cpp','\tm_netId  = new unsigned char[4U];',
            '\tm_netId  = new unsigned char[4U];\n\tfor (unsigned int i=0U; i<4U; ++i) m_netId[i]=(id >> (24U-8U*i)) & 0xffU;')
    replace(directory/'MMDVMNetwork.cpp','\t\t} else if (::memcmp(m_buffer, "DMRG", 4U) == 0) {',
            '\t\t} else if (length == 4 && ::memcmp(m_buffer, "DMRP", 4U) == 0) {\n'
            '\t\t\tm_socket.write(m_buffer, 4U, m_rptAddress, m_rptPort);\n'
            '\t\t} else if (::memcmp(m_buffer, "DMRG", 4U) == 0) {')
    p=directory/(name+'.cpp');text=p.read_text()
    start=text.index('\tLogMessage("Waiting for MMDVM to connect.....");')
    end=text.index('\tLogMessage("MMDVM has connected");',start)+len('\tLogMessage("MMDVM has connected");')
    replace(p,text[start:end],'\tLogMessage("PU2PNY: interface Gateway local pronta; RF nao verificado");')
    replace(p,'new CMMDVMNetwork(rptAddress, rptPort, localAddress, localPort, debug);',
            'new CMMDVMNetwork(rptAddress, rptPort, localAddress, localPort, m_conf.getDMRId(), debug);')
print('CM_GATEWAY_511_PATCH_OK')
