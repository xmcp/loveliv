#coding=utf-8
import itchat
import itchat.out #monkey patching log out notification
import threading
import sqlite3
import time
from utils import log

CHAT_NAME='ll.xmcp.ml'
logged_errors=set()

# patch itchat.out.println, if `LOG OUT` is being outputted, log and exit
stopped=False
def _monkey_patched_println(msg, *args, **kwargs):
    if msg=='LOG OUT':
        stopped=True
        log('error','微信机器人会话已退出')
    return _original_println(msg, *args, **kwargs)

_original_println=itchat.out.print_line
itchat.out.print_line=_monkey_patched_println

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
    while not stopped:
        try:
            time.sleep(10)
            send_msgs()
        except Exception as e:
            print('!!! exception: [%s] %s'%(type(e),e))
    log('debug','微信机器人已停止工作')

@itchat.msg_register(itchat.content.TEXT,isGroupChat=True)
def status_indicate(msg):
    if msg['isAt']:
        return '[发呆]'

@itchat.msg_register(itchat.content.TEXT,isGroupChat=False)
def custom_push(msg):
    cmd,_,content=msg['Content'].partition(' ')
    if cmd.lower()=='send':
        return '成功' if itchat.send_msg(content,toUserName=group_name) else '失败'
        
itchat.auto_login(hotReload=True,enableCmdQR=2)

group_name=itchat.search_chatrooms(name=CHAT_NAME)[0]['UserName']
print('wx group username:',group_name)

threading.Thread(target=msg_mainloop).start()
itchat.run()