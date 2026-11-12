#!/usr/bin/env python3
"""Executar apenas os cinco conversores pinados e os gateways conhecidos."""
import os
import sys
from pathlib import Path
MODES={'dmr2ysf':'DMR2YSF','ysf2dmr':'YSF2DMR','dmr2nxdn':'DMR2NXDN','ysf2nxdn':'YSF2NXDN','ysf2p25':'YSF2P25'}
if len(sys.argv)!=3 or sys.argv[1] not in MODES or sys.argv[2] not in ('converter','gateway'):raise SystemExit(2)
mode,kind=sys.argv[1:]
d=Path('/var/lib/2pny/crossmode')/mode
binary=MODES[mode] if kind=='converter' else (d/'gateway-binary').read_text()
if binary not in (*MODES.values(),'YSFGateway','NXDNGateway','P25Gateway'):raise SystemExit(2)
os.chdir(d)
os.execv('/usr/local/bin/'+binary,[binary,str(d/(kind+'.ini'))])
