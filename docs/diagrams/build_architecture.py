"""README 구성도 생성. 원본 벡터(SVG)와 한글 폰트를 적용한 PNG를 함께 출력한다."""
from pathlib import Path
from html import escape
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W,H=2400,1510
img=Image.new('RGB',(W,H),'#ffffff'); draw=ImageDraw.Draw(img)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>']
font_dir=Path('C:/Windows/Fonts')
def font(size,bold=False):return ImageFont.truetype(str(font_dir/('malgunbd.ttf' if bold else 'malgun.ttf')),size)
def rect(box,fill,stroke='#d5dfeb',radius=18,width=2):
 x1,y1,x2,y2=box
 draw.rounded_rectangle(box,radius=radius,fill=fill,outline=stroke,width=width)
 svg.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
def text(x,y,value,size=27,color='#283e56',bold=False,center=False):
 f=font(size,bold)
 if center:x-=draw.textlength(value,font=f)/2
 draw.text((x,y),value,font=f,fill=color)
 svg.append(f'<text x="{x}" y="{y+size}" fill="{color}" font-family="Malgun Gothic, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}">{escape(value)}</text>')
def arrow(x1,y1,x2,y2,color='#4773ad',both=False):
 draw.line((x1,y1,x2,y2),fill=color,width=4)
 svg.append(f'<path d="M {x1} {y1} L {x2} {y2}" stroke="{color}" stroke-width="4" fill="none"/>')
 def tip(x,y,a):
  pts=[(x,y),(x-14*math.cos(a-.48),y-14*math.sin(a-.48)),(x-14*math.cos(a+.48),y-14*math.sin(a+.48))]
  draw.polygon(pts,fill=color)
  svg.append('<polygon points="'+' '.join(f'{px},{py}' for px,py in pts)+f'" fill="{color}"/>')
 a=math.atan2(y2-y1,x2-x1);tip(x2,y2,a)
 if both:tip(x1,y1,a+math.pi)

def line(points,color='#4773ad',width=4):
 draw.line(points,fill=color,width=width,joint='curve')
 svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
def ellipse(box,fill='white',stroke='#4773ad',width=4):
 x1,y1,x2,y2=box
 draw.ellipse(box,fill=fill,outline=stroke,width=width)
 svg.append(f'<ellipse cx="{(x1+x2)/2}" cy="{(y1+y2)/2}" rx="{(x2-x1)/2}" ry="{(y2-y1)/2}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
def icon(cx,cy,kind,color):
 if kind=='camera':
  rect((cx-60,cy-36,cx+60,cy+34),'white',color,12,4)
  ellipse((cx-23,cy-25,cx+23,cy+21),'#edf4fd',color,4)
  line([(cx-23,cy+36),(cx-23,cy+48),(cx+23,cy+48)],color,4)
 elif kind=='app':
  rect((cx-66,cy-43,cx+66,cy+38),'white',color,10,4)
  line([(cx-65,cy-19),(cx+65,cy-19)],color,3)
  for dx in [-48,-33,-18]:ellipse((cx+dx-3,cy-33,cx+dx+3,cy-27),color,color,1)
  ellipse((cx-14,cy-7,cx+14,cy+18),'#edf4fd',color,3)
  line([(cx-30,cy+29),(cx-20,cy+19),(cx+20,cy+19),(cx+30,cy+29)],color,3)
 elif kind=='server':
  for dy in [-43,-10,23]:
   rect((cx-60,cy+dy,cx+60,cy+dy+26),'white',color,6,3)
   ellipse((cx-46,cy+dy+9,cx-38,cy+dy+17),color,color,1)
   line([(cx-20,cy+dy+13),(cx+40,cy+dy+13)],color,3)
 elif kind=='ai':
  rect((cx-38,cy-38,cx+38,cy+38),'#edf4fd',color,10,4)
  for t in [-22,0,22]:
   for side in [-1,1]:
    line([(cx+side*38,cy+t),(cx+side*53,cy+t)],color,3)
    line([(cx+t,cy+side*38),(cx+t,cy+side*53)],color,3)
  text(cx,cy-22,'AI',30,color,True,True)
 elif kind=='db':
  rect((cx-54,cy-35,cx+54,cy+31),'white',color,1,3)
  ellipse((cx-54,cy+12,cx+54,cy+49),'white',color,3)
  rect((cx-51,cy-30,cx+51,cy+28),'white','white',0,1)
  ellipse((cx-54,cy-49,cx+54,cy-12),'#edf4fd',color,3)
  line([(cx-54,cy-29),(cx-54,cy+29)],color,3)
  line([(cx+54,cy-29),(cx+54,cy+29)],color,3)
 elif kind=='files':
  rect((cx-45,cy-48,cx+50,cy+35),'#edf4fd',color,6,3)
  rect((cx-60,cy-31,cx+35,cy+52),'white',color,6,3)
  for dy in [-9,7,23]:line([(cx-42,cy+dy),(cx+17,cy+dy)],color,3)
 elif kind=='monitor':
  rect((cx-66,cy-43,cx+66,cy+31),'white',color,8,4)
  line([(cx,cy+31),(cx,cy+49),(cx-30,cy+49),(cx+30,cy+49)],color,4)
  line([(cx-43,cy+10),(cx-22,cy-8),(cx-4,cy+4),(cx+25,cy-23),(cx+43,cy-6)],color,4)
def card(cx,cy,title,kind,detail,color='#3668a8',width=290):
 rect((cx-width/2,cy-105,cx+width/2,cy+112),'white','#d8e3ef',18,2)
 icon(cx,cy-27,kind,color)
 text(cx,cy+36,title,29,color,True,True)
 text(cx,cy+78,detail,22,'#61758a',False,True)
def label(cx,y,title,color='#3668a8',size=25):
 tw=draw.textlength(title,font=font(size,True))
 rect((cx-tw/2-12,y-3,cx+tw/2+12,y+size+9),'white','white',5,1)
 text(cx,y,title,size,color,True,True)
def route(points,color='#3668a8'):
 line(points,color)
 arrow(*points[-2],*points[-1],color)

BLUE='#3668a8';GREEN='#27806a';AMBER='#b57a2c'
text(65,35,'PC 부품 수집에서 가격 비교까지',47,'#172d49',True)
text(67,102,'사이트별 수집 → 공통 상품 정제 → DB 저장 → 웹 검색·비교',26,'#64778b')
rect((55,190,420,1340),'#f3f7fc','#c4d4e9',24)
rect((480,190,1360,1340),'#f3f9f6','#bed9cf',24)
rect((1420,190,2345,1340),'#fcf8f1','#e2d0b1',24)
text(90,220,'수집 대상',32,BLUE,True);text(520,220,'Python 수집 파이프라인',32,GREEN,True);text(1460,220,'DB · 웹 조회',32,AMBER,True)
card(235,490,'컴퓨존','app','목록·상세 HTML',BLUE,300)
card(235,1050,'다나와','app','동적 목록·판매처',BLUE,300)
card(735,490,'사이트별 크롤러','app','Requests · Selenium',GREEN,420)
card(1090,1020,'정규화 · 상품 구분','app','문자열·규격 규칙 (ML 아님)',GREEN,440)
card(1880,490,'PostgreSQL','db','상품·판매처·가격 이력',AMBER,510)
card(1880,920,'Flask 웹','server','검색·필터·가격·기본 호환성',AMBER,510)
arrow(385,490,525,490,BLUE);label(455,440,'① 수집',BLUE,22)
route([(385,1050),(445,1050),(445,610),(735,610),(735,602)],BLUE)
route([(735,602),(735,800),(1090,800),(1090,910)],GREEN);label(950,753,'② 파싱 → 규격별 식별키',GREEN,24)
route([(1310,1020),(1385,1020),(1385,490),(1625,490)],GREEN);label(1475,435,'③ 저장',GREEN,24)
arrow(1880,602,1880,810,AMBER,True);label(1880,725,'④ DB 조회',AMBER,25)
text(520,300,'CLI: 사이트·카테고리·수집 수 선택',25,GREEN)
# 실행 설정은 크롤러 카드의 위쪽으로 전달합니다.
# 두 카드의 경계를 겹치지 않도록 CLI를 별도 줄 대신 상단 설명으로 축약합니다.
card(1880,1230,'브라우저','monitor','목록·상세·가격 차트',AMBER,510)
arrow(1880,1032,1880,1118,AMBER)
text(525,1220,'CPU · GPU · RAM · SSD · 메인보드',27,GREEN,True)
text(525,1270,'수집 로그 / 개별 실패·건너뜀 기록',25,'#64778b')
text(67,1390,'호환성은 소켓·메모리 규격 기준의 기본 조회이며 전체 조립 호환성 보장이 아닙니다.',24,'#64778b')
text(67,1440,'실제 쇼핑몰 재수집·DB 접속은 이번 문서 작업에서 실행하지 않았습니다.',22,'#64778b')

svg.append('</svg>')
img.save(ROOT/'images/system-architecture.png')
(ROOT/'images/system-architecture.svg').write_text('\n'.join(svg),encoding='utf-8')
print('Created PNG + SVG')
