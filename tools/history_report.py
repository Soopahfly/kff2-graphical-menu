#!/usr/bin/env python3
"""Read a copied KFF2 G3 journal and print counts, or export them as CSV.

Example: python3 tools/history_report.py .KFF2-history --csv game-stats.csv
Only the verified prefix is used if the final record is incomplete or corrupt.
"""
import argparse,csv,json,struct,sys,zlib
from pathlib import Path
HEADER=struct.Struct('<4sHBBIIIHH')

def read_history(path):
    stats={};sequence=0;warning=None
    with Path(path).open('rb') as f:
        while True:
            header=f.read(HEADER.size)
            if not header:break
            if len(header)!=HEADER.size:
                warning='Incomplete tail ignored';break
            magic,length,flags,version,seq,total,random,pathlen,reserved=HEADER.unpack(header)
            if magic!=b'KF3H' or version!=1:
                if sequence==0:raise ValueError('Unrecognised history format')
                warning='Unrecognised tail ignored';break
            if not 0<pathlen<1006 or length!=HEADER.size+pathlen+4 or flags&~1 or reserved:
                warning='Invalid tail ignored';break
            body=f.read(pathlen+4)
            if len(body)!=pathlen+4 or zlib.crc32(header+body[:-4])!=int.from_bytes(body[-4:],'little'):
                warning='Incomplete or checksum-invalid tail ignored';break
            if seq<=sequence or total==0 or random>total or b'\0' in body[:-4]:
                warning='Invalid record tail ignored';break
            sequence=seq;name=body[:-4].decode('cp437')
            stats[name]={'path':name,'launches':total,'random_launches':random,
                         'manual_launches':total-random,'last_launch':seq,
                         'last_source':'random' if flags&1 else 'manual'}
    return sorted(stats.values(),key=lambda x:x['path']),warning

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('history',type=Path);p.add_argument('--csv',type=Path);a=p.parse_args()
    try:rows,warning=read_history(a.history)
    except (OSError,ValueError) as e:p.exit(1,str(e)+'\n')
    if warning:print(warning,file=sys.stderr)
    if a.csv:
        with a.csv.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['path','launches','random_launches','manual_launches','last_launch','last_source']);w.writeheader();w.writerows(rows)
    else:print(json.dumps(rows,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
