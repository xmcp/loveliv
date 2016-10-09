#coding=utf-8
from flask import *
import os
import sqlite3
import datetime

app=Flask(__name__)

@app.template_filter('parsetime')
def parse_timestamp(x):
    return datetime.datetime.fromtimestamp(x).isoformat()

@app.template_filter('strftime')
def parse_timestamp(x):
    return datetime.datetime.fromtimestamp(x).strftime('%m-%d %H:%M:%S')


@app.route('/')
def index():
    with sqlite3.connect('events.db') as db:
        cur=db.execute('select id,title,begin,end,last_update from events')
        g.events=cur.fetchall()
    return render_template('index.html')


@app.route('/<eventid>/')
def event_index(eventid):
    return str(eventid)


app.debug=True
app.run(port=int(os.environ.get('LOVELIV_PORT',80)))