#coding=utf-8
import sqlite3
import datetime
import functools
import score_parser

def log(ch,x):
    print(' -> log to',ch,'channel :', x)
    with sqlite3.connect('events.db') as db:
        db.execute(
            'insert into logs (time, channel, content) values (?,?,?)',
            [int(datetime.datetime.now().timestamp()),ch,x]
        )

def init_db(eventid):
    with sqlite3.connect('db/%d.db'%eventid) as db:
        db.execute(r'''
        create table if not exists line (
          time integer,
          t1pre integer,
          t1cur integer,
          t2pre integer,
          t2cur integer,
          t3pre integer,
          t3cur integer
        )''')
        for i in (1,2,3,4,5):
            db.execute('''
            create table if not exists follow%d (
              time integer,
              level integer,
              score integer,
              rank integer
            )'''%i)

def init_master():
    with sqlite3.connect('events.db') as db:
        db.executescript(r'''
        create table if not exists events (
            id integer unique,
            title text,
            begin integer,
            end integer,
            last_update integer,
            score_parser text
        );
        create table if not exists follows (
            ind integer unique,
            id integer,
            name text
        );
        create table if not exists logs (
            id integer primary key,
            time integer,
            channel text,
            content text
        );
        create table if not exists push_msgs (
            msgid integer primary key,
            content text
        )''')

@functools.lru_cache()
def parse_score_meta(eventid):
    with sqlite3.connect('events.db') as db:
        cur=db.cursor()
        cur.execute('select score_parser from events where id=?',[eventid])
        res=cur.fetchone()
    if res and res[0]:
        def wrapper(x,format_str='%s'):
            orig_res=score_parser.parsers[res[0]](x)
            if orig_res:
                return format_str%orig_res
            else:
                return ''
        return wrapper
    else:
        return lambda x,y=None:''