#coding=utf-8
""" table structure:

Combo       S   A   B   C   -

Ez ScoreS   ?   ?   ?   ?   ?

Nm ScoreB   ?   ?   ?   ?   ?
Nm ScoreA   ?   ?   ?   ?   ?
Nm ScoreS   ?   ?   ?   ?   ?

Hd ScoreC   ?   ?   ?   ?   ?
Hd ScoreB   ?   ?   ?   ?   ?
Hd ScoreA   ?   ?   ?   ?   ?
Hd ScoreS   ?   ?   ?   ?   ?

Ex ScoreC   ?   ?   ?   ?   ?
Ex ScoreB   ?   ?   ?   ?   ?
Ex ScoreA   ?   ?   ?   ?   ?
Ex ScoreS   ?   ?   ?   ?   ?
"""

table=[
    [65, 64, 62, 61, 60],
    [130, 128, 125, 123, 120],
    [135, 133, 130, 127, 125],
    [140, 138, 135, 132, 130],
    [201, 196, 190, 186, 182],
    [212, 206, 200, 196, 192],
    [223, 216, 210, 206, 202],
    [233, 227, 220, 216, 211],
    [346, 336, 317, 311, 305],
    [364, 354, 334, 327, 321],
    [386, 375, 354, 347, 340],
    [404, 393, 371, 363, 356],
]

items={
    'Ez': 15,
    'Nm': 30,
    'Hd': 45,
    'EX': 75,
}

evt_scores={}
evt_tuples={}
modes=['Ez']+['Nm']*3+['Hd']*4+['EX']*4
scores='SBASCBASCBAS'
combos='SABC-'
for r, row in enumerate(table):
    for c, col in enumerate(row):
        evt_scores.setdefault(col,[]).append('%s %s:%s'%(modes[r],scores[r],combos[c]))
        evt_scores.setdefault(col*4,[]).append('4x %s %s:%s'%(modes[r],scores[r],combos[c]))
        evt_tuples[col]=(col,1,0,-items[modes[r]])
        evt_tuples[col*4]=(col*4,4,0,-4*items[modes[r]])

def parse_score(x):
    if x<=0: return
    elif x<5: return '非活动 Ez -%d'%(5-x)
    elif x==5: return '非活动 Ez'
    elif x<10: return '非活动 Nm -%d'%(10-x)
    elif x==10: return '非活动 Nm'
    elif x<16: return '非活动 Hd -%d'%(16-x)
    elif x==16: return '非活动 Hd'
    elif x<27: return '非活动 EX -%d'%(27-x)
    elif x==27: return '非活动 EX'
    elif x in evt_scores:
        return ' / '.join(evt_scores[x])
        
def parse_tuple(x):
    if x<=0: return (x,0,0,0)
    elif x<=5: return (x,1,5,x)
    elif x<=10: return (x,1,10,x)
    elif x<=16: return (x,1,15,x)
    elif x<=27: return (x,1,25,x)
    else: return evt_tuples.get(x,(x,0,0,0))