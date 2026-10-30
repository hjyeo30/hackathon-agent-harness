"""Analyze actual ASCII PGM pixels; coordinates are x=column, y=row."""
import argparse
from collections import deque
import json
from pathlib import Path
import time


def read_pgm(path):
    with open(path, encoding='ascii') as stream:
        text=stream.read(20_000_001)
    if len(text)>20_000_000: raise ValueError('PGM exceeds example input budget')
    tokens=' '.join(line.split('#',1)[0] for line in text.splitlines()).split()
    if len(tokens)<4 or tokens[0]!='P2': raise ValueError('expected P2 ASCII PGM')
    try: width,height,maximum=map(int,tokens[1:4]); values=list(map(int,tokens[4:]))
    except ValueError: raise ValueError('PGM dimensions and pixels must be integers')
    if width<=0 or height<=0 or width*height>1_000_000: raise ValueError('invalid image dimensions')
    if maximum!=255: raise ValueError('example requires 8-bit max value 255')
    if len(values)!=width*height or any(not 0<=v<=255 for v in values): raise ValueError('invalid pixel count or range')
    return [values[y*width:(y+1)*width] for y in range(height)]


def components(pixels, threshold=128, connectivity=4):
    if connectivity not in (4,8) or not 0<=threshold<=255: raise ValueError('invalid analysis parameters')
    if not pixels or not pixels[0] or any(len(row)!=len(pixels[0]) for row in pixels): raise ValueError('rectangular nonempty image required')
    if any(type(v) is not int or not 0<=v<=255 for row in pixels for v in row): raise ValueError('8-bit integer pixels required')
    height,width=len(pixels),len(pixels[0])
    offsets=[(1,0),(-1,0),(0,1),(0,-1)]
    if connectivity==8: offsets += [(1,1),(1,-1),(-1,1),(-1,-1)]
    seen=set(); found=[]
    for y in range(height):
        for x in range(width):
            if (x,y) in seen or pixels[y][x]<threshold: continue
            queue=deque([(x,y)]); seen.add((x,y)); points=[]
            while queue:
                px,py=queue.popleft(); points.append((px,py))
                for dx,dy in offsets:
                    nx,ny=px+dx,py+dy
                    if 0<=nx<width and 0<=ny<height and (nx,ny) not in seen and pixels[ny][nx]>=threshold:
                        seen.add((nx,ny));queue.append((nx,ny))
            xs,ys=zip(*points)
            found.append({'area':len(points),'bbox':[min(xs),min(ys),max(xs),max(ys)]})
    return found


def write_overlay(path,pixels,regions):
    height,width=len(pixels),len(pixels[0]); scale=40
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (width*scale,height*scale,width*scale,height*scale)]
    for y,row in enumerate(pixels):
        for x,value in enumerate(row):
            parts.append('<rect x="%d" y="%d" width="40" height="40" fill="rgb(%d,%d,%d)" stroke="#888"/>' % (x*scale,y*scale,value,value,value))
    for region in regions:
        x0,y0,x1,y1=region['bbox']
        parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="red" stroke-width="3"/>' % (x0*scale+2,y0*scale+2,(x1-x0+1)*scale-4,(y1-y0+1)*scale-4))
    parts.append('</svg>');Path(path).write_text('\n'.join(parts),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',nargs='?',default='fixtures/diagonal-edge.pgm')
    parser.add_argument('--connectivity',type=int,choices=[4,8],default=4)
    parser.add_argument('--output',default=None,help='Optional local SVG overlay path')
    args=parser.parse_args();start=time.perf_counter();stage='decode'
    try:
        pixels=read_pgm(args.image);stage='label';regions=components(pixels,connectivity=args.connectivity)
        if args.output:
            stage='overlay';Path(args.output).parent.mkdir(parents=True,exist_ok=True);write_overlay(args.output,pixels,regions)
    except (ValueError,OSError) as exc:
        print(json.dumps({'status':'FAIL','stage':stage,'error_type':type(exc).__name__,'error':str(exc)}));return 1
    print(json.dumps({'status':'PASS','regions':regions,'metrics':{'width_px':len(pixels[0]),'height_px':len(pixels),'regions':len(regions),'foreground_px':sum(r['area'] for r in regions),'duration_ms':(time.perf_counter()-start)*1000},'stage_summary':['decode_pgm','validate_shape','threshold_inclusive','connected_components'] + (['overlay'] if args.output else [])}));return 0

if __name__=='__main__':raise SystemExit(main())
