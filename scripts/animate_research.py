"""Animate the approved immutable lab plate using clipped pixels and SVG overlays."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
FRONT = 'M334 516L377 515L383 505L402 503L418 511L427 519L425 530L385 533L379 543L338 545L330 535Z'
BACK = 'M351 501L374 499L383 493L398 493L409 499L416 507L405 513L379 511L356 514Z'
STYLE = '''
.typing-front{transform-origin:334px 535px}.typing-back{transform-origin:353px 509px}
.lab-cursor{transform:translate(492px,365px)}.click-feedback{opacity:0;transform-origin:550px 402px}
.right-reticle{transform:translate(1740px,360px)}.monitor-sweep{opacity:0}.key-feedback{opacity:0}
@keyframes typeFront{0%,8%,18%,28%,38%,48%,58%,68%,100%{transform:rotate(0deg)}13%,33%,53%{transform:rotate(-4deg)}}
@keyframes typeBack{0%,18%,28%,38%,48%,58%,68%,100%{transform:rotate(0deg)}23%,43%,63%{transform:rotate(-4deg)}}
@keyframes labCursor{0%,20%,100%{transform:translate(492px,365px)}42%,66%{transform:translate(550px,402px)}82%{transform:translate(520px,380px)}}
@keyframes clickFeedback{0%,44%,62%,100%{opacity:0;transform:scale(.65)}48%{opacity:.7;transform:scale(.65)}60%{opacity:0;transform:scale(1.5)}}
@keyframes monitorSweep{0%,100%{opacity:0;transform:translateY(0)}15%{opacity:.35}80%{opacity:.35;transform:translateY(160px)}90%{opacity:0;transform:translateY(160px)}}
@keyframes reticleDrift{0%,100%{transform:translate(1740px,360px)}50%{transform:translate(1754px,351px)}}
@keyframes keyFeedback{0%,43%,65%,100%{opacity:0}48%,56%{opacity:.5}}
@media(prefers-reduced-motion:no-preference){
.typing-front{animation:typeFront 5s ease-in-out infinite}.typing-back{animation:typeBack 5s ease-in-out infinite}
.lab-cursor{animation:labCursor 8s steps(10,end) infinite}.click-feedback{animation:clickFeedback 8s linear infinite}
.monitor-sweep{animation:monitorSweep 7s linear infinite}.right-reticle{animation:reticleDrift 7s ease-in-out infinite}
.key-feedback{animation:keyFeedback 8s ease-in-out infinite}.right-key{animation-delay:1.4s}
}
'''


def animated_plate(source):
    image = re.search(r'<image\b[^>]+/>', source).group()
    plate = image.replace('<image ', '<image id="lab-plate" ', 1)
    layers = f'''<defs>{plate}
<mask id="lab-base" maskUnits="userSpaceOnUse" x="0" y="0" width="2172" height="724"><rect width="2172" height="724" fill="white"/><path d="{FRONT}" fill="black"/><path d="{BACK}" fill="black"/></mask>
<clipPath id="front-hand"><path d="{FRONT}"/></clipPath><clipPath id="back-hand"><path d="{BACK}"/></clipPath>
<clipPath id="left-monitor"><path d="M450 327H620L588 460H420Z"/></clipPath>
<clipPath id="right-monitor"><path d="M1644 282H1880L1840 452H1589Z"/></clipPath></defs>
<use href="#lab-plate" mask="url(#lab-base)"/>
<g class="typing-back"><use href="#lab-plate" clip-path="url(#back-hand)"/></g>
<g class="typing-front"><use href="#lab-plate" clip-path="url(#front-hand)"/></g>
<g clip-path="url(#left-monitor)">
<g class="lab-cursor"><path d="M0 0V25L7 19L14 29L20 25L13 16H25Z" fill="#e6f6d7" stroke="#123523" stroke-width="3"/></g>
<path class="click-feedback" d="M536 392H564V412H536Z" fill="none" stroke="#b5f77d" stroke-width="3"/>
</g>
<path class="key-feedback" d="M478 491H508L501 509H472Z" fill="#c4ff9a"/>
<g clip-path="url(#right-monitor)"><rect class="monitor-sweep" x="1580" y="283" width="310" height="4" fill="#b5ffab"/>
<g class="right-reticle" fill="none" stroke="#c1ff97" stroke-width="3" opacity=".7"><path d="M-26 -13V-23H-15M15 -23H26V-13M26 13V23H15M-15 23H-26V13"/></g></g>
<path class="key-feedback right-key" d="M1722 491H1750L1743 506H1717Z" fill="#c4ff9a"/>
<rect class="key-feedback right-key" x="2011" y="427" width="24" height="13" fill="#c4ff9a"/>
'''
    result = source.replace(image, layers, 1)
    return result.replace('</style>', STYLE + '</style>', 1)


def main():
    for mobile in (False, True):
        suffix = '-mobile' if mobile else ''
        for still in (False, True):
            old = ASSETS / ('arcade-research-room' + suffix + ('-still' if still else '') + '.svg')
            source = old.read_text(encoding='utf-8')
            target = ASSETS / ('research-workbench' + suffix + ('-still' if still else '') + '.svg')
            result = source if still else animated_plate(source)
            ET.fromstring(result)
            target.write_text(result, encoding='utf-8')
            print(target.name)


if __name__ == '__main__':
    main()
