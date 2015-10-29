import socket
from threading import Thread
from functools import wraps
from sys import stderr, stdout

def thread(func):
    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target = func, args = args, kwargs = kwargs)
        func_hl.start()
        return func_hl
    return async_func

class IRCBot(object):

    def __init__(self, server_tuple, nick, channel_list, debug=False, quiet=False):
        self.joined = []
        self.server_tuple = server_tuple
        self.debug = debug
        self.quiet = quiet
        self.nick = nick
        self.channel_list = channel_list
        self.connected = False

    def connect(self):
        if not self.connected:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            try:
                self.socket.connect(self.server_tuple)
                self.connected = True
            except Exception as e:
                print "Bot not connected: " + str(e)
                return
            self.pdebug("Bot connected")
            self.recvloop()
            self.sendline("USER " + self.nick + " " + self.nick + " " + self.nick + " :hi" )
            self.setnick(self.nick)
            self.join_all(self.channel_list)
        else:
            print "Bot already connected"

    def disconnect(self):
        if self.connected:
            self.socket.close()
            self.connected = False
            self.joined = []
            self.pdebug("Bot disconnected")
        else:
            print("Bot is not connected")

    def pdebug(self, msg):
        if self.debug:
            stderr.write("DEBUG: " + msg + "\n")

    def reconnect(self):
        self.close()
        self.connect()

    @thread
    def recvloop(self):
        self.pdebug("entering recvloop")
        while 1:
            if self.connected:
                try:
                    out = self.socket.recv(2048)
                    if not self.quiet:
                        stdout.write(out)
                    if out.startswith("PING"):
                        self.sendline("PONG :" + self.server_tuple[0])
                except socket.timeout:
                    pass
            else:
                self.pdebug("recvloop exiting")
                return

    def setnick(self, nick):
        self.nick = nick
        self.sendline("NICK " + nick)

    def sendline(self, text):
        if self.connected:
            try:
                self.pdebug("Sending: " + text)
                self.socket.send(text + "\n")
            except socket.timeout as e:
                self.disconnect()
                print "Connection was lost! ({}): {}".format(self.nick, str(e))
        else:
            print "Bot is not connected"

    def join_one(self, channel):
        if channel.startswith("#"):
            self.sendline("JOIN " + channel)
            self.joined.append(channel)
        else:
            print "'" + channel + "' is not a valid channel"

    def join_all(self, channels):
        for c in channels:
            self.join_one(c)

    def leave_one(self, channel):
        if channel.startswith("#") and channel in self.joined:
            self.sendline("PART " + channel)
            self.joined.remove(channel)
        else:
            print "'" + channel + "' is not a valid channel or is not joined"

    def msg(self, chan_usr, msg):
        self.sendline("PRIVMSG " + chan_usr + " :" + msg)

    def msg_all_channels(self, msg):
        for c in self.joined:
            self.msg(c, msg)
