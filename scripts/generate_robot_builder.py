"""Render the contribution workshop from validated, actual GitHub calendar data."""
from pathlib import Path
import argparse
from datetime import date
import json
import math
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont

if __package__:
    from .calendar_data import Calendar, fetch_calendar, normalize_calendar, column_height, placement_targets
else:
    from calendar_data import Calendar, fetch_calendar, normalize_calendar, column_height, placement_targets

W, H, AA = 1120, 410, 2
FPS, SECONDS = 20, 16
BG = '#0d1117'
TEXT, MUTED = '#e6edf3', '#9aa7b7'
GREEN = '#56d364'

def load_font(size, bold=False):
    candidates = [
        Path('C:/Windows/Fonts') / ('seguisb.ttf' if bold else 'segoeui.ttf'),
        Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size*AA)
    return ImageFont.load_default(size=size*AA)

FONTS = {(size,bold): load_font(size,bold) for size,bold in
         [(13,False),(12,False),(12,True)]}

def p(w, d, z=0):
    return (160 + 16.55*w - 12.6*d, 132 + 3.0*w + 9.2*d - z)

def smooth(a):
    a = max(0, min(1, a))
    return a*a*(3-2*a)

def lerp(a, b, t):
    return a + (b-a)*t

def mix(c1, c2, t):
    a, b = tuple(bytes.fromhex(c1[1:])), tuple(bytes.fromhex(c2[1:]))
    return tuple(round(lerp(x, y, t)) for x, y in zip(a,b))

class Canvas:
    def __init__(self, im):
        self.im, self.draw = im, ImageDraw.Draw(im)
    def xy(self, points):
        return [(round(x*AA), round(y*AA)) for x,y in points]
    def poly(self, points, fill, outline=None, width=1):
        self.draw.polygon(self.xy(points), fill=fill)
        if outline:
            self.draw.line(self.xy(points+[points[0]]), fill=outline, width=round(width*AA), joint='curve')
    def line(self, points, fill, width=1):
        self.draw.line(self.xy(points), fill=fill, width=round(width*AA), joint='curve')
    def ellipse(self, box, fill, outline=None, width=1):
        self.draw.ellipse(tuple(round(v*AA) for v in box), fill, outline, width=round(width*AA))
    def rect(self, box, fill, radius=0, outline=None, width=1):
        self.draw.rounded_rectangle(tuple(round(v*AA) for v in box), radius=round(radius*AA), fill=fill, outline=outline, width=round(width*AA))
    def text(self, xy, text, size=13, fill=MUTED, bold=False, anchor=None):
        self.draw.text((round(xy[0]*AA), round(xy[1]*AA)), text, font=FONTS[size,bold], fill=fill, anchor=anchor)

def column(c, w, d, height, shade, lean=0, lift=0, alpha=1):
    gap = .075
    coords = [(w+gap,d+gap), (w+1-gap,d+gap), (w+1-gap,d+1-gap), (w+gap,d+1-gap)]
    base = [p(a,b,lift) for a,b in coords]
    top = [(x+lean,y-height) for x,y in base]
    side = ['#80d88b','#4fbd63','#2e9b48','#23843b','#1d6b32'][shade-1]
    front = ['#a5ecad','#72db82','#4bc962','#35ac4f','#2b9844'][shade-1]
    cap = ['#c4f5ca','#9aeca7','#77e38a','#57d971','#42cb60'][shade-1]
    c.poly([base[1],base[2],top[2],top[1]],side)
    c.poly([base[2],base[3],top[3],top[2]],front)
    c.poly(top,cap)
    c.line([top[3],top[0],top[1]],mix(cap,'#ffffff',.20),.65)
    # A visible stack seam makes the construction read as placed blocks.
    if height > 19:
        for level in range(12, int(height-1), 12):
            f=level/height
            q=[(base[k][0]+lean*f,base[k][1]-level) for k in [1,2,3]]
            c.line(q, mix(front,'#155b31',.15), .65)

def foundation(calendar):
    im = Image.new('RGB', (W*AA,H*AA), BG)
    c = Canvas(im)
    c.text((W-48,29),f'{calendar.total:,} contributions',12,GREEN,True,anchor='ra')
    # Fixed isometric white board: seven rows by 53 weeks.
    corners=[p(0,0),p(calendar.weeks,0),p(calendar.weeks,7),p(0,7)]
    c.poly([(x+6,y+11) for x,y in corners], '#090c10')
    c.poly([corners[2],corners[3],(corners[3][0],corners[3][1]+4),(corners[2][0],corners[2][1]+4)], '#a4b1bb')
    c.poly([corners[1],corners[2],(corners[2][0],corners[2][1]+4),(corners[1][0],corners[1][1]+4)], '#8998a7')
    c.poly(corners, '#c5d0d9')
    for w in range(calendar.weeks):
        for d in range(7):
            s=.045
            c.poly([p(w+s,d+s),p(w+1-s,d+s),p(w+1-s,d+1-s),p(w+s,d+1-s)], ('#f0f5f3' if (w+d)%3 else '#e8efec') if (w,d) in calendar.days else '#8a979f')
    months = [(pos[0], item.day.strftime('%b')) for pos,item in sorted(calendar.days.items()) if item.day.day == 1]
    for w,month in months:
        x,y = p(w,7.8)
        c.text((x-2,y+11),month,12,anchor='ma')
    return im

def robot(c, w, t, kind, active, phase, renderer):
    x,y=p(w,-2.25)
    bob = math.sin(t*8)*.9 if kind=='travel' else 0
    y+=bob
    c.ellipse((x-24,y+2,x+30,y+12),'#080b0f')
    # The mechanical arm works in front of the robot and toward the board.
    if kind=='place':
        tw,td=renderer.targets[active]
        final=renderer.heights[tw,td]
        destination=p(tw+.5,td+.5,final)
        root=(x-12,y-19)
        reach=smooth(min(1,phase/.30)) * (1-smooth((phase-.82)/.18))
        carry=smooth((phase-.18)/.35)
        hand=(lerp(x-29,destination[0],reach),lerp(y-36,destination[1]-14+14*carry,reach))
        elbow=(lerp(root[0],hand[0],.45)-23, min(root[1],hand[1])-20)
        c.line([root,elbow,hand],'#253244',9)
        c.line([root,elbow,hand],'#a5b5bf',5)
        for j in [root,elbow]:
            c.ellipse((j[0]-4,j[1]-4,j[0]+4,j[1]+4),'#e2ebe8', '#72828c')
        c.line([(hand[0]-5,hand[1]-2),(hand[0]-5,hand[1]+5),(hand[0]-2,hand[1]+8)],'#c9d8d2',2)
        c.line([(hand[0]+5,hand[1]-2),(hand[0]+5,hand[1]+5),(hand[0]+2,hand[1]+8)],'#c9d8d2',2)
        if .10<phase<.51:
            # Top block: drawn in the same isometric basis as the data columns.
            drop=max(0,(1-smooth((phase-.10)/.41))*22)
            column(c,tw,td,8, renderer.calendar.days[tw,td].level,lift=final-8+drop)
    # Little tread base and shoes: no borrowed character or game motif.
    c.rect((x-19,y-4,x+24,y+8),'#384654',7, '#6d7c89')
    for dx in [-10,3,15]:
        c.ellipse((x+dx-4,y-2,x+dx+4,y+6),'#0d1721', '#7e919f')
    c.poly([(x-13,y-30),(x+13,y-30),(x+21,y-24),(x+21,y-5),(x+11,y-1),(x-13,y-6)], '#d5e0dd')
    c.poly([(x+13,y-30),(x+21,y-24),(x+21,y-5),(x+13,y-10)], '#95a8a4')
    c.rect((x-7,y-23,x+8,y-10),'#253b35',3)
    c.line([(x-3,y-16),(x+1,y-12),(x+6,y-20)], GREEN,2)
    # A cuboid head, slightly tipped toward the column being placed.
    tilt=math.sin(phase*math.pi)*2 if kind=='place' else 0
    hy=y-49+tilt
    c.poly([(x-23,hy-14),(x+17,hy-14),(x+25,hy-8),(x+25,hy+15),(x+17,hy+20),(x-23,hy+14)], '#dce8e3')
    c.poly([(x+17,hy-14),(x+25,hy-8),(x+25,hy+15),(x+17,hy+20)], '#9aafaa')
    c.poly([(x-23,hy-14),(x-15,hy-19),(x+25,hy-19),(x+17,hy-14)],'#f0f8f3')
    c.rect((x-18,hy-8,x+12,hy+10),'#14251e',4)
    blink=math.sin(t*2.1)>.995
    for eye in [-9,4]:
        c.rect((x+eye-2,hy-1,x+eye+2,hy+(1 if blink else 5)),GREEN,1)
    c.line([(x-3,hy-19),(x-3,hy-28)],'#a8bdb5',2)
    c.ellipse((x-6,hy-32,x,hy-26),GREEN)

def render(t, renderer):
    im=renderer.base.copy()
    c=Canvas(im)
    w,kind,active,phase=renderer.state(t)
    status='Warming up' if kind=='start' else 'Year complete' if kind in ['rest','reset'] else 'Placing a block' if kind=='place' else 'Building the calendar'
    c.ellipse((851,62,857,68),GREEN)
    c.text((868,57),status,13,TEXT)
    # Chronological build frontier; drawn far-to-near for correct occlusion.
    items=[]
    for (ww,dd),day in renderer.active.items():
        level=day.level
        h,lean=renderer.column_state((ww,dd),t)
        if h>.1:
            items.append((ww*.5+dd,ww,dd,h,level,lean))
    for _,ww,dd,h,level,lean in sorted(items):
        column(c,ww,dd,h,level,lean)
    robot(c,w,t,kind,active,phase,renderer)
    # Clear, restrained impact rings make the final block landing easy to see.
    if kind=='place':
        dt=phase*1.35-.69
        if 0<dt<.35:
            tw,td=renderer.targets[active]
            x,y=p(tw+.5,td+.5,renderer.heights[tw,td]+2)
            r=4+dt*34
            color=mix(GREEN,BG,dt/.35)
            c.ellipse((x-r,y-r*.43,x+r,y+r*.43),None,color,1.2)
    # Fade scene back to the empty white board so the infinite loop resets gently.
    if kind=='reset':
        im=Image.blend(im,renderer.base,smooth(phase))
    if kind=='start':
        im=Image.blend(renderer.base,im,smooth(t/.6))
    return im.resize((W,H),Image.Resampling.LANCZOS)

class WorkshopRenderer:
    def __init__(self, calendar: Calendar):
        self.calendar = calendar
        self.active = {pos: day for pos,day in calendar.days.items() if day.count}
        maximum = max((day.count for day in self.active.values()), default=0)
        self.heights = {pos: column_height(day.count, maximum) for pos,day in self.active.items()}
        self.targets = placement_targets(calendar)
        self.base = foundation(calendar)
        self.segments = [(0,.7,-1,-1,'start',None)]
        self.places = []
        cursor, previous = .7, -1
        travel_budget = 11.95 - 1.35*len(self.targets)
        for index,(week,day) in enumerate(self.targets):
            travel = travel_budget * (week-previous)/(calendar.weeks+2)
            self.segments.append((cursor,cursor+travel,previous,week,'travel',None))
            cursor += travel
            self.places.append(cursor)
            self.segments.append((cursor,cursor+1.35,week,week,'place',index))
            cursor += 1.35
            previous = week
        self.segments.append((cursor,12.65,previous,calendar.weeks+1,'travel',None))
        self.segments.extend([(12.65,15.1,calendar.weeks+1,calendar.weeks+1,'rest',None),
                              (15.1,16,calendar.weeks+1,calendar.weeks+1,'reset',None)])

    def state(self, t):
        for start,end,a,b,kind,target in self.segments:
            if start <= t < end:
                local = (t-start)/(end-start)
                return lerp(a,b,smooth(local)),kind,target,local
        return self.calendar.weeks+1,'rest',None,0

    def frame(self, t):
        return render(t,self)

    def column_state(self, position, t):
        week,day=position
        robot_week,_,_,_=self.state(t)
        final=self.heights[position]
        height=final*smooth((robot_week-week-day*.055+1)/1.1)
        lean=0
        if position in self.targets:
            elapsed=t-self.places[self.targets.index(position)]
            if elapsed<0:
                height=max(0,height-8)
            elif elapsed<.69:
                # The held cap must land on an already completed base.
                height=max(0,final-8)
            else:
                height=final
                dt=elapsed-.69
                lean=6*math.sin(dt*19)*math.exp(-dt*5) if dt<1.1 else 0
        return height,lean


def export_assets(calendar: Calendar, output: Path, fps: int = FPS) -> tuple[Path,Path]:
    renderer = WorkshopRenderer(calendar)
    poster = renderer.frame(13.6)
    palette = poster.quantize(colors=192)
    frames = []
    for n in range(fps*SECONDS):
        # Start with the completed year: static previews still communicate data.
        t = (n/fps+12.65) % SECONDS
        frames.append(renderer.frame(t).quantize(palette=palette,dither=Image.Dither.NONE))
    output.mkdir(parents=True,exist_ok=True)
    gif,png = output/'robot-builder.gif',output/'robot-builder.png'
    with tempfile.TemporaryDirectory(dir=output) as temp:
        temp = Path(temp)
        poster.save(temp/'poster.png')
        frames[0].save(temp/'animation.gif',save_all=True,append_images=frames[1:],
                       duration=round(1000/fps),loop=0,optimize=True,disposal=1)
        # No output changes until fetching, validating and rendering all succeed.
        os.replace(temp/'animation.gif',gif)
        os.replace(temp/'poster.png',png)
    return gif,png


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default='nigelcheong1')
    parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parents[1]/'assets')
    parser.add_argument('--input',type=Path,help='Use an offline GraphQL snapshot (for local reproduction)')
    args = parser.parse_args()
    if args.input:
        snapshot=json.loads(args.input.read_text(encoding='utf-8'))
        payload,start,end = snapshot['response'],date.fromisoformat(snapshot['start']),date.fromisoformat(snapshot['end'])
    else:
        payload,start,end = fetch_calendar(args.username,os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN',''))
    calendar = normalize_calendar(payload,args.username,start,end)
    gif,png = export_assets(calendar,args.output_dir)
    print(f'Rendered {calendar.total} contributions across {len(calendar.days)} days; GIF {gif.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
