#coding=utf-8
from flask import *
from flask_compress import Compress
import os
import sqlite3
import datetime
from utils import parse_score_meta

app=Flask(__name__)
app.config['COMPRESS_LEVEL']=9
Compress(app)
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

@app.before_request
def graph_delta_setter():
    g.graph_delta=int(request.cookies.get('graph_delta', 10 if 'Mobile' in request.user_agent.string else 3))
    assert g.graph_delta in [1,3,10], '计数点无效'

@app.url_value_preprocessor
def preproc_follower_ind(_,values):
    if values is not None and 'ind' in values:
        g.follower_ind=values['ind']

## template helper

@app.template_global('get_score_parser')
def template_get_score_parser(evt):
    return parse_score_meta(evt)

@app.template_global('get_follower_info')
def template_get_follower_info():
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
        cur=db.cursor()
        cur.execute('select id from events order by id desc limit 0,1')
        res=cur.fetchone()
        if res:
            return redirect(url_for('event_index',eventid=res[0]))
        else:
            return redirect(url_for('event_list'))

@app.route('/config/delta/<int:delta>')
def set_graph(delta):
    assert delta in [1,3,10], '计数点无效'
    resp=make_response(redirect(request.referrer or '/'))
    resp.set_cookie('graph_delta',str(delta))
    return resp
            
@app.route('/list')
def event_list():
    with sqlite3.connect('events.db') as db:
        cur=db.cursor()
        cur.execute('select id,title,begin,end,last_update from events')
        g.events=cur.fetchall()
        cur.execute('select time,channel,content from logs order by time desc limit 0,8')
        logs=cur.fetchall()

    return render_template('index.html',logs=logs)

@app.route('/logs')
def raw_logs():
    with sqlite3.connect('events.db') as db:
        cur=db.cursor()
        cur.execute('select time,channel,content from logs order by time desc')
        logs = cur.fetchall()
    return render_template('logs_view.html',logs=logs)

@app.route('/<int:eventid>')
@app.route('/<int:eventid>/')
def _event_index(eventid):
    return redirect(url_for('event_index',eventid=eventid))

@app.route('/<int:eventid>/index')
def event_index(eventid):
    db=getevent(eventid)
    scores=[]
    last_action=[]

    with db:
        cur=db.cursor()
        for ind,name in g.follows:
            cur.execute('select score,rank from follow%d order by time desc limit 0,1'%ind)
            res=cur.fetchone() or [-1,999999]
            scores.append({
                'score': res[0],
                'name': name,
                'special': False,
                'desc': '#%d / 预测 %d pt'%(res[1],res[0]/(g.time-g.begin)*(g.end-g.begin)),
            })
            cur.execute('select score,min(time) from follow%d group by score order by score desc limit 0,2'%ind)
            res=cur.fetchmany(2)
            if len(res)==2:
                last,second=res
                last_action.append({
                    'name': name,
                    'time': last[1],
                    'score': last[0]-second[0],
                })
            else: #not enough data
                last_action.append({
                    'name': name,
                    'time': None,
                    'score': None,
                })

        cur.execute('select t1cur,t1pre,t2cur,t2pre,t3cur,t3pre from line order by time desc limit 0,1')
        t1cur, t1pre, t2cur, t2pre, t3cur, t3pre=cur.fetchone() or [-1,-1,-1,-1,-1,-1]
        for name,cur,pre in [(1,t1cur,t1pre),(2,t2cur,t2pre),(3,t3cur,t3pre)]:
            scores.append({
                'score': cur,
                'name': '%d 档'%name,
                'special': True,
                'desc': '实际 / 预测 %d pt / 拟合 %d pt'%(pre,int(pre*(g.time-g.begin)/(g.end-g.begin))),
            })

    return render_template('event_index.html',scores=scores,last_action=last_action)

@app.route('/<int:eventid>/predict')
def event_predict(eventid):
    getevent(eventid)
    return render_template('event_predict.html')

@app.route('/<int:eventid>/follow<int:ind>')
@app.route('/<int:eventid>/follow<int:ind>/')
def event_follow(eventid,ind):
    return redirect(url_for('follower_details',eventid=eventid,ind=ind))

@app.route('/<int:eventid>/follow<int:ind>/stats')
def follower_stats(eventid,ind):
    getevent(eventid)
    return render_template('follow_stats.html')

@app.route('/<int:eventid>/follow<int:ind>/details')
def follower_details(eventid,ind):
    db=getevent(eventid)
    scores=[]
    with db:
        cur=db.cursor()
        cur.execute('select time,level,score,rank from follow%d order by time desc limit 0,1'%ind)
        res=cur.fetchone()
        assert res, '没有该玩家的记录'
        g.ftime, g.flevel, g.fscore, g.frank=res

        cur.execute('select min(time), score, min(rank), max(rank) from follow%d group by score'%ind)
        for score in cur.fetchall():
            scores.append({
                'type': 'score',
                'value': score,
                'time': score[0],
            })
        cur.execute('select min(time), level from follow%d group by level'%ind)
        for level in cur.fetchall()[1:]:
            scores.append({
                'type': 'level',
                'value': level,
                'time': level[0]+1, #thus lv-update msg will displays after the song msg
            })

    return render_template('follow_details.html', scores=scores)

@app.route('/<int:eventid>/follow<int:ind>/score')
def follower_scores(eventid,ind):
    getevent(eventid)
    return render_template('follow_score.html')

@app.route('/<int:eventid>/follow<int:ind>/rank')
def follower_rank(eventid,ind):
    getevent(eventid)
    return render_template('follow_rank.html')

## api

# noinspection PyUnresolvedReferences
@app.route('/<int:eventid>/api_predict.json')
def api_predict(eventid):
    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time,t1pre,t1cur,t2pre,t2cur,t3pre,t3cur from line')
        lines=cur.fetchall()[::g.graph_delta]
    return jsonify(
        times=[parse_timestamp_str(x[0]).replace(' ','\n') for x in lines],
        l1c=[int(x[2]) for x in lines],
        l2c=[int(x[4]) for x in lines],
        l3c=[int(x[6]) for x in lines],
        l1p=[int(x[1]) for x in lines],
        l2p=[int(x[3]) for x in lines],
        l3p=[int(x[5]) for x in lines],
        l1r=[int(x[1]*(x[0]-g.begin)/(g.end-g.begin)) for x in lines],
        l2r=[int(x[3]*(x[0]-g.begin)/(g.end-g.begin)) for x in lines],
        l3r=[int(x[5]*(x[0]-g.begin)/(g.end-g.begin)) for x in lines],
    )

@app.route('/<int:eventid>/follow<int:ind>/api_stats.json')
def api_follower_stats(eventid,ind):
    db=getevent(eventid)
    times={}
    scores={}
    with db:
        cur=db.cursor()
        cur.execute('select min(time),score from follow%d group by score'%ind)
        res=cur.fetchall()
        for ind in range(len(res)):
            hour=to_datetime(res[ind][0]).hour
            score=res[ind][1]-res[ind-1][1] if ind>0 else None
            times.setdefault(hour,0)
            times[hour]+=1
            if score is not None:
                scores.setdefault(score,0)
                scores[score]+=1

    return jsonify(
        times=list(times.items()),
        scores=list(scores.items()),
    )

@app.route('/<int:eventid>/follow<int:ind>/api_score.json')
def api_follower_score(eventid,ind):
    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time,score from follow%d'%ind)
        scores=cur.fetchall()[::g.graph_delta]
    return jsonify(
        times=[parse_timestamp_str(x[0]).replace(' ','\n') for x in scores],
        real=[int(x[1]) for x in scores],
        predict=[int(x[1]/(x[0]-g.begin)*(g.end-g.begin)) for x in scores],
    )

@app.route('/<int:eventid>/follow<int:ind>/api_rank.json')
def api_follower_rank(eventid,ind):
    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time,rank from follow%d'%ind)
        ranks=cur.fetchall()
    return jsonify(
        times=[parse_timestamp_str(x[0]).replace(' ','\n') for x in ranks],
        rank=[int(x[1]) for x in ranks],
    )

app.run(host='0.0.0.0',port=int(os.environ.get('LOVELIV_PORT',80)))