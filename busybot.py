import requests
import sqlite3
import datetime
import time
import os

from dbutils import init_db, init_master
s=requests.Session()

def _fetch_user_rank(uid,eventid):
    res=s.get(
        'http://sl.loveliv.es/ranking.php',
        params={
            'userId':uid,
            'event_id':eventid,
        }
    )
    res.raise_for_status()
    for user in res.json()['data']:
        if user['user_data']['user_id']==uid:
            return {
                'score': user['score'],
                'rank': user['rank'],
                'level': user['user_data']['level'],
            }
    else:
        raise RuntimeError(res.json())

def _fetch_line():
    res=s.get('http://2300.ml/api/json')
    res.raise_for_status()
    j=res.json()
    return ({
        'id': int(j['event_info']['event_id']),
        'title': j['event_info']['title'],
        'begin': datetime.datetime.strptime(j['event_info']['begin'],'%Y-%m-%d %H:%M:%S'),
        'end': datetime.datetime.strptime(j['event_info']['end'],'%Y-%m-%d %H:%M:%S'),
    }, j['predictions']) # -> {
        #   '2300': {
        #     'current': int(),
        #     'predict': int(),
        #   }, ...
        # }

#print(_fetch_user_rank(4420401,56))

if not os.path.exists('events.db'):
    print(' -> initializing master db...')
    init_master()
with sqlite3.connect('events.db') as _db:
    _cur=_db.execute('select ind,id,name from follows')
    follows=_cur.fetchall() # [(ind, user_id, name), ...]
    print(' -> got %d user(s) to follow'%len(follows))

def _fetchall():
    print(' == fetching line')
    evt_info,predict=_fetch_line()
    eventid=evt_info['id']
    if not os.path.exists('db/%d.db'%eventid):
        print(' -> new event: event #%d %s'%(eventid,evt_info['title']))
        print(' -> creating database and writing event info...')
        init_db(eventid)
        with sqlite3.connect('events.db') as db:
            db.execute(
                'replace into events (id, title, begin, end) values (?,?,?,?)',
                [eventid, evt_info['title'], int(evt_info['begin'].timestamp()), int(evt_info['end'].timestamp())]
            )

    with sqlite3.connect('db/%d.db'%eventid) as db:
        print(' -> writing line data...')
        db.execute('insert into line (time, t1pre, t1cur, t2pre, t2cur, t3pre, t3cur) values (?,?,?,?,?,?,?)', [
            int(datetime.datetime.now().timestamp()),
            predict['2300']['predict'], predict['2300']['current'],
            predict['11500']['predict'], predict['11500']['current'],
            predict['23000']['predict'], predict['23000']['current'],
        ])
        for ind,uid,name in follows:
            print(' == fetching score of #%d %s at place %d'%(uid,name,ind))
            details=_fetch_user_rank(uid,eventid)
            print(' -> writing score data...')
            db.execute(
                'insert into follow%d (time,level,score,rank) values (?,?,?,?)'%ind,
                [int(datetime.datetime.now().timestamp()), details['level'], details['score'], details['rank']]
            )

def mainloop():
    print('=== busybot started')
    curmin=datetime.datetime.now().minute

    while True:
        print(' -> waiting for next update...')
        while curmin==datetime.datetime.now().minute:
            time.sleep(1)

        curmin=datetime.datetime.now().minute
        print('=== ticked at %s'%datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        try:
            _fetchall()
        except Exception as e:
            print('!!! %s %s'%(type(e),e))
        else:
            print('=== update completed')

mainloop()