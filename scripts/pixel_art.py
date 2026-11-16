"""Authored pixel artwork; shared by the rolling calendar generator."""
import html
from datetime import date, timedelta
from .calendar_data import Calendar

BG, FG, GREEN, MUTED = '#0d1117', '#e6edf3', '#7ee787', '#a4b1be'
colors = {'NONE':'#e4ece5','FIRST_QUARTILE':'#c5f2cd','SECOND_QUARTILE':'#87df9b','THIRD_QUARTILE':'#4dc66b','FOURTH_QUARTILE':'#239c4b'}

FONT = {
 'A':['01110','10001','10001','11111','10001','10001','10001'],
 'B':['11110','10001','10001','11110','10001','10001','11110'],
 'C':['01111','10000','10000','10000','10000','10000','01111'],
 'D':['11110','10001','10001','10001','10001','10001','11110'],
 'E':['11111','10000','10000','11110','10000','10000','11111'],
 'F':['11111','10000','10000','11110','10000','10000','10000'],
 'G':['01111','10000','10000','10111','10001','10001','01111'],
 'H':['10001','10001','10001','11111','10001','10001','10001'],
 'I':['11111','00100','00100','00100','00100','00100','11111'],
 'J':['00111','00010','00010','00010','10010','10010','01100'],
 'K':['10001','10010','10100','11000','10100','10010','10001'],
 'L':['10000','10000','10000','10000','10000','10000','11111'],
 'M':['10001','11011','10101','10101','10001','10001','10001'],
 'N':['10001','11001','11001','10101','10011','10011','10001'],
 'O':['01110','10001','10001','10001','10001','10001','01110'],
 'P':['11110','10001','10001','11110','10000','10000','10000'],
 'Q':['01110','10001','10001','10001','10101','10010','01101'],
 'R':['11110','10001','10001','11110','10100','10010','10001'],
 'S':['01111','10000','10000','01110','00001','00001','11110'],
 'T':['11111','00100','00100','00100','00100','00100','00100'],
 'U':['10001','10001','10001','10001','10001','10001','01110'],
 'V':['10001','10001','10001','10001','10001','01010','00100'],
 'W':['10001','10001','10001','10101','10101','11011','10001'],
 'X':['10001','10001','01010','00100','01010','10001','10001'],
 'Y':['10001','10001','01010','00100','00100','00100','00100'],
 'Z':['11111','00001','00010','00100','01000','10000','11111'],
 '0':['01110','10001','10011','10101','11001','10001','01110'],
 '1':['00100','01100','00100','00100','00100','00100','01110'],
 '2':['01110','10001','00001','00010','00100','01000','11111'],
 '3':['11110','00001','00001','01110','00001','00001','11110'],
 '4':['00010','00110','01010','10010','11111','00010','00010'],
 '5':['11111','10000','10000','11110','00001','00001','11110'],
 '6':['01111','10000','10000','11110','10001','10001','01110'],
 '7':['11111','00001','00010','00100','01000','01000','01000'],
 '8':['01110','10001','10001','01110','10001','10001','01110'],
 '9':['01110','10001','10001','01111','00001','00001','11110'],
 '+':['00000','00100','00100','11111','00100','00100','00000'],
 '-':['00000','00000','00000','11111','00000','00000','00000'],
 '&':['01100','10010','10100','01000','10101','10010','01101'],
 '.':['00000','00000','00000','00000','00000','00110','00110'],
 '’':['010','010','100','000','000','000','000'],
 ':':['00000','00110','00110','00000','00110','00110','00000'],
 '/':['00001','00010','00010','00100','01000','01000','10000'],
 ' ':['000','000','000','000','000','000','000'],
}


def pwidth(value, scale):
    return sum((len(FONT.get(char, FONT[' '])[0])+1)*scale for char in value.upper())-scale


def ptext(value, x, y, scale=3, color=FG, anchor='start'):
    if anchor == 'end': x -= pwidth(value, scale)
    if anchor == 'middle': x -= pwidth(value, scale)/2
    shapes=[]
    for char in value.upper():
        glyph=FONT.get(char, FONT[' '])
        for row,line in enumerate(glyph):
            for col,bit in enumerate(line):
                if bit=='1': shapes.append(f'<rect x="{x+col*scale:g}" y="{y+row*scale:g}" width="{scale:g}" height="{scale:g}"/>')
        x += (len(glyph[0])+1)*scale
    return f'<g fill="{color}" shape-rendering="crispEdges">'+''.join(shapes)+'</g>'


def svg(w,h,title,content,style='',viewbox=None):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{viewbox or f"0 0 {w} {h}"}" role="img"><title>{html.escape(title)}</title><style>{style}</style>{content}</svg>'


def regular_text(x,y,value,size=28,color=FG,weight=400):
    return f'<text x="{x}" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(value)}</text>'


def bot(color=FG,paddle=True):
    grid=[
      '....OOOOOOOO....','...OWWWWWWWWO...','..OWWWWWWWWWWO..','..OWDDDDDDDDWO..',
      '..OWDGGDDGGDWO..','..OWDGGDDGGDWO..','..OWDDDDDDDDWO..','...OWWWWWWWWO...',
      '....OOOOOOOO....','.....OWWWWO.....','...OOWWWWWWOO...','..OWWWWWWWWWWO..',
      '..OWWGGGGGGWWO..','..OWWGGGGGGWWO..','...OWWWWWWWWO...','....OWWWWWWO....',
      '....OOOWWOOO....','...OWWO..OWWO...','...OWWO..OWWO...','..OOOOO..OOOOO..',
    ]
    palette={'O':'#0a1710','W':color,'D':'#13261b','G':'#7ee787'}
    result='<g shape-rendering="crispEdges">'
    for y,line in enumerate(grid):
        for x,v in enumerate(line):
            if v!='.': result+=f'<rect x="{x*4}" y="{y*4}" width="4" height="4" fill="{palette[v]}"/>'
    if paddle:
        result+='<g class="paddle"><rect x="48" y="48" width="18" height="12" fill="#edf5e9"/><rect x="62" y="43" width="8" height="24" fill="#acbd9c"/><path d="M67 23H87V28H92V47H87V52H67V47H62V28H67Z" fill="#8ade53" stroke="#102312" stroke-width="4"/><rect x="71" y="29" width="4" height="4" fill="#315c25"/><rect x="79" y="37" width="4" height="4" fill="#315c25"/></g>'
    return result+'</g>'


def render_calendar(calendar: Calendar, animated=True, mobile=False):
    calendar_start, calendar_end = calendar.start, calendar.end
    origin = calendar_start - timedelta(days=(calendar_start.weekday()+1)%7)
    days = [{'date': item.day.isoformat(), 'contributionCount': item.count,
             'contributionLevel': list(colors)[item.level]}
            for _, item in sorted(calendar.days.items())]
    tiles=''
    for day in days:
        offset=(date.fromisoformat(day['date'])-origin).days
        x,y=50+(offset//7)*18,91+(offset%7)*18
        tiles+=f'<rect data-date="{day["date"]}" data-count="{day["contributionCount"]}" x="{x}" y="{y}" width="15" height="15" fill="{colors[day["contributionLevel"]]}"/>'
    if mobile:
        body='<rect width="520" height="240" fill="#0d1117"/><g transform="translate(0 45) scale(.47)">'+tiles+'</g>'
        body+=ptext(str(calendar.total)+' CONTRIBUTIONS',500,18,3,GREEN,'end')
        body+='<g transform="translate(24 42)"><g class="builder-mobile"><g transform="scale(.4)">'+bot(paddle=False)+'</g><rect x="25" y="15" width="8" height="8" fill="#7ee787"/></g></g>'
        body+=ptext('BUILDING THE CALENDAR',24,169,3)
        body+=regular_text(24,224,f'{calendar_start:%d %b %Y} – {calendar_end:%d %b %Y}',20,MUTED)
        for i,c in enumerate(colors.values()):body+=f'<rect x="{360+i*26}" y="208" width="18" height="18" fill="{c}"/>'
        motion='''@keyframes mobileBuilder{0%,100%{transform:translateX(0)}48%,58%{transform:translateX(405px)}}@media(prefers-reduced-motion:no-preference){.builder-mobile{animation:mobileBuilder 13s steps(45,end) infinite}}'''
        return svg(520,240,f'{calendar.total} CONTRIBUTIONS — {calendar_start} to {calendar_end}',body,motion if animated else '')
    body='<rect width="1120" height="290" fill="#0d1117"/>'+tiles
    body+=ptext(str(calendar.total)+' CONTRIBUTIONS',1070,18,2.4,GREEN,'end')
    body+='<g transform="translate(46 27)"><g class="builder"><g transform="scale(.55)">'+bot(paddle=False)+'</g><rect x="35" y="20" width="10" height="10" fill="#7ee787"/></g></g>'
    body+=ptext('BUILDING THE CALENDAR',50,234,2.3)
    body+=regular_text(50,279,f'{calendar_start:%d %b %Y} – {calendar_end:%d %b %Y}',16,MUTED)
    body+=ptext('LESS',854,239,1.7,MUTED)
    for i,c in enumerate(colors.values()):body+=f'<rect x="{910+i*25}" y="233" width="17" height="17" fill="{c}"/>'
    motion='''@keyframes builder{0%,100%{transform:translateX(0)}48%,58%{transform:translateX(810px)}}@media(prefers-reduced-motion:no-preference){.builder{animation:builder 13s steps(45,end) infinite}}'''
    return svg(1120,290,f'{calendar.total} CONTRIBUTIONS — {calendar_start} to {calendar_end}',body,motion if animated else '')
