#coding=utf-8
""" table structure:

Combo       S   A   B   C   -

Ez ScoreS   ?   ?   ?   ?   ?

Nm ScoreS   ?   ?   ?   ?   ?
Nm ScoreA   ?   ?   ?   ?   ?
Nm ScoreB   ?   ?   ?   ?   ?

Hd ScoreS   ?   ?   ?   ?   ?
Hd ScoreA   ?   ?   ?   ?   ?
Hd ScoreB   ?   ?   ?   ?   ?
Hd ScoreC   ?   ?   ?   ?   ?

Ex ScoreS   ?   ?   ?   ?   ?
Ex ScoreA   ?   ?   ?   ?   ?
Ex ScoreB   ?   ?   ?   ?   ?
Ex ScoreC   ?   ?   ?   ?   ?
"""

table=[
    [71,70,69,67,66],
    [148,145,143,140,137],
    [143,140,137,135,133],
    [137,135,132,129,125],
    [261,254,246,241,237],
    [249,242,235,230,226],
    [237,231,224,220,215],
    [226,219,213,209,204],
    [565,549,518,508,498],
    [540,525,498,485,475],
    [509,495,467,458,448],
    [484,470,444,435,426],
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
scores='SSABSABCSABC'
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