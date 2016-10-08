#coding=utf-8
import sqlite3

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
        for i in (1,2,3,4):
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
            last_update integer
        );
        create table if not exists follows (
            ind integer unique,
            id integer,
            name text
        );''')
