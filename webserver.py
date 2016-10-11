#coding=utf-8
from flask import *
import os
import sqlite3
import datetime

app=Flask(__name__)
app.debug=True

## internal function

to_datetime=datetime.datetime.fromtimestamp # this name is so fucking long

def getevent(eventid):
    assert os.path.isfile('db/%d.db'%eventid), '分数数据库不存在'
    with sqlite3.connect('events.db') as db:
        cur=db.cursor()
        cur.execute('select title,begin,`end`,last_update from events where id=?',[eventid])
        res=cur.fetchone()
        assert res, '活动信息不存在'

        cur.execute('select ind,name from follows')
        g.eventid=eventid
        g.follows=cur.fetchall()

    g.title=res[0]
    g.begin=res[1]
    g.end=res[2]
    g.real_time=res[3]
    g.time=g.real_time if g.real_time<g.end else g.end

    return sqlite3.connect('db/%d.db'%eventid)

## template helper

@app.template_filter('parsetime')
def parse_timestamp(x):
    return to_datetime(x).isoformat()

@app.template_filter('strftime')
def parse_timestamp(x):
    return to_datetime(x).strftime('%m-%d %H:%M')

## controller

@app.route('/')
def index():
    with sqlite3.connect('events.db') as db:
        cur=db.execute('select id,title,begin,end,last_update from events')
        g.events=cur.fetchall()
    return render_template('index.html')


@app.route('/<int:eventid>/index')
def event_index(eventid):
    db=getevent(eventid)
    scores=[]

    with db:
        cur=db.cursor()
        for ind,name in g.follows:
            cur.execute('select score,rank from follow%d order by time desc limit 0,1'%ind)
            res=cur.fetchone() or [-1,999999]
            scores.append({
                'score': res[0],
                'name': name,
                'desc': '#%d'%res[1],
            })
        cur.execute('select t1cur,t1pre,t2cur,t2pre,t3cur,t3pre from line order by time desc limit 0,1')
        t1cur, t1pre, t2cur, t2pre, t3cur, t3pre=cur.fetchone() or [-1,-1,-1,-1,-1,-1]
        for name,cur,pre in [(1,t1cur,t1pre),(2,t2cur,t2pre),(3,t3cur,t3pre)]:
            scores.append({
                'score': int(pre*(g.time-g.begin)/(g.end-g.begin)),
                'name': '%d 档'%name,
                'desc': '实际 %d / 预测 %d'%(cur,pre),
            })

    return render_template('event_index.html',scores=scores)

@app.route('/<int:eventid>/predict')
def event_predict(eventid):
    getevent(eventid)
    return render_template('event_predict.html')

@app.route('/<int:eventid>/api_predict.json')
def api_predict(eventid):
    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time,t1pre,t1cur,t2pre,t2cur,t3pre,t3cur from line')
        lines=cur.fetchall()
    times=[x[0] for x in lines]
    l1=[x[6] for x in lines] # fixme
    return jsonify(
        times=times,
        l1=l1,
    )

app.run(port=int(os.environ.get('LOVELIV_PORT',80)))