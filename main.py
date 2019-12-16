# -*- coding: UTF-8 -*-

import requests
import sys
import time
import hashlib
import json
import os
import traceback

import codecs


def timestamp():
    return str(int(time.time()*1000))


class YouDaoNoteSession(requests.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }

    def login(self, username, password):
        self.get('https://note.youdao.com/signIn/index.html')
        self.headers['Referer'] = 'https://note.youdao.com/signIn/index.html'

        self.get('https://note.youdao.com/auth/cq.json?app=web&_='+timestamp())
        self.get('https://note.youdao.com/auth/urs/login.json?app=web&_='+timestamp())

        data = {
            'username': username,
            'password': hashlib.md5(password.encode('utf-8')).hexdigest()
        }
        self.post('https://note.youdao.com/login/acc/urs/verify/check?app=web&product=YNOTE&tp=urstoken&cf=6&fr=1&systemName=&deviceType=&ru=https%3A%2F%2Fnote.youdao.com%2FsignIn%2F%2FloginCallback.html&er=https%3A%2F%2Fnote.youdao.com%2FsignIn%2F%2FloginCallback.html&vcode=&systemName=linux&deviceType=linuxPC&timestamp='+timestamp(), data=data, allow_redirects=True)
        self.get('https://note.youdao.com/login/acc/login?app=web&product=YNOTE&tp=urstoken&cf=6&fr=1&systemName=&deviceType=&ru=https%3A%2F%2Fnote.youdao.com%2FsignIn%2F%2FloginCallback.html&er=https%3A%2F%2Fnote.youdao.com%2FsignIn%2F%2FloginCallback.html&vcode=&systemName=linux&deviceType=linuxPC&timestamp='+timestamp())
        self.get('https://note.youdao.com/signIn//loginCallback.html?product=YNOTE&tp=urstoken&app=web&s=true')
        self.get('https://note.youdao.com/yws/mapi/user?method=get&multilevelEnable=true&_='+timestamp())
        print(self.cookies)

        self.cstk = self.cookies.get('YNOTE_CSTK')


    def getNoteFolder(self):
        try:
            data = {
                'path': '/',
                'dirOnly': 'true',
                'f': 'true',
                'cstk': self.cstk
            }
            response = self.post('https://note.youdao.com/yws/api/personal/file?method=listEntireByParentPath&keyfrom=web', data=data)
            content = response.content.decode('utf-8')
            jsonList = json.loads(content)
            for i in jsonList:
                id = (i['fileEntry']['id'])
                cate = (i['fileEntry']['name'])
                self.getNoteList(id, cate)
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('重新在web浏览器登录一遍，再执行此文件')

    def getNoteList(self, id, cate):
        response = self.get('https://note.youdao.com/yws/api/personal/file/'+id+'?all=true&f=true&len=100&sort=1&isReverse=false&method=listPageByParentId&keyfrom=web&cstk='+self.cstk)
        content = response.content.decode('utf-8')
        jsonList = json.loads(content)['entries']
        for i in jsonList:
            id = (i['fileEntry']['id'])
            name = (i['fileEntry']['name'])
            if i['fileEntry']['dir'] is True:
                self.getNoteList(id, cate+'/'+name)
            else:
                try:
                    self.getNote(id, name, cate)
                except Exception as e:
                    print('### CRUSH ON ' + name)
                    print(e)

    def getNote(self, id, name, parent):
        data = {
            'fileId': id,
            'version': -1,
            'read': 'true',
            'cstk': self.cstk
        }
        response = self.post('https://note.youdao.com/yws/api/personal/sync?method=download&keyfrom=web', data=data)
        content = (response.content.decode('utf-8'))
        print('+++' + name + '+++')
        if not os.path.exists(parent):
            os.makedirs(parent)
        if not name.endswith('.md'):
            name += '.html'
        # with open('%s/%s' % (parent, name), 'w') as fp:
        with codecs.open('%s/%s' % (parent, name), 'w', encoding='utf-8') as fp:
            fp.write(content)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('参数不符合： *.py [username] [password] ')
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    sess = YouDaoNoteSession()
    sess.login(username, password)
    sess.getNoteFolder()

