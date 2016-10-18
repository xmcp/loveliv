#coding=utf-8
from . import _utils

evt_scores=_utils.parse_trad_evt_table([
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
])

def parse_score(x):
    if x<=0:
        return
    elif x<5:
        return '非活动 Ez 损失 %d 图标'%(5-x)
    elif x==5:
        return '非活动 Ez'
    elif x<10:
        return '非活动 Nm 损失 %d 图标'%(10-x)
    elif x==10:
        return '非活动 Nm'
    elif x<16:
        return '非活动 Hd 损失 %d 图标'%(16-x)
    elif x==16:
        return '非活动 Hd'
    elif x<27:
        return '非活动 Ex 损失 %d 图标'%(27-x)
    elif x==27:
        return '非活动 Ex'
    elif x in evt_scores:
        return '活动曲 %s'%(' 或 '.join(evt_scores[x]))
