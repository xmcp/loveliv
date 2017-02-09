#coding=utf-8

table=[
# No. 1   2   3   4
    [63, 58, 53, 50], # S Easy
    [60, 56, 51, 48], # A
    [58, 53, 49, 46], # B
    [55, 51, 46, 44], # C

    [150, 138, 126, 120], # Normal
    [144, 132, 121, 115],
    [138, 127, 116, 110],
    [131, 121, 110, 105],

    [266, 244, 223, 211], # Hard
    [254, 234, 214, 204],
    [243, 224, 204, 195],
    [232, 214, 195, 186],

    [536, 493, 450, 428], #Expert
    [513, 472, 431, 411],
    [491, 452, 412, 393],
    [469, 431, 394, 375],
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
    if x==14:
        return 'Ez 失败'
    elif x==34:
        return 'Nm 失败'
    elif x==59:
        return 'Hd 失败'
    elif x==119:
        return 'EX 失败'
    elif x in evt_scores:
        return ' / '.join(evt_scores[x])

def parse_tuple(x):
    return evt_tuples.get(x,(x,0,0,0))