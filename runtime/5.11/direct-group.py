#!/usr/bin/env python3
"""P2P-511: DMR em malha direta; descoberta BEP5, sem relay de áudio.

O código do grupo nunca é anunciado. Exige segredo aleatório com pelo menos
128 bits. Estado conectado só após receber pacote autenticado. NAT simétrico
pode impedir conexão; DHT não resolve essa limitação.
"""
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import selectors
import socket
import struct
import time
from pathlib import Path
try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
except ImportError:
    ChaCha20Poly1305 = None

BOOTSTRAP = [('router.bittorrent.com', 6881), ('router.utorrent.com', 6881), ('dht.transmissionbt.com', 6881)]


def encode(v):
    if isinstance(v, int):
        return b'i'+str(v).encode()+b'e'
    if isinstance(v, bytes):
        return str(len(v)).encode()+b':'+v
    if isinstance(v, list):
        return b'l'+b''.join(encode(i) for i in v)+b'e'
    if isinstance(v, dict):
        return b'd'+b''.join(encode(k)+encode(v[k]) for k in sorted(v))+b'e'
    raise ValueError('tipo BEP5 inválido')


def decode(raw):
    if len(raw) > 8192:
        raise ValueError('BEP5 grande')
    def parse(i, depth=0):
        if depth > 8 or i >= len(raw):
            raise ValueError('BEP5 inválido')
        c = raw[i:i+1]
        if c == b'i':
            j = raw.index(b'e', i); return int(raw[i+1:j]), j+1
        if c in (b'd', b'l'):
            out = {} if c == b'd' else []; i += 1
            while raw[i:i+1] != b'e':
                value, i = parse(i, depth+1)
                if isinstance(out, dict):
                    if not isinstance(value, bytes): raise ValueError('chave inválida')
                    item, i = parse(i, depth+1); out[value] = item
                else: out.append(value)
            return out, i+1
        j = raw.index(b':', i); n = int(raw[i:j]); i = j+1
        if n < 0 or i+n > len(raw): raise ValueError('comprimento inválido')
        return raw[i:i+n], i+n
    out, end = parse(0)
    if end != len(raw) or not isinstance(out, dict): raise ValueError('BEP5 inválido')
    return out


class Channel:
    def __init__(self, code):
        if not re.fullmatch(r'[A-Za-z0-9_-]{22,128}', code):
            raise ValueError('use o código aleatório gerado para o grupo')
        self.infohash = hashlib.sha1(('pu2pny-direct-v1:'+code).encode()).digest()
        key = hashlib.sha256(('pu2pny-direct-key-v1:'+code).encode()).digest()
        self.key = key
        self.node = secrets.token_bytes(16)
        self.cipher = ChaCha20Poly1305(hmac.digest(key, self.node, 'sha256')) if ChaCha20Poly1305 else None
        self.counter = 0
        self.replay = {}

    def pack(self, payload, encrypt=None):
        self.counter += 1
        use_cipher = self.cipher is not None and encrypt is not False
        header = b'PNY1'+self.node+struct.pack('!Q', self.counter)+(b'C' if use_cipher else b'H')
        if use_cipher:
            payload=self.cipher.encrypt(self.node[:4]+header[20:28],payload,header)
        packet=header+payload
        return packet+hmac.digest(self.key,packet,'sha256')

    def unpack(self, raw):
        if len(raw) < 62 or len(raw) > 256 or raw[:4] != b'PNY1': raise ValueError('pacote inválido')
        node, count = raw[4:20], struct.unpack('!Q', raw[20:28])[0]
        if node == self.node or count == 0: raise ValueError('eco')
        if not hmac.compare_digest(raw[-32:],hmac.digest(self.key,raw[:-32],'sha256')):raise ValueError('autenticação')
        payload=raw[29:-32]
        if raw[28:29]==b'C':
            if not ChaCha20Poly1305:raise ValueError('cifra indisponível')
            payload=ChaCha20Poly1305(hmac.digest(self.key,node,'sha256')).decrypt(node[:4]+raw[20:28],payload,raw[:29])
        elif raw[28:29]!=b'H':raise ValueError('cifra desconhecida')
        high, mask = self.replay.get(node, (0, 0))
        if count > high:
            mask = ((mask << min(64, count-high)) | 1) & ((1 << 64)-1); high = count
        else:
            delta = high-count
            if delta >= 64 or mask & (1 << delta): raise ValueError('replay')
            mask |= 1 << delta
        if len(self.replay) >= 64 and node not in self.replay: raise ValueError('limite de pares')
        self.replay[node] = (high, mask)
        return payload


class Group:
    def __init__(self, code, bind=('0.0.0.0', 43072), host_bind=('127.0.0.1', 62031), host=('127.0.0.1', 62032), bootstrap=BOOTSTRAP):
        self.channel = Channel(code)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); self.sock.bind(bind); self.sock.setblocking(False)
        self.radio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); self.radio.bind(host_bind); self.radio.setblocking(False)
        self.host = host
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.sock, selectors.EVENT_READ, 'net'); self.sel.register(self.radio, selectors.EVENT_READ, 'rf')
        self.dht_id = secrets.token_bytes(20)
        self.peers = {}; self.nodes = {}; self.queried = set(); self.pending = {}
        self.bootstrap = bootstrap; self.lookup_due = 0; self.status_due = 0; self.budget = 0
        self.stream = None; self.stream_until = 0

    def add_peer(self, addr, public=True):
        ip = ipaddress.ip_address(addr[0])
        if public and not ip.is_global: return
        if not 0 < addr[1] <= 65535 or len(self.peers) >= 32 or addr == self.sock.getsockname(): return
        self.peers.setdefault(addr, {'seen': -1e12, 'next': 0, 'cipher':False, 'since': time.monotonic()})

    def query(self, addr, name, args):
        if len(self.pending) >= 8: return
        t = secrets.token_bytes(4)
        self.pending[t] = (addr, name, time.monotonic())
        self.sock.sendto(encode({b't': t, b'y': b'q', b'q': name, b'a': {b'id': self.dht_id, **args}, b'ro': 1}), addr)

    def discovery(self, raw, addr):
        obj = decode(raw); t = obj.get(b't'); pending = self.pending.get(t)
        if not pending or addr != pending[0]: return
        del self.pending[t]
        row = obj.get(b'r')
        if not isinstance(row, dict): return
        if pending[1] == b'get_peers':
            for value in row.get(b'values', [])[:32]:
                if isinstance(value, bytes) and len(value) == 6:
                    self.add_peer((socket.inet_ntoa(value[:4]), struct.unpack('!H',value[4:])[0]))
            nodes = row.get(b'nodes', b'')
            if isinstance(nodes, bytes):
                for i in range(0, min(len(nodes), 26*64)-25, 26):
                    ip = socket.inet_ntoa(nodes[i+20:i+24]); port = struct.unpack('!H',nodes[i+24:i+26])[0]
                    if ipaddress.ip_address(ip).is_global and port:
                        nodeid=nodes[i:i+20];endpoint=(ip,port)
                        self.nodes[endpoint]=nodeid
                        if len(self.nodes)>64:
                            worst=max(self.nodes,key=lambda a:self.distance(self.nodes[a]))
                            del self.nodes[worst]
            token = row.get(b'token')
            if isinstance(token, bytes) and 0 < len(token) <= 128:
                self.query(addr, b'announce_peer', {b'info_hash': self.channel.infohash, b'token': token,
                                                  b'port': self.sock.getsockname()[1], b'implied_port': 1})

    def distance(self,nodeid):
        return int.from_bytes(nodeid,'big') ^ int.from_bytes(self.channel.infohash,'big') if len(nodeid)==20 else 1<<160

    def tick(self):
        now = time.monotonic()
        self.pending = {t: p for t, p in self.pending.items() if now-p[2] < 8}
        if now >= self.lookup_due:
            self.lookup_due = now+300; self.budget=64; self.queried=set()
            for host, port in self.bootstrap:
                try:
                    self.nodes.setdefault((socket.gethostbyname(host),port),b'')
                except OSError: pass
        for addr in sorted(set(self.nodes)-self.queried,key=lambda a:self.distance(self.nodes[a]))[:max(0,8-len(self.pending))]:
            if self.budget <= 0: break
            self.queried.add(addr); self.budget -= 1
            try: self.query(addr, b'get_peers', {b'info_hash': self.channel.infohash})
            except OSError: pass
        for addr, p in list(self.peers.items()):
            if now-p['since'] > 900 and now-p['seen'] > 90:
                del self.peers[addr]; continue
            if now >= p['next']:
                try: self.sock.sendto(self.channel.pack(b'hello:C' if self.channel.cipher else b'hello:H',False), addr)
                except OSError: pass
                p['next'] = now+(25 if now-p['seen'] < 75 else 5)

    def step(self, timeout=1):
        self.tick()
        for key, _ in self.sel.select(timeout):
            try: raw, addr = key.fileobj.recvfrom(8193)
            except OSError: continue
            if key.data == 'rf':
                if addr != self.host: continue
                if raw[:4] == b'DMRP':
                    self.radio.sendto(raw, self.host)
                elif len(raw) == 55 and raw[:4] == b'DMRD':
                    if not self.accept_stream(('rf', raw[16:20])): continue
                    for peer, state in self.peers.items():
                        if time.monotonic()-state['seen'] < 75:
                            try: self.sock.sendto(self.channel.pack(raw,state['cipher']),peer)
                            except OSError: pass
            elif raw[:1] == b'd':
                try: self.discovery(raw, addr)
                except (ValueError, IndexError, KeyError, TypeError, OSError): pass
            elif raw[:4] == b'PNY1':
                try: payload = self.channel.unpack(raw)
                except Exception: continue
                self.add_peer(addr, public=False)
                if addr not in self.peers: continue
                self.peers[addr]['seen'] = time.monotonic()
                if payload in (b'hello:C',b'hello:H',b'ack:C',b'ack:H'):
                    self.peers[addr]['cipher']=bool(payload.endswith(b':C') and self.channel.cipher)
                    if payload.startswith(b'hello:'):
                        self.sock.sendto(self.channel.pack(b'ack:C' if self.channel.cipher else b'ack:H',False),addr)
                elif len(payload) == 55 and payload[:4] == b'DMRD' and self.accept_stream((addr, payload[16:20])):
                    self.radio.sendto(payload, self.host)

    def accept_stream(self, stream):
        now = time.monotonic()
        if now < self.stream_until and stream != self.stream: return False
        self.stream = stream; self.stream_until = now+1
        return True

    def status(self):
        now = time.monotonic()
        return {'encryption': 'ChaCha20-Poly1305' if self.channel.cipher else 'HMAC: áudio sem cifra',
                'relay': False, 'peers': [{'endpoint': f'{ip}:{port}',
                 'state': 'conectado P2P' if now-p['seen'] < 75 else 'não foi possível conectar direto' if now-p['since'] > 90 else 'procurando',
                 'via': ('UDP direto · cifrado' if p['cipher'] else 'UDP direto · autenticado sem cifra') if now-p['seen'] < 75 else '—'} for (ip,port),p in self.peers.items()]}

    def close(self):
        self.sel.close(); self.sock.close(); self.radio.close()


def main():
    state = Path('/var/lib/2pny')
    settings = json.loads((state/'direct-group.json').read_text())
    if settings.get('enabled') is not True: return
    # Não iniciar fora do perfil DMR nem se estiver concorrendo com crossmode.
    cfg = json.loads((state/'config.json').read_text())
    if cfg.get('protocol') != 'DMR': raise SystemExit('Direct grupo exige perfil DMR')
    group = Group(settings['code'])
    try:
        while True:
            group.step()
            now = time.monotonic()
            if now >= group.status_due:
                group.status_due = now+5
                path=Path('/run/2pny/direct-group-status.json'); tmp=path.with_suffix('.tmp')
                tmp.write_text(json.dumps(group.status(), ensure_ascii=False)); os.chmod(tmp,0o644); os.replace(tmp,path)
    finally: group.close()

if __name__ == '__main__': main()
