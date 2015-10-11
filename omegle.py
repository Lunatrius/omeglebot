import json
import urllib
import urllib2

import socket
import thread
import traceback


class Event:
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def call(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)


class Omegle:
    status = 'disconnected'  # disconnected, connecting, connected, disconnected

    on_connected = Event()
    on_disconnected = Event()
    on_msg = Event()
    on_error = Event()
    strangerID = None

    def send(self, page, message):
        req = urllib2.Request('http://omegle.com/' + page, urllib.urlencode(message))
        response = urllib2.urlopen(req)
        content = response.read()

        if content == 'win':
            return []

        try:
            return json.loads(content)
        except Exception as e:
            print(['something broke', content, e])
            return []

    def get_event(self):
        response = self.send('events', {'id': self.strangerID})
        if type(response) != list:
            return []

        return response

    def start_session(self):
        return self.send('start', {"rcs": 1})

    def connect(self):
        if self.status == 'disconnected' and self.strangerID is None:
            self.status = 'connecting'
            self.strangerID = self.start_session()

            if self.strangerID == '':
                self.status = 'disconnected'
                self.on_disconnected.call('invalidSession')
                self.strangerID = None
            else:
                thread.start_new_thread(self.event_loop, ())

    def event_loop(self):
        try:
            bot = False
            typing = False
            while self.strangerID is not None:
                events = self.get_event()
                for event in events:
                    if event[0] == 'connected':
                        self.status = 'connected'
                        self.on_connected.call()
                    elif event[0] == 'gotMessage':
                        if not bot and not typing:
                            self.on_msg.call('*status: possibly a bot')
                            bot = True
                        self.on_msg.call(event[1].replace('\\/', '/'))
                    elif event[0] == 'antinudeBanned':
                        self.strangerID = None
                        self.on_disconnected.call('antinudeBanned (%s)' % (event[1].replace('\\/', '/')))
                        self.status = 'disconnected'
                    elif event[0] == 'strangerDisconnected':
                        self.strangerID = None
                        self.on_disconnected.call('strangerDisconnected')
                        self.status = 'disconnected'
                    elif event[0] == 'typing' and not typing:
                        self.on_msg.call('*status: appears to be a human')
                        typing = True
                    elif event[0] in ['waiting', 'typing', 'stoppedTyping', 'statusInfo', 'identDigests']:
                        print(('EVENT', event))
                    else:
                        self.on_error.call('%s: %s' % (event[0], event[1] if len(event) >= 2 else 'N/A'))
        except:
            self.on_error.call(traceback.format_exc())
            self.on_disconnected.call('Error')
            self.status = 'disconnected'

    def msg(self, msg):
        if self.status == 'connected' and self.strangerID is not None:
            try:
                self.send('send', {'msg': msg, 'id': self.strangerID})
            except:
                self.on_error.call(traceback.format_exc())

    def disconnect(self):
        if self.status == 'connected' and self.strangerID is not None:
            # self.status = 'disconnected'
            try:
                # send a disconnect packet and just wait for the event loop to die due to disconnection
                self.send('disconnect', {'id': self.strangerID})
                self.strangerID = None
                self.status = 'disconnected'
                self.on_disconnected.call()
            except:
                self.on_error.call(traceback.format_exc())
