#coding=utf-8
from flask import *
import os
import sqlite3
import datetime

app=Flask(__name__)
app.debug=True
app.jinja_options['extensions'].append('jinja2.ext.do')

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

@app.url_value_preprocessor
def preproc_follower_ind(_,values):
    if values is not None and 'ind' in values:
        g.follower_ind=values['ind']

@app.template_global('get_follower_info')
def get_follower_info():
    with sqlite3.connect('events.db') as db_master:
        cur=db_master.cursor()
        cur.execute('select id,name from follows where ind=?',[g.follower_ind])
        res=cur.fetchone()
        assert res, '没有找到该关注者'
        g.fid, g.fname=res

@app.template_filter('parsetime')
def parse_timestamp_iso(x):
    return to_datetime(x).isoformat()

@app.template_filter('strftime')
def parse_timestamp_str(x):
    return to_datetime(x).strftime('%m-%d %H:%M')

## controller

@app.route('/')
def index():
    with sqlite3.connect('events.db') as db:
        cur=db.execute('select id,title,begin,end,last_update from events')
        g.events=cur.fetchall()
    return render_template('index.html')

@app.route('/<int:eventid>')
@app.route('/<int:eventid>/')
def _event_index(eventid):
    return redirect(url_for('event_index',eventid=eventid))

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
                'desc': '拟合 / 实际 %d / 预测 %d'%(cur,pre),
            })

    return render_template('event_index.html',scores=scores)

@app.route('/<int:eventid>/predict')
def event_predict(eventid):
    getevent(eventid)
    return render_template('event_predict.html')

@app.route('/<int:eventid>/follow<int:ind>')
@app.route('/<int:eventid>/follow<int:ind>/')
def event_follow(eventid,ind):
    return redirect(url_for('follower_details',eventid=eventid,ind=ind))

@app.route('/<int:eventid>/follow<int:ind>/details')
def follower_details(eventid,ind):
    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time,level,score,rank from follow%d order by time desc limit 0,1'%ind)
        res=cur.fetchone()
        assert res, '没有该玩家的记录'
        g.ftime, g.flevel, g.fscore, g.frank=res

        # todo: user level support
        cur.execute('select min(time), score, min(rank), max(rank) from follow%d group by score'%ind)
        res=cur.fetchall()

    return render_template('follow_details.html', scores=res)

@app.route('/<int:eventid>/follow<int:ind>/score')
def follower_scores(eventid,ind):
    getevent(eventid)
    return render_template('follow_score.html')

## api

# noinspection PyUnresolvedReferences
@app.route('/<int:eventid>/api_predict.json')
def api_predict(eventid):
    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time,t1pre,t1cur,t2pre,t2cur,t3pre,t3cur from line')
        lines=cur.fetchall()
    times=[parse_timestamp_str(x[0]).replace(' ','\n') for x in lines]
    return jsonify(
        times=times,
        l1c=[x[2] for x in lines],
        l2c=[x[4] for x in lines],
        l3c=[x[6] for x in lines],
        l1p=[x[1] for x in lines],
        l2p=[x[3] for x in lines],
        l3p=[x[5] for x in lines],
        l1r=[x[1]*(x[0]-g.begin)/(g.end-g.begin) for x in lines],
        l2r=[x[3]*(x[0]-g.begin)/(g.end-g.begin) for x in lines],
        l3r=[x[5]*(x[0]-g.begin)/(g.end-g.begin) for x in lines],
    )

@app.route('/<int:eventid>/follow<int:ind>/api_score.json')
def api_follower_score(eventid,ind):
    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time,score from follow1')
        scores=cur.fetchall()
    times=[parse_timestamp_str(x[0]).replace(' ','\n') for x in scores]
    return jsonify(
        times=times,
        real=[x[1] for x in scores],
        predict=[x[1]/(x[0]-g.begin)*(g.end-g.begin) for x in scores],
    )

app.run(host='0.0.0.0',port=int(os.environ.get('LOVELIV_PORT',80)))