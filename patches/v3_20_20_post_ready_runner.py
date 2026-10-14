from pathlib import Path

base=Path(__file__).with_name('v3_20_20_post_ready_fixes.py')
src=base.read_text(encoding='utf-8')

start_marker="node,a,b=_span(s,'_draw_theme_art'); chunk=s[a:b]"
section=src.find('# PACÍFICO: keep calm identity')
a=src.find(start_marker,section)
b=src.find('# Structural/static validation.',a)
if section<0 or a<0 or b<0:
    raise SystemExit('v3.20.20 runner: could not locate Pacific patch section')

replacement=r'''# Locate the Pacífico motion branch by its unique comment instead of matching
# the whole branch byte-for-byte. Earlier theme patches can alter whitespace.
motion_marker='# Movimento quase imperceptível:'
mid=s.find(motion_marker)
if mid<0:
    raise SystemExit('v3.20.20 Pacific motion marker missing')
branch_start=s.rfind('            elif theme_name=="Pacífico":',0,mid)
branch_end=s.find('            elif theme_name=="ZKStrap Core":',mid)
if branch_start<0 or branch_end<0 or branch_end<=branch_start:
    raise SystemExit('v3.20.20 Pacific motion branch bounds missing')
new_branch='''            elif theme_name=="Pacífico":
                # Movimento calmo, mas perceptível: duas marés em parallax,
                # reflexos viajando na superfície e bolhas subindo devagar.
                for row,(yyf,speed,amp) in enumerate(((.59,.095,4.0),(.74,.070,5.2))):
                    pts=[]; yy=int(h*yyf)
                    for x in range(-24,w+32,24):
                        pts += [x,yy+int(math.sin(x/68.0+ph*speed+row*.85)*amp)]
                    if len(pts)>=4:
                        canvas.create_line(*pts,fill=accent if row==0 else self._mix_hex(base,accent2,.68),width=2 if row==0 else 1,smooth=True)
                for j in range(7):
                    px=int((j*143+ph*(3.0+(j%3)*.7))%max(1,w))
                    py=int(h*(.53+(j%4)*.085)+math.sin(ph*.08+j*.9)*3)
                    half=7+(j%3)*5
                    canvas.create_line(px-half,py,px+half,py,fill=accent2 if j%3==0 else self._mix_hex(base,accent,.56),width=1)
                for j in range(5):
                    bx=int(w*(.18+j*.16)+math.sin(ph*.055+j)*8)
                    by=int(h*.90-((ph*(1.1+j*.16)+j*37)%max(24,int(h*.40))))
                    r=2+(j%2)
                    canvas.create_oval(bx-r,by-r,bx+r,by+r,outline=self._mix_hex(base,accent2,.72),width=1)
                shimmer_x=int(w*(.79+math.sin(ph*.035)*.015))
                canvas.create_line(shimmer_x,int(h*.34),shimmer_x,int(h*.49),fill=self._mix_hex(base,accent2,.52),width=1)
'''
s=s[:branch_start]+new_branch+s[branch_end:]

'''

patched=src[:a]+replacement+src[b:]
code=compile(patched,str(base),'exec')
exec(code,globals(),globals())
