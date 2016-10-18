import requests
from requests.adapters import HTTPAdapter
import sqlite3
import datetime
import time
import os
from utils import log, init_db, init_master, parse_score_meta
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('-e',nargs='?',dest='EVENT_ID',help='Specify event id')
parser.add_argument('-b',nargs='*',dest='BUGGY_USERS',help='User INDs that will skip errors when fetching')
args=parser.parse_args()

s=requests.Session()
s.mount('http://',HTTPAdapter(max_retries=2))

TIMEOUT=15
INF=999999

def push(x):
    print(' -> add push:',x.replace('\n','\\n'))
    with sqlite3.connect('events.db') as db:
        db.execute(
            'insert into push_msgs (content) values (?)',
            ['%s %s'%(datetime.datetime.now().strftime('%m-%d %H:%M'),x)]
        )

def line_num(x):
    return -1 if x<=0 else 1 if x<=2300 else 2 if x<=11500 else 3 if x<=23000 else 4 if x!=INF else -1

def _fetch_user_rank(ind,uid,eventid):
    res=s.get(
        'http://sl.loveliv.es/ranking.php',
        params={
            'userId':uid,
            'event_id':eventid,
        },
        timeout=TIMEOUT,
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
        if last_user_score[ind] is not None:
            if ind not in BUGGY_USERS:
                log('error','%d 的分数获取失败，使用上次结果'%uid)
            return {
                'score': last_user_score[ind][1],
                'rank': last_user_score[ind][2],
                'level': last_user_score[ind][0],
            }
        else:
            if ind not in BUGGY_USERS:
                log('error','%d 的分数获取失败'%uid)
            return {
                'score': 0,
                'rank': INF,
                'level': -1,
            }

def _fetch_line():
    res = s.get('http://2300.ml/api/json', timeout=TIMEOUT)
    res.raise_for_status()
    j = res.json()

    if args.EVENT_ID is not None:
        evt_info=evt_info_bkp
    else:
        evt_info={
            'id': int(j['event_info']['event_id']),
            'title': j['event_info']['title'],
            'begin': datetime.datetime.strptime(j['event_info']['begin'],'%Y-%m-%d %H:%M:%S'),
            'end': datetime.datetime.strptime(j['event_info']['end'],'%Y-%m-%d %H:%M:%S'),
        }
    return evt_info, j['predictions']


if not os.path.exists('events.db'):
    print(' -> initializing master db...')
    init_master()
with sqlite3.connect('events.db') as _db:
    _cur=_db.execute('select ind,id,name from follows')
    follows=_cur.fetchall() # [(ind, user_id, name), ...]
    print(' -> got %d user(s) to follow'%len(follows))
    last_user_score={x[0]:None for x in follows} # {ind: (level, score, rank), ...}

def _fetchall():
    print(' == fetching line')
    evt_info,predict=_fetch_line()
    eventid=evt_info['id']
    score_parser=parse_score_meta(eventid)

    if not os.path.exists('db/%d.db'%eventid): # init db
        print(' -> new event: event #%d %s'%(eventid,evt_info['title']))
        print(' -> creating database and writing event info...')
        init_db(eventid)
        with sqlite3.connect('events.db') as db:
            db.execute(
                'insert or replace into events (id, title, begin, end, last_update, score_parser) '
                'values (?,?,?,?,null,(select score_parser from events where id=?))',
                [eventid,evt_info['title'],int(evt_info['begin'].timestamp()),int(evt_info['end'].timestamp()),eventid]
            )
    if datetime.datetime.now()-datetime.timedelta(hours=1)>evt_info['end']:
        log('debug','活动 #%d 结束，爬虫停止抓取'%eventid)
        raise SystemExit('活动结束')

    with sqlite3.connect('db/%d.db'%eventid) as db:
        db.execute('insert into line (time, t1pre, t1cur, t2pre, t2cur, t3pre, t3cur) values (?,?,?,?,?,?,?)', [
            int(datetime.datetime.now().timestamp()),
            predict['2300']['predict'], predict['2300']['current'],
            predict['11500']['predict'], predict['11500']['current'],
            predict['23000']['predict'], predict['23000']['current'],
        ])
        for ind,uid,name in follows:
            print(' == fetching score of #%d %s at place %d'%(uid,name,ind))
            details=_fetch_user_rank(ind,uid,eventid)

            if last_user_score[ind] is not None:
                last_lv, last_score, last_rank=last_user_score[ind]

                if details['level']!=last_lv:
                    log('info','关注者 %s 等级变更：lv %d → lv %d'%(name,last_lv,details['level']))
                    if last_user_score[ind][0]>0 and details['level']>0:
                        push('%s\n升级到了 lv. %d'%(name,details['level']))

                if details['score']!=last_score:
                    score_delta=details['score']-last_score
                    log('info','关注者 %s 分数变更：%d pt + %d pt → %d pt%s'%\
                        (name,last_score,score_delta,details['score'],score_parser(score_delta,' (%s)')))
                    if last_score and details['score']>0:
                        push('%s\n%s获得了 %d pt\n→ %d pt (#%d)'%\
                            (name,score_parser(score_delta,'%s\n'),score_delta,details['score'],details['rank']))

                if line_num(details['rank'])!=line_num(last_rank):
                    better_line=min(line_num(last_rank),line_num(details['rank']))
                    log('info','关注者 %s 档位变更：L%d → L%d (#%d)'%\
                        (name,line_num(last_rank),line_num(details['rank']),details['rank']))
                    if line_num(last_rank)>0 and line_num(details['rank'])>0:
                        push('%s\n%s了 %d 档\n当前排名：#%d'%\
                             (name,'离开' if better_line==line_num(last_rank) else '进入',better_line,details['rank']))

            last_user_score[ind]=(details['level'],details['score'],details['rank'])

            db.execute(
                'insert into follow%d (time,level,score,rank) values (?,?,?,?)'%ind,
                [int(datetime.datetime.now().timestamp()), details['level'], details['score'], details['rank']]
            )

    return eventid

def mainloop():
    print('=== servant started')
    curmin=datetime.datetime.now().minute
    log('success','LoveLiv Servant 已启动，关注者共有 %d 人'%len(follows))

    while True:
        print(' -> waiting for next update...')
        while curmin==datetime.datetime.now().minute:
            time.sleep(1)

        curmin=datetime.datetime.now().minute
        print('=== ticked at %s'%datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        tstart=time.time()
        eventid=None
        bug=None
        try:
            eventid=_fetchall()
        except Exception as e:
            bug='[%s] %s'%(type(e),e)
            print('!!!',bug)
        except SystemExit:
            bug='活动结束'
            return
        else:
            bug=None
            with sqlite3.connect('events.db') as db:
                db.execute(
                    'update events set last_update=? where id=?',
                    [int(datetime.datetime.now().timestamp()), eventid]
                )
            print(' == update completed')
        finally:
            if bug is not None:
                log('error','爬取出错，用时 %.1f 秒：%s'%(time.time()-tstart,bug))
            else:
                log('debug','活动 #%s 爬取成功，用时 %.1f 秒'%(eventid,time.time()-tstart))

if args.EVENT_ID:
    print(' -> EVENT_ID specified. fetching details...')
    eres=s.get('http://sifcn.loveliv.es/api/event_meta/%s' % args.EVENT_ID)
    eres.raise_for_status()
    ej=eres.json()
    evt_info_bkp={
        'id': int(ej['event_id']),
        'title': ej['title'],
        'begin': datetime.datetime.strptime(ej['begin']['time'], '%Y-%m-%d %H:%M:%S'),
        'end': datetime.datetime.strptime(ej['end']['time'], '%Y-%m-%d %H:%M:%S'),
    }
BUGGY_USERS=[int(x) for x in args.BUGGY_USERS or []]

mainloop()