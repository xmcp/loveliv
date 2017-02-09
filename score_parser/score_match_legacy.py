#coding=utf-8

table=[
# No. 1   2   3   4
    [54, 50, 45, 43], # S Easy
    [52, 48, 43, 41], # A
    [50, 46, 42, 40], # B
    [47, 43, 40, 38], # C

    [134, 123, 112, 107], # Normal
    [128, 118, 107, 102],
    [122, 113, 103, 98],
    [117, 107, 98, 93],

    [245, 225, 205, 196], # Hard
    [234, 216, 197, 187],
    [224, 206, 188, 179],
    [214, 197, 180, 171],

    [408, 375, 343, 326], #Expert
    [391, 360, 328, 313],
    [374, 344, 314, 299],
    [357, 328, 300, 286],
]

lps={
    'Ez': 5,
    'Nm': 10,
    'Hd': 15,
    'EX': 25,
}

evt_scores={}
evt_tuples={}
modes=['Ez']*4+['Nm']*4+['Hd']*4+['EX']*4
scores='SABC'*4
nums='1234'
for r, row in enumerate(table):
    for c, col in enumerate(row):
        evt_scores.setdefault(col,[]).append('%s %s #%s' % (modes[r],scores[r],nums[c]))
        evt_tuples[col]=(col,1,lps[modes[r]],0)

def parse_score(x):
    if x==12:
        return 'Ez 失败'
    elif x==30:
        return 'Nm 失败'
    elif x==55:
        return 'Hd 失败'
    elif x==91:
        return 'EX 失败'
    elif x in evt_scores:
        return ' / '.join(evt_scores[x])
        
def parse_tuple(x):
    return evt_tuples.get(x,(x,0,0,0))