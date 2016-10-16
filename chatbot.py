#coding=utf-8
import itchat
import threading
import sqlite3
import time
from utils import log

logged_errors=set()

def send_msgs():
    with sqlite3.connect('events.db') as db:
        cur=db.cursor()
        cur.execute('select msgid,content from push_msgs')
        res=cur.fetchall()
        for msgid,content in res:
            if itchat.send_msg(content,toUserName=group_name):
                cur=db.cursor()
                cur.execute('delete from push_msgs where msgid=?',[msgid])
                db.commit()
                print(' -> sent msg:',content)
            else:
                if msgid not in logged_errors:
                    print('!!! send failed:',content)
                    log('error','微信消息发送失败（#%d）：%s'%(msgid,content))
                    logged_errors.add(msgid)
            time.sleep(.5)

def msg_mainloop():
    log('success','微信机器人已启动')
    while True:
        try:
            time.sleep(10)
            send_msgs()
        except Exception as e:
            print('!!! exception: [%s] %s'%(type(e),e))

@itchat.msg_register(itchat.content.TEXT,isGroupChat=True)
def status_indicate(msg):
    if msg['isAt']:
        return '[发呆]'

itchat.auto_login(hotReload=True)

group_name=itchat.search_chatrooms(name='ll.xmcp.ml')[0]['UserName']
print('wx group username:',group_name)

threading.Thread(target=msg_mainloop).start()
itchat.run()