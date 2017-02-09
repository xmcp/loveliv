#coding=utf-8
from flask import *
from flask_compress import Compress
import os
import sqlite3
import datetime
from utils import parse_score_meta, stat_score_meta

app=Flask(__name__)
app.config['COMPRESS_LEVEL']=9
Compress(app)
app.debug=True
app.jinja_options['extensions'].append('jinja2.ext.do')

## internal function

to_datetime=datetime.datetime.fromtimestamp # this name is so fucking long

def getevent(eventid):
    def does_follower_exist(row):
        cur=evtdb.cursor()
        try:
            cur.execute('select count(*)>0 from follow%d'%row[0])
        except sqlite3.OperationalError:
            return False
        else:
            return cur.fetchone()[0]

    with sqlite3.connect('events.db') as mstdb, sqlite3.connect('db/%d.db'%eventid) as evtdb:
        cur=mstdb.cursor()
        cur.execute('select title,begin,`end`,last_update,score_parser from events where id=?',[eventid])
        res=cur.fetchone()
        assert res, '活动信息不存在'

        cur.execute('select ind,name from follows')
        g.eventid=eventid
        g.follows=list(filter(does_follower_exist,cur.fetchall()))

    g.title=res[0]
    g.begin=res[1]
    g.end=res[2]
    g.real_time=res[3]
    g.time=g.real_time if g.real_time<g.end else g.end
    g.score_parser=parse_score_meta(eventid)

    return sqlite3.connect('db/%d.db'%eventid)

@app.before_request
def graph_delta_setter():
    g.graph_delta=int(request.cookies.get('graph_delta', 15 if 'Mobile' in request.user_agent.string else 3))
    assert g.graph_delta in [1,3,15], '计数点无效'

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
        cur.execute('select id from events order by end desc limit 0,1')
        res=cur.fetchone()
        if res:
            return redirect(url_for('event_index',eventid=res[0]))
        else:
            return redirect(url_for('event_list'))

@app.route('/config/delta/<int:delta>')
def set_graph(delta):
    assert delta in [1,3,15], '计数点无效'
    resp=make_response(redirect(request.referrer or '/'))
    resp.set_cookie('graph_delta',str(delta))
    return resp
            
@app.route('/list')
def event_list():
    with sqlite3.connect('events.db') as db:
        cur=db.cursor()
        cur.execute('select id,title,begin,end,last_update,score_parser from events order by end desc')
        g.events=cur.fetchall()
        cur.execute('select time,channel,content from logs order by time desc limit 0,8')
        logs=cur.fetchall()

    return render_template('index.html',logs=logs,curtime=datetime.datetime.now().timestamp())

@app.route('/logs')
def raw_logs():
    with sqlite3.connect('events.db') as db:
        cur=db.cursor()
        cur.execute('select time,channel,content from logs order by time desc')
        logs = cur.fetchall()
    return render_template('logs_view.html',logs=logs)

@app.route('/badge')
def event_badge():
    with sqlite3.connect('events.db') as db:
        cur=db.cursor()
        cur.execute('select id,end from events order by end desc limit 0,1')
        res=cur.fetchone()
        if res:
            eventid,eventend=res
        else:
            return 'No event.'
        cur.execute("select time,content from logs where channel='error' order by time desc limit 0,3")
        err_logs=cur.fetchall()

    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time, t1pre, t1cur, t2pre, t2cur, t3pre, t3cur from line order by time desc limit 0,1')
        linetime,t1p,t1c,t2p,t2c,t3p,t3c=cur.fetchone()
        follows={}
        for ind,name in g.follows:
            cur.execute('select time,score,rank from follow%d order by time desc limit 0,1'%ind)
            follows[ind]=[name]
            follows[ind].extend(cur.fetchone())

    return render_template(
        'badge.html',
        timeleft=to_datetime(eventend)-datetime.datetime.now(),
        line=dict(time=linetime,t1p=t1p,t1c=t1c,t2p=t2p,t2c=t2c,t3p=t3p,t3c=t3c),
        follows={k:dict(name=v[0],time=v[1],score=v[2],rank=v[3]) for k,v in follows.items()},
        err_logs=err_logs,
    )

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
            res=cur.fetchone()
            if not res:
                continue
            scores.append({
                'score': res[0],
                'name': name,
                'special': False,
                'desc': '#%s / 预测 %d pt'%('INF' if res[1]==999999 else res[1],res[0]/(g.time-g.begin)*(g.end-g.begin)),
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
        for name,cur,pre in [(2300,t1cur,t1pre),(11500,t2cur,t2pre),(23000,t3cur,t3pre)]:
            if cur or pre:
                scores.append({
                    'score': cur,
                    'name': '#%d'%name,
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
        cur.execute('select time,t1pre,t1cur,t2pre,t2cur,t3pre,t3cur from line order by time asc')
        lines=cur.fetchall()[::g.graph_delta]
    return jsonify(
        times=[parse_timestamp_str(x[0]).replace(' ','\n') for x in lines],
        l1c=[int(x[2]) for x in lines],
        l2c=[int(x[4]) for x in lines],
        l3c=[int(x[6]) for x in lines],
        l1p=[int(x[1]) for x in lines],
        l2p=[int(x[3]) for x in lines],
        l3p=[int(x[5]) for x in lines],
    )

@app.route('/<int:eventid>/follow<int:ind>/api_stats.json')
def api_follower_stats(eventid,ind):
    def kuro_shift(d: datetime.datetime):
        if d.hour<3:
            return (d-datetime.timedelta(days=1)).date(), d.hour+24-3
        else:
            return d.date(),d.hour-3
            
    db=getevent(eventid)
    statgazer=stat_score_meta(eventid)
    times={}
    scores={}
    with db:
        cur=db.cursor()
        cur.execute('select min(time),score from follow%d group by score'%ind)
        res=cur.fetchall()
        for ind in range(len(res)):
            tim=to_datetime(res[ind][0])
            score=res[ind][1]-res[ind-1][1] if ind>0 else None
            key=kuro_shift(tim)
            times.setdefault(key,(0,0,0,0))
            if score is not None:
                scores.setdefault(score,0)
                scores[score]+=1                
                score_tuple=statgazer(score)
                times[key]=tuple(times[key][i]+score_tuple[i] for i in range(4))

    ks=list(sorted(scores.keys()))
    return jsonify(
        times=[[(h,d.strftime('%d'),v[i]) for (d,h),v in times.items()] for i in range(4)],
        maxes=[max((x[i] for x in times.values())) for i in range(4)],
        mines=[min((x[i] for x in times.values())) for i in range(4)],
        days=[d.strftime('%d') for d in sorted(set([d for d,_ in times.keys()]),reverse=True)],
        scores_keys=ks,
        scores_values=[scores[k] for k in ks],
    )

@app.route('/<int:eventid>/follow<int:ind>/api_score.json')
def api_follower_score(eventid,ind):
    db=getevent(eventid)
    with db:
        cur=db.cursor()
        cur.execute('select time,score from follow%d order by time asc'%ind)
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
        cur.execute('select time,rank from follow%d order by time asc'%ind)
        ranks=cur.fetchall()
    return jsonify(
        times=[parse_timestamp_str(x[0]).replace(' ','\n') for x in ranks],
        rank=[min(100000,int(x[1])) for x in ranks],
    )

app.run(host='0.0.0.0',port=int(os.environ.get('LOVELIV_PORT',80)))
