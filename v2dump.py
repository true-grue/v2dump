# v2dump.py 20100914
# Author: Peter Sovietov

import sys

Prefix = ''


def dw(buf, d):
    return (ord(buf[d + 3]) << 24) | (ord(buf[d + 2]) << 16)| \
           (ord(buf[d + 1]) << 8) | ord(buf[d])

def delta(buf, d, num):
    return ord(buf[d]) | (ord(buf[d + num]) << 8) | \
            (ord(buf[d + 2 * num]) << 16)

def nt(c, buf, d, num):
    r = []
    t = p = v = 0
    for i in range(d, d + num):        
        t += delta(buf, i, num)
        p = (p + ord(buf[i + 3 * num])) & 0xff
        v = (v + ord(buf[i + 4 * num])) & 0xff
        r += [(t, chr(0x90 | c) + chr(p) + chr(v))]
    return r  

def pc(c, buf, d, num):
    r = []
    t = p = 0
    for i in range(d, d + num):        
        t += delta(buf, i, num)
        p = (p + ord(buf[i + 3 * num])) & 0xff
        r += [(t, chr(0xc0 | c) + chr(p))]
    return r  

def pb(c, buf, d, num):
    r = []
    t = p0 = p1 = 0
    for i in range(d, d + num):        
        t += delta(buf, i, num)
        p0 = (p0 + ord(buf[i + 3 * num])) & 0xff
        p1 = (p1 + ord(buf[i + 4 * num])) & 0xff
        r += [(t, chr(0xe0 | c) + chr(p0) + chr(p1))]
    return r  

def cc(c, n, buf, d, num):
    r = []
    t = p = 0
    for i in range(d, d + num):        
        t += delta(buf, i, num)
        p = (p + ord(buf[i + 3 * num])) & 0xff
        r += [(t, chr(0xb0 | c) + chr(n + 1) + chr(p))]
    return r  

def v2dump(buf):
    d = 0
    v2 = {}
    v2['timediv'] = dw(buf, d)  
    v2['maxtime'] = dw(buf, d + 4)
    gdnum = dw(buf, d + 8)
    d += 12
    v2['gptr'] = buf[d:d + 10 * gdnum]
    d += 10 * gdnum
    for i in range(16):
        v2[i] = {}
        notenum = dw(buf, d)
        d += 4
        if notenum:
            v2[i]['noteptr'] = nt(i, buf, d, notenum)
            d += 5 * notenum
            pcnum = dw(buf, d)
            d += 4
            v2[i]['pcptr'] = pc(i, buf, d, pcnum)
            d += 4 * pcnum
            pbnum = dw(buf, d)
            d += 4
            v2[i]['pbptr'] = pb(i, buf, d, pcnum)
            d += 5 * pbnum
            for j in range(7):
                ccnum = dw(buf, d)
                d += 4               
                v2[i][j] = cc(i, j, buf, d, ccnum)
                d += 4 * ccnum
    size = dw(buf, d)
    d += 4
    v2['globals'] = buf[d:d + size]
    d += size
    size = dw(buf, d)
    d += 4
    v2['patchmap'] = buf[d:d + size]
    return v2

def v2load(name):
    f = open(name, 'rb')
    buf = f.read()
    f.close()
    return v2dump(buf)

def save(name, buf):
    f = open(Prefix + name, 'wb')
    f.write(buf)
    f.close()

def mididelta(t):
    return chr(((t >> 21) & 0x7f) | 0x80) + chr(((t >> 14) & 0x7f) | 0x80) + \
           chr(((t >> 7) & 0x7f) | 0x80) + chr(t & 0x7f)

def miditrack(c, mt):
    r = ''
    t = 0
    s = sorted(c['pcptr'] + c[0] + c[1] + c[2] + c[3] + c[4] + c[5] + c[6] + \
         c['pbptr'] + c['noteptr'])  
    for e in s:
        if e[0] > mt:
            break
        r += mididelta(e[0] - t) + e[1]
        t = e[0]
    r += '\x00\xff\x2f\x00'
    n = len(r)
    return 'MTrk' + chr((n >> 24) & 0xff) + chr((n >> 16) & 0xff) + \
         chr((n >> 8) & 0xff) + chr(n & 0xff) + r

def save_midifile(v2):
    t = ''
    n = 0
    for i in range(16):
        if v2[i]:
            t += miditrack(v2[i], v2['maxtime'])
            n += 1
    save('.mid', 'MThd\0\0\0\6\0\1\0' + chr(n) + '\0\xac' + t)

def save_patch(i, buf):
    name = 'v2p1' + Prefix + str(i)
    buf = name + '\0' * (36 - len(name)) + '\6\0\0\0' + buf
    buf += '\0' * (895 - len(buf))
    save('_' + str(i) + '.v2p', buf)

def save_patchmap(buf):
    i = 0
    patch = begin = dw(buf, i)
    i += 4
    while i < patch:
        end = dw(buf, i)
        save_patch(i / 4, buf[begin:end])
        begin = end
        i += 4
    save_patch(i / 4, buf[begin:])


if len(sys.argv) != 2:
    print 'v2dump by Peter Sovietov\nUsage: v2dump file.v2m'
    sys.exit()

name = sys.argv[1]
Prefix = name.lower().replace('.v2m', '')
v2 = v2load(name)
save_midifile(v2)
save_patchmap(v2['patchmap'])
