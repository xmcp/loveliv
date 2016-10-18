#coding=utf-8

def parse_trad_evt_table(table):
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
    ret={}
    modes=['Ez']+['Nm']*3+['Hd']*4+['Ex']*4
    scores='SSABSABCSABC'
    combos='SABC-'
    for r,row in enumerate(table):
        for c,col in enumerate(row):
            ret.setdefault(col,[]).append('%s Score%s Combo%s'%(modes[r],scores[r],combos[c]))
            ret.setdefault(col*4,[]).append('4x %s Score%s Combo%s'%(modes[r],scores[r],combos[c]))
    return ret
