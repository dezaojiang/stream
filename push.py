#-*- coding: utf-8 -*-
#!/usr/bin/env python

import sys, collections, urllib2, json, time, socket, re, datetime, zlib, md5, threading, os, subprocess




#推流线程
class push(threading.Thread):
    def __init__(self, casedict, timegap):
        threading.Thread.__init__(self)
        self.casedict = casedict
        self.timegap = timegap
        self.osname = os.name
        if self.osname == 'posix':
            self.ffmpeg = './ffmpeg/ffmpeg -loglevel quiet -strict experimental -i ./ffmpeg/mp4.mp4 -i ./ffmpeg/metadata.txt'
        elif self.osname == 'nt':
            self.ffmpeg = 'ffmpeg\\ffmpeg.exe -loglevel quiet -strict experimental -i ffmpeg\\mp4.mp4 -i ffmpeg\\metadata.txt'
        self.puhpara = ' '.join([
                                    '-map_metadata',     '1',
                                    '-f',                self.casedict['rtmppuhfmtctn'],
                                    '-vcodec',           self.casedict['rtmppuhvcdc'],
                                    '-b',                self.casedict['rtmppuhvbrte'],
                                    '-r',                self.casedict['rtmppuhvfrmrte'],
                                    '-s',                self.casedict['rtmppuhvres'],
                                    '-sc_threshold',     '0',
##                                    '-force_key_frames', '"expr:gte(t,n_forced*7)"',
                                    '-force_key_frames', '"expr:gte(t,n_forced*1)"',
                                    '-acodec',           self.casedict['rtmppuhacdc'],
                                    '-ab',               self.casedict['rtmppuhabrte'],
                                    '-ar',               self.casedict['rtmppuhasplrte'],
                                    '-ac',               self.casedict['rtmppuhachn']
                               ])
        if self.osname == 'posix':
            self.ffprob = '| ./ffmpeg/ffprobe -hide_banner -show_entries frame=media_type,key_frame,pkt_pts -i -'
        elif self.osname == 'nt':
            self.ffprob = '| ffmpeg\\ffprobe.exe -hide_banner -show_entries frame=media_type,key_frame,pkt_pts -i -'

    def run(self):
        puhproc = subprocess.Popen(' '.join([self.ffmpeg, self.puhpara, '-', self.puhpara, self.casedict['rtmppuhurl'], self.ffprob]), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True)
        vfldflag = True
        afldflag = True
        vflag = False
        aflag = False
        kflag = False
        puhstrt = time.time()
        while ((self.osname == 'posix' and puhproc.poll() is None) or (self.osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(puhproc.pid) + '"', '| find.exe', '"' + str(puhproc.pid) + '"', '2>&1>nul']), shell = True) == 0)) and time.time() < puhstrt + 60 * 17:
            line = puhproc.stdout.readline()
            if line == 'media_type=video\n':
                vflag = True
                aflag = False
                kflag = False
                continue
            if line == 'media_type=audio\n':
                vflag = False
                aflag = True
                kflag = False
                continue
            if vflag or aflag:
                if line == 'key_frame=1\n':
                    kflag = True
                    continue
                if line == 'key_frame=0\n':
                    kflag = False
                    continue
            if kflag and line.startswith('pkt_pts='):
                if vflag:
                    if vfldflag:
                        vfldflag = False
                        self.casedict['rtmppuhvfld'] = time.time() + self.timegap
                    self.casedict['rtmppuhvlog'][line.rstrip().split('=')[1]] = time.time() + self.timegap
                    vflag = False
                    aflag = False
                    kflag = False
                    continue
                if aflag:
                    if afldflag:
                        afldflag = False
                        self.casedict['rtmppuhafld'] = time.time() + self.timegap
                    self.casedict['rtmppuhalog'][line.rstrip().split('=')[1]] = time.time() + self.timegap
                    vflag = False
                    aflag = False
                    kflag = False
                    continue
        self.casedict['rtmppuhdrt'] = time.time() - puhstrt
        if self.osname == 'posix' and puhproc.poll() is None:
            puhproc.kill()
            puhproc.wait()
        elif self.osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(puhproc.pid) + '"', '| find.exe', '"' + str(puhproc.pid) + '"', '2>&1>nul']), shell = True) == 0: #Issue 2475: Popen.poll always returns None，似乎python2.7.1/2.7.4仍存在这个bug
            subprocess.call(' '.join(['taskkill.exe /f /t /pid', str(puhproc.pid), '2>&1>nul']), shell = True) #Popen.kill 似乎在windows无效，无论shell=True/False
            puhproc.wait()
        del puhproc




def main():
    #公共变量
    pullservip = '127.0.0.1'
    pullservport = None
    talkpair = None
    logrefer = None
    for i in range(1, len(sys.argv) - 1):
        if sys.argv[i].lower() == '-pullserverip':
            pullservip = sys.argv[i + 1]
        elif sys.argv[i].lower() == '-pullserverport':
            pullservport = sys.argv[i + 1]
        elif sys.argv[i].lower() == '-talkpair':
            talkpair = sys.argv[i + 1]
        elif sys.argv[i].lower() == '-logrefer':
            logrefer = sys.argv[i + 1]
    try:
        int(pullservport)
    except:
        print 'please pass -pullservport 49152-65535'
        return
    if not 49152 <= int(pullservport) <= 65535:
        print 'please pass -pullservport 49152-65535'
        return
    if talkpair is None:
        print 'please pass -talkpair'
        return

    if logrefer is not None and logrefer.lower() == 'true':
        logname = ''.join(['log/live_', talkpair, '.log'])
    else:
        logname = 'log/live.log'

    casedict = collections.OrderedDict()
    casedict['casename'] = None

    casefile = open('case/live.ini')
    logfile = open(logname, mode = 'w+', buffering = 0)

    talkhead = dict()
    talkhead['talkpair'] = talkpair

    timegap = 0.0
    #对时
    for i in range(0, 7):
        try:
            timeresp = urllib2.urlopen('http://www.convert-unix-time.com/api?timestamp=now', timeout = 17)
            timedict = json.loads(timeresp.read())
            timeresp.close()
        except:
            time.sleep(0.7)
            continue
        if timedict.has_key(u'timestamp') and type(timedict[u'timestamp']) is int:
            timegap = timedict[u'timestamp'] - time.time()
            break

    pullserverwanip = ''
    for i in range(0, 7):
        try:
##            wanipresp = urllib2.urlopen('http://ip-api.com/json', timeout = 17)
            wanipresp = urllib2.urlopen('http://api.ipify.org/?format=json', timeout = 17)
            wanipdict = json.loads(wanipresp.read())
            wanipresp.close()
        except:
            time.sleep(0.7)
            continue
##        if wanipdict.has_key(u'query') and type(wanipdict[u'query']) is unicode:
        if wanipdict.has_key(u'ip') and type(wanipdict[u'ip']) is unicode:
##            pullserverwanip = wanipdict[u'query'].encode(encoding = 'utf8')
            pullserverwanip = wanipdict[u'ip'].encode(encoding = 'utf8')
            break
    pulltimereq = urllib2.Request(''.join(['http://', pullservip, ':', pullservport, '/time']), headers = talkhead)
    for i in range(0, 7):
        try:
            pulltimereqstrt = time.time()
            pulltimeresp = urllib2.urlopen(pulltimereq, timeout = 17)
            pulltimereqstop = time.time()
        except:
            if i == 6:
                print 'cannot connect to', ''.join([pullservip, ':', pullservport, ':', talkpair])
                return
            time.sleep(7)
            continue
        #www.convert-unix-time.com的返回值有误差，用下面的方法校正
        if pulltimeresp.headers.getheader('talkpair') == talkpair:
            if pullservip == '127.0.0.1':
                timegap = float(pulltimeresp.headers.getheader('timegap'))
            elif pulltimeresp.headers.getheader('pullserverlanip') == socket.gethostbyname(socket.gethostname()):
                timegap = float(pulltimeresp.headers.getheader('timegap'))
            elif pulltimeresp.headers.getheader('pullserverwanip') == pullserverwanip:
                timegap = float(pulltimeresp.headers.getheader('timegap'))
            elif float(pulltimeresp.headers.getheader('nowtime')) + float(pulltimeresp.headers.getheader('timegap')) + ((pulltimereqstop - pulltimereqstrt) / 2) < time.time() + timegap:
##                timegap = timegap + float(pulltimeresp.headers.getheader('nowtime')) + float(pulltimeresp.headers.getheader('timegap')) + ((pulltimereqstop - pulltimereqstrt) / 2) - (time.time() + timegap)
                timegap = float(pulltimeresp.headers.getheader('nowtime')) + float(pulltimeresp.headers.getheader('timegap')) + ((pulltimereqstop - pulltimereqstrt) / 2) - time.time()
            pulltimeresp.close()
            break
        elif i == 6:
            print 'cannot connect to', ''.join([pullservip, ':', pullservport, ':', talkpair])
            return

    #打印pullserverip、pullserverport、talkpair、logfile、timegap
    print 'PULLSERVERIP :  ', pullservip
    print 'PULLSERVERPORT :', pullservport
    print 'TALKPAIR :      ', talkpair
    print 'LOGFILE :       ', logname

    #http通信、log分析、log落盘
    def flow():
        #flow的子方法，把json.loads得到的collections.OrderedDict，从unicode还原到str
        def strify(input):
            if type(input) is collections.OrderedDict:
                output = collections.OrderedDict()
                for k, v in input.iteritems():
                    output[strify(k)] = strify(v)
                return output
            elif type(input) is unicode:
                return input.encode(encoding = 'utf8')
            else:
                return input

        talkhead['casename'] = casedict['casename']
        #http下发job
        print '[job]', casedict['casename'] #debug
        jobreq = urllib2.Request(''.join(['http://', pullservip, ':', pullservport, '/job']), headers = talkhead)
        for i in range(0, 7):
            try:
                jobresp = urllib2.urlopen(jobreq, timeout = 17)
            except Exception as e:
                print e, '@下发job' #debug
                if id == 6:
                    return
                time.sleep(7)
                continue
            if jobresp.headers.getheader('talkpair') == talkpair and jobresp.headers.getheader('casename') == casedict['casename'] and jobresp.read() == 'job receive':
                jobresp.close()
                break
            elif i == 6:
                jobresp.close()
                return

        casedict['casetime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
##        time.sleep(0.7)
        puhthrd = push(casedict, timegap)
        puhthrd.start()
        puhthrd.join()
        del puhthrd
        time.sleep(7)

        #http回收log
        print '[log]', casedict['casename'] #debug
        logreq = urllib2.Request(''.join(['http://', pullservip, ':', pullservport, '/log']), headers = talkhead)
        for i in range(0, 7):
            try:
                logresp = urllib2.urlopen(logreq, timeout = 17)
            except Exception as e:
                print e, '@回收log' #debug
                time.sleep(17)
                continue
            if logresp.headers.getheader('talkpair') == talkpair and logresp.headers.getheader('casename') == casedict['casename']:
                try:
                    logtext = zlib.decompress(logresp.read())
                except Exception as e:
                    print e, '@解压log' #debug
                    logresp.close()
                    time.sleep(17)
                    continue
##                print md5.md5(logtext).hexdigest(), '@md5 logdict json' #tmp debug
                if md5.md5(logtext).hexdigest() == logresp.headers.getheader('logmd5'):
                    logresp.close()
                    try:
                        logdict = json.loads(logtext, object_pairs_hook = collections.OrderedDict)
                    except Exception as e:
                        print e, '序列化log' #debug
                        time.sleep(17)
                        continue
                    strlogdict = strify(logdict)
                    del logdict
                    for k, v in strlogdict.iteritems():
                        if casedict[k] is None and v is not None:
                            casedict[k] = v
                    time.sleep(17)

        casedict['rtmppuhvbrte'] = float(casedict['rtmppuhvbrte'])
        casedict['rtmppuhvfrmrte'] = float(casedict['rtmppuhvfrmrte'])
        casedict['rtmppuhabrte'] = float(casedict['rtmppuhabrte'])
        casedict['rtmppuhasplrte'] = float(casedict['rtmppuhasplrte'])
        casedict['rtmppuhachn'] = float(casedict['rtmppuhachn'])
        if len(casedict['rtmppuhvlog']) == 0:
            del casedict['rtmppuhvlog']
            casedict['rtmppuhvlog'] = None
        if len(casedict['rtmppuhalog']) == 0:
            del casedict['rtmppuhalog']
            casedict['rtmppuhalog'] = None

        #rtmp push log分析
##        if casedict['rtmppuhdrt'] is not None:
##            if casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
##                casedict['rtmppuhsptrlt'] = 'PASSED'
##            elif not casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
##                casedict['rtmppuhsptrlt'] = 'FAILED'
        if casedict['rtmppuhvfld'] is not None:
            if casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
                casedict['rtmppuhsptrlt'] = 'PASSED'
            elif not casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
                casedict['rtmppuhsptrlt'] = 'FAILED'
        if casedict['rtmppuhafld'] is not None:
            if casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
                casedict['rtmppuhsptrlt'] = 'PASSED'
            elif not casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
                casedict['rtmppuhsptrlt'] = 'FAILED'
        if casedict['rtmppuhvlog'] is not None:
            if casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
                casedict['rtmppuhsptrlt'] = 'PASSED'
            elif not casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
                casedict['rtmppuhsptrlt'] = 'FAILED'
        if casedict['rtmppuhalog'] is not None:
            if casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
                casedict['rtmppuhsptrlt'] = 'PASSED'
            elif not casedict['rtmppuhspt'] and casedict['rtmppuhsptrlt'] is None:
                casedict['rtmppuhsptrlt'] = 'FAILED'

        #rtmp pull log分析
        if casedict['rtmppulmta'] is not None:
            casedict['rtmpmtarlt'] = 'PASSED'
            for k in casedict['rtmppuhmta'].keys():
                if not (casedict['rtmppulmta'].has_key(k) and casedict['rtmppulmta'][k] == casedict['rtmppuhmta'][k]):
                    casedict['rtmpmtarlt'] = 'FAILED'
                    break
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulfmtctn'] is not None:
            pulfmtctnequ = casedict['rtmppulfmtctn']
            if casedict['rtmppulfmtctn'] == 'hls,applehttp':
                pulfmtctnequ = 'flv'
            if casedict['rtmppuhfmtctn'] in pulfmtctnequ:
                casedict['rtmpfmtctnrlt'] = 'PASSED'
            else:
                casedict['rtmpfmtctnrlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulvcdc'] is not None:
            pulvcdcequ = casedict['rtmppulvcdc']
            if pulvcdcequ == 'h264':
                pulvcdcequ = 'libx264'
            if pulvcdcequ == casedict['rtmppuhvcdc']:
                casedict['rtmpvcdcrlt'] = 'PASSED'
            else:
                casedict['rtmpvcdcrlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulvbrte'] is not None:
            pulvbrteequ = float(casedict['rtmppulvbrte'].split(' ')[0])
            if casedict['rtmppulvbrte'].split(' ')[1] == '':
                if 1 <= casedict['rtmppuhvbrte'] < 1000 and casedict['rtmppuhvbrte'] - 1 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1:
                    casedict['rtmpvbrterlt'] = 'PASSED'
                else:
                    casedict['rtmpvbrterlt'] = 'FAILED'
            elif casedict['rtmppulvbrte'].split(' ')[1] == 'k':
                pulvbrteequ *= 1000
                if 1000 <= casedict['rtmppuhvbrte'] < 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1000:
                    casedict['rtmpvbrterlt'] = 'PASSED'
                else:
                    casedict['rtmpvbrterlt'] = 'FAILED'
            elif casedict['rtmppulvbrte'].split(' ')[1] == 'm':
                pulvbrteequ *= 1000 * 1000
                if 1000 * 1000 <= casedict['rtmppuhvbrte'] < 1000 * 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 * 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1000 * 1000:
                    casedict['rtmpvbrterlt'] = 'PASSED'
                else:
                    casedict['rtmpvbrterlt'] = 'FAILED'
            elif casedict['rtmppulvbrte'].split(' ')[1] == 'g':
                pulvbrteequ *= 1000 * 1000 * 1000
                if 1000 * 10000 * 1000 <= casedict['rtmppuhvbrte'] < 1000 * 1000 * 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 * 1000 * 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1000 * 1000 * 1000:
                    casedict['rtmpvbrterlt'] = 'PASSED'
                else:
                    casedict['rtmpvbrterlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulvfrmrte'] is not None:
            pulvfrmrteequ = float(casedict['rtmppulvfrmrte'])
            if casedict['rtmppuhvfrmrte'] - 1 <= pulvfrmrteequ <= casedict['rtmppuhvfrmrte'] + 1:
                casedict['rtmpvfrmrterlt'] = 'PASSED'
            else:
                casedict['rtmpvfrmrterlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulvres'] is not None:
            if casedict['rtmppulvres'] == casedict['rtmppuhvres']:
                casedict['rtmpvresrlt'] = 'PASSED'
            else:
                casedict['rtmpvresrlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulacdc'] is not None:
            pulacdcequ = casedict['rtmppulacdc']
            if pulacdcequ == 'mp3':
                pulacdcequ = 'libmp3lame'
            if pulacdcequ == casedict['rtmppuhacdc']:
                casedict['rtmpacdcrlt'] = 'PASSED'
            else:
                casedict['rtmpacdcrlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulabrte'] is not None:
            pulabrteequ = float(casedict['rtmppulabrte'].split(' ')[0])
            if casedict['rtmppulabrte'].split(' ')[1] == '':
                if 1 <= casedict['rtmppuhabrte'] < 1000 and casedict['rtmppuhabrte'] - 1 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1:
                    casedict['rtmpabrterlt'] = 'PASSED'
                else:
                    casedict['rtmpabrterlt'] = 'FAILED'
            elif casedict['rtmppulabrte'].split(' ')[1] == 'k':
                pulabrteequ *= 1000
                if 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000:
                    casedict['rtmpabrterlt'] = 'PASSED'
                else:
                    casedict['rtmpabrterlt'] = 'FAILED'
            elif casedict['rtmppulabrte'].split(' ')[1] == 'm':
                pulabrteequ *= 1000 * 1000
                if 1000 * 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 * 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000 * 1000:
                    casedict['rtmpabrterlt'] = 'PASSED'
                else:
                    casedict['rtmpabrterlt'] = 'FAILED'
            elif casedict['rtmppulabrte'].split(' ')[1] == 'g':
                pulabrteequ *= 1000 * 1000 * 1000
                if 1000 * 1000 * 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 * 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 * 1000 * 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000 * 1000 * 1000:
                    casedict['rtmpabrterlt'] = 'PASSED'
                else:
                    casedict['rtmpabrterlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulasplrte'] is not None:
            pulasplrteequ = float(casedict['rtmppulasplrte'])
            if casedict['rtmppuhasplrte'] - 1 <= pulasplrteequ <= casedict['rtmppuhasplrte'] + 1:
                casedict['rtmpasplrterlt'] = 'PASSED'
            else:
                casedict['rtmpasplrterlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulachn'] is not None:
            pulchnequ = casedict['rtmppulachn']
            if pulchnequ == 'mono':
                pulchnequ = 1.0
            elif pulchnequ == 'stereo':
                pulchnequ = 2.0
            else:
                pulchnequ = float(casedict['rtmppulachn'])
            if pulchnequ == casedict['rtmppuhachn']:
                casedict['rtmpachnrlt'] = 'PASSED'
            else:
                casedict['rtmpachnrlt'] = 'FAILED'
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
        if casedict['rtmppulvfld'] is not None:
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
            if casedict['rtmppuhvfld'] is not None:
                casedict['rtmpvflddly'] = casedict['rtmppulvfld'] - casedict['rtmppuhvfld']
        if casedict['rtmppulafld'] is not None:
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
            if casedict['rtmppuhafld'] is not None:
                casedict['rtmpaflddly'] = casedict['rtmppulafld'] - casedict['rtmppuhafld']
        if casedict['rtmppulvlog'] is not None:
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
            if casedict['rtmppuhvlog'] is not None:
                casedict['rtmpvlosfrm'] = 0
                casedict['rtmpvavgdly'] = 0
                c = 0
                cflag = False
                for k in casedict['rtmppuhvlog'].keys():
                    if casedict['rtmppulvlog'].has_key(k):
                        t = casedict['rtmppulvlog'][k] - casedict['rtmppuhvlog'][k]
                        casedict['rtmpvavgdly'] += t
                        if casedict['rtmpvmaxdly'] is None:
                            casedict['rtmpvmaxdly'] = t
                        elif t > casedict['rtmpvmaxdly']:
                            casedict['rtmpvmaxdly'] = t
                        if casedict['rtmpvmindly'] is None:
                            casedict['rtmpvmindly'] = t
                        elif t < casedict['rtmpvmindly']:
                            casedict['rtmpvmindly'] = t

                        if cflag:
                            cflag = False
                            if casedict['rtmpvmaxconlosfrm'] is None:
                                casedict['rtmpvmaxconlosfrm'] = c
                            elif c > casedict['rtmpvmaxconlosfrm']:
                                casedict['rtmpvmaxconlosfrm'] = c
                            if casedict['rtmpvminconlosfrm'] is None:
                                casedict['rtmpvminconlosfrm'] = c
                            elif c < casedict['rtmpvminconlosfrm']:
                                casedict['rtmpvminconlosfrm'] = c
                            c = 0
                    else:
                        casedict['rtmpvlosfrm'] += 1
                        c += 1
                        cflag = True
                #整个循环出来结果仍旧为none，一种情况是完全没丢帧，另一种情况是直到末尾才开始连续丢帧
                if casedict['rtmpvlosfrm'] == 0:
                    casedict['rtmpvmaxconlosfrm'] = 0
                    casedict['rtmpvminconlosfrm'] = 0
                elif cflag:
                    if casedict['rtmpvmaxconlosfrm'] is None:
                        casedict['rtmpvmaxconlosfrm'] = c
                    elif c > casedict['rtmpvmaxconlosfrm']:
                        casedict['rtmpvmaxconlosfrm'] = c
                    if casedict['rtmpvminconlosfrm'] is None:
                        casedict['rtmpvminconlosfrm'] = c
                    elif c < casedict['rtmpvminconlosfrm']:
                        casedict['rtmpvminconlosfrm'] = c
                casedict['rtmpvtolfrm'] = len(casedict['rtmppuhvlog'])
                casedict['rtmpvlosfrmrto'] = float(casedict['rtmpvlosfrm']) / casedict['rtmpvtolfrm']
                if casedict['rtmpvtolfrm'] != casedict['rtmpvlosfrm']:
                    casedict['rtmpvavgdly'] /= (casedict['rtmpvtolfrm'] - casedict['rtmpvlosfrm'])
        if casedict['rtmppulalog'] is not None:
            if casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'PASSED'
            elif not casedict['rtmppulspt'] and casedict['rtmppulsptrlt'] is None:
                casedict['rtmppulsptrlt'] = 'FAILED'
            if casedict['rtmppuhalog'] is not None:
                casedict['rtmpalosfrm'] = 0
                casedict['rtmpaavgdly'] = 0
                c = 0
                cflag = False
                for k in casedict['rtmppuhalog'].keys():
                    if casedict['rtmppulalog'].has_key(k):
                        t = casedict['rtmppulalog'][k] - casedict['rtmppuhalog'][k]
                        casedict['rtmpaavgdly'] += t
                        if casedict['rtmpamaxdly'] is None:
                            casedict['rtmpamaxdly'] = t
                        elif t > casedict['rtmpamaxdly']:
                            casedict['rtmpamaxdly'] = t
                        if casedict['rtmpamindly'] is None:
                            casedict['rtmpamindly'] = t
                        elif t < casedict['rtmpamindly']:
                            casedict['rtmpamindly'] = t

                        if cflag:
                            cflag = False
                            if casedict['rtmpamaxconlosfrm'] is None:
                                casedict['rtmpamaxconlosfrm'] = c
                            elif c > casedict['rtmpamaxconlosfrm']:
                                casedict['rtmpamaxconlosfrm'] = c
                            if casedict['rtmpaminconlosfrm'] is None:
                                casedict['rtmpaminconlosfrm'] = c
                            elif c < casedict['rtmpaminconlosfrm']:
                                casedict['rtmpaminconlosfrm'] = c
                            c = 0
                    else:
                        casedict['rtmpalosfrm'] += 1
                        c += 1
                        cflag = True
                #整个循环出来结果仍旧为none，一种情况是完全没丢帧，另一种情况是直到末尾才开始连续丢帧
                if casedict['rtmpalosfrm'] == 0:
                    casedict['rtmpamaxconlosfrm'] = 0
                    casedict['rtmpaminconlosfrm'] = 0
                elif cflag:
                    if casedict['rtmpamaxconlosfrm'] is None:
                        casedict['rtmpamaxconlosfrm'] = c
                    elif c > casedict['rtmpamaxconlosfrm']:
                        casedict['rtmpamaxconlosfrm'] = c
                    if casedict['rtmpaminconlosfrm'] is None:
                        casedict['rtmpaminconlosfrm'] = c
                    elif c < casedict['rtmpaminconlosfrm']:
                        casedict['rtmpaminconlosfrm'] = c
                casedict['rtmpatolfrm'] = len(casedict['rtmppuhalog'])
                casedict['rtmpalosfrmrto'] = float(casedict['rtmpalosfrm']) / casedict['rtmpatolfrm']
                if casedict['rtmpatolfrm'] != casedict['rtmpalosfrm']:
                    casedict['rtmpaavgdly'] /= (casedict['rtmpatolfrm'] - casedict['rtmpalosfrm'])

        #hdl pull log分析
        if casedict['hdlpulmta'] is not None:
            casedict['hdlmtarlt'] = 'PASSED'
            for k in casedict['rtmppuhmta'].keys():
                if not (casedict['hdlpulmta'].has_key(k) and casedict['hdlpulmta'][k] == casedict['rtmppuhmta'][k]):
                    casedict['hdlmtarlt'] = 'FAILED'
                    break
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulfmtctn'] is not None:
            pulfmtctnequ = casedict['hdlpulfmtctn']
            if casedict['hdlpulfmtctn'] == 'hls,applehttp':
                pulfmtctnequ = 'flv'
            if casedict['rtmppuhfmtctn'] in pulfmtctnequ:
                casedict['hdlfmtctnrlt'] = 'PASSED'
            else:
                casedict['hdlfmtctnrlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulvcdc'] is not None:
            pulvcdcequ = casedict['hdlpulvcdc']
            if pulvcdcequ == 'h264':
                pulvcdcequ = 'libx264'
            if pulvcdcequ == casedict['rtmppuhvcdc']:
                casedict['hdlvcdcrlt'] = 'PASSED'
            else:
                casedict['hdlvcdcrlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulvbrte'] is not None:
            pulvbrteequ = float(casedict['hdlpulvbrte'].split(' ')[0])
            if casedict['hdlpulvbrte'].split(' ')[1] == '':
                if 1 <= casedict['rtmppuhvbrte']  < 1000 and casedict['rtmppuhvbrte'] - 1 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1:
                    casedict['hdlvbrterlt'] = 'PASSED'
                else:
                    casedict['hdlvbrterlt'] = 'FAILED'
            elif casedict['hdlpulvbrte'].split(' ')[1] == 'k':
                pulvbrteequ *= 1000
                if 1000 <= casedict['rtmppuhvbrte']  < 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 10000:
                    casedict['hdlvbrterlt'] = 'PASSED'
                else:
                    casedict['hdlvbrterlt'] = 'FAILED'
            elif casedict['hdlpulvbrte'].split(' ')[1] == 'm':
                pulvbrteequ *= 1000 * 1000
                if 1000 * 1000 <= casedict['rtmppuhvbrte']  < 1000 * 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 * 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 10000 * 1000:
                    casedict['hdlvbrterlt'] = 'PASSED'
                else:
                    casedict['hdlvbrterlt'] = 'FAILED'
            elif casedict['hdlpulvbrte'].split(' ')[1] == 'g':
                pulvbrteequ *= 1000 * 1000 * 1000
                if 1000 * 1000 * 1000 <= casedict['rtmppuhvbrte']  < 1000 * 1000 * 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 * 1000 * 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 10000 * 1000 * 1000:
                    casedict['hdlvbrterlt'] = 'PASSED'
                else:
                    casedict['hdlvbrterlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulvfrmrte'] is not None:
            pulvfrmrteequ = float(casedict['hdlpulvfrmrte'])
            if casedict['rtmppuhvfrmrte'] - 1 <= pulvfrmrteequ <= casedict['rtmppuhvfrmrte'] + 1:
                casedict['hdlvfrmrterlt'] = 'PASSED'
            else:
                casedict['hdlvfrmrterlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulvres'] is not None:
            if casedict['hdlpulvres'] == casedict['rtmppuhvres']:
                casedict['hdlvresrlt'] = 'PASSED'
            else:
                casedict['hdlvresrlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulacdc'] is not None:
            pulacdcequ = casedict['hdlpulacdc']
            if pulacdcequ == 'mp3':
                pulacdcequ = 'libmp3lame'
            if pulacdcequ == casedict['rtmppuhacdc']:
                casedict['hdlacdcrlt'] = 'PASSED'
            else:
                casedict['hdlacdcrlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulabrte'] is not None:
            pulabrteequ = float(casedict['hdlpulabrte'].split(' ')[0])
            if casedict['hdlpulabrte'].split(' ')[1] == '':
                if 1 <= casedict['rtmppuhabrte'] < 1000 and casedict['rtmppuhabrte'] - 1 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1:
                    casedict['hdlabrterlt'] = 'PASSED'
                else:
                    casedict['hdlabrterlt'] = 'FAILED'
            elif casedict['hdlpulabrte'].split(' ')[1] == 'k':
                pulabrteequ *= 1000
                if 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000:
                    casedict['hdlabrterlt'] = 'PASSED'
                else:
                    casedict['hdlabrterlt'] = 'FAILED'
            elif casedict['hdlpulabrte'].split(' ')[1] == 'm':
                pulabrteequ *= 1000 * 1000
                if 1000 * 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 * 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000 * 1000:
                    casedict['hdlabrterlt'] = 'PASSED'
                else:
                    casedict['hdlabrterlt'] = 'FAILED'
            elif casedict['hdlpulabrte'].split(' ')[1] == 'g':
                pulabrteequ *= 1000 * 1000 * 1000
                if 1000 * 1000 * 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 * 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 * 1000 * 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000 * 1000 * 1000:
                    casedict['hdlabrterlt'] = 'PASSED'
                else:
                    casedict['hdlabrterlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulasplrte'] is not None:
            pulasplrteequ = float(casedict['hdlpulasplrte'])
            if casedict['rtmppuhasplrte'] - 1 <= pulasplrteequ <= casedict['rtmppuhasplrte'] + 1:
                casedict['hdlasplrterlt'] = 'PASSED'
            else:
                casedict['hdlasplrterlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulachn'] is not None:
            pulchnequ = casedict['hdlpulachn']
            if pulchnequ == 'mono':
                pulchnequ = 1.0
            elif pulchnequ == 'stereo':
                pulchnequ = 2.0
            else:
                pulchnequ = float(casedict['hdlpulachn'])
            if pulchnequ == casedict['rtmppuhachn']:
                casedict['hdlachnrlt'] = 'PASSED'
            else:
                casedict['hdlachnrlt'] = 'FAILED'
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
        if casedict['hdlpulvfld'] is not None:
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
            if casedict['rtmppuhvfld'] is not None:
                casedict['hdlvflddly'] = casedict['hdlpulvfld'] - casedict['rtmppuhvfld']
        if casedict['hdlpulafld'] is not None:
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
            if casedict['rtmppuhafld'] is not None:
                casedict['hdlaflddly'] = casedict['hdlpulafld'] - casedict['rtmppuhafld']
        if casedict['hdlpulvlog'] is not None:
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
            if casedict['rtmppuhvlog'] is not None:
                casedict['hdlvlosfrm'] = 0
                casedict['hdlvavgdly'] = 0
                c = 0
                cflag = False
                for k in casedict['rtmppuhvlog'].keys():
                    if casedict['hdlpulvlog'].has_key(k):
                        t = casedict['hdlpulvlog'][k] - casedict['rtmppuhvlog'][k]
                        casedict['hdlvavgdly'] += t
                        if casedict['hdlvmaxdly'] is None:
                            casedict['hdlvmaxdly'] = t
                        elif t > casedict['hdlvmaxdly']:
                            casedict['hdlvmaxdly'] = t
                        if casedict['hdlvmindly'] is None:
                            casedict['hdlvmindly'] = t
                        elif t < casedict['hdlvmindly']:
                            casedict['hdlvmindly'] = t

                        if cflag:
                            cflag = False
                            if casedict['hdlvmaxconlosfrm'] is None:
                                casedict['hdlvmaxconlosfrm'] = c
                            elif c > casedict['hdlvmaxconlosfrm']:
                                casedict['hdlvmaxconlosfrm'] = c
                            if casedict['hdlvminconlosfrm'] is None:
                                casedict['hdlvminconlosfrm'] = c
                            elif c < casedict['hdlvminconlosfrm']:
                                casedict['hdlvminconlosfrm'] = c
                            c = 0
                    else:
                        casedict['hdlvlosfrm'] += 1
                        c += 1
                        cflag = True
                #整个循环出来结果仍旧为none，一种情况是完全没丢帧，另一种情况是直到末尾才开始连续丢帧
                if casedict['hdlvlosfrm'] == 0:
                    casedict['hdlvmaxconlosfrm'] = 0
                    casedict['hdlvminconlosfrm'] = 0
                elif cflag:
                    if casedict['hdlvmaxconlosfrm'] is None:
                        casedict['hdlvmaxconlosfrm'] = c
                    elif c > casedict['hdlvmaxconlosfrm']:
                        casedict['hdlvmaxconlosfrm'] = c
                    if casedict['hdlvminconlosfrm'] is None:
                        casedict['hdlvminconlosfrm'] = c
                    elif c < casedict['hdlvminconlosfrm']:
                        casedict['hdlvminconlosfrm'] = c
                casedict['hdlvtolfrm'] = len(casedict['rtmppuhvlog'])
                casedict['hdlvlosfrmrto'] = float(casedict['hdlvlosfrm']) / casedict['hdlvtolfrm']
                if casedict['hdlvtolfrm'] != casedict['hdlvlosfrm']:
                    casedict['hdlvavgdly'] /= (casedict['hdlvtolfrm'] - casedict['hdlvlosfrm'])
        if casedict['hdlpulalog'] is not None:
            if casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'PASSED'
            elif not casedict['hdlpulspt'] and casedict['hdlpulsptrlt'] is None:
                casedict['hdlpulsptrlt'] = 'FAILED'
            if casedict['rtmppuhalog'] is not None:
                casedict['hdlalosfrm'] = 0
                casedict['hdlaavgdly'] = 0
                c = 0
                cflag = False
                for k in casedict['rtmppuhalog'].keys():
                    if casedict['hdlpulalog'].has_key(k):
                        t = casedict['hdlpulalog'][k] - casedict['rtmppuhalog'][k]
                        casedict['hdlaavgdly'] += t
                        if casedict['hdlamaxdly'] is None:
                            casedict['hdlamaxdly'] = t
                        elif t > casedict['hdlamaxdly']:
                            casedict['hdlamaxdly'] = t
                        if casedict['hdlamindly'] is None:
                            casedict['hdlamindly'] = t
                        elif t < casedict['hdlamindly']:
                            casedict['hdlamindly'] = t

                        if cflag:
                            cflag = False
                            if casedict['hdlamaxconlosfrm'] is None:
                                casedict['hdlamaxconlosfrm'] = c
                            elif c > casedict['hdlamaxconlosfrm']:
                                casedict['hdlamaxconlosfrm'] = c
                            if casedict['hdlaminconlosfrm'] is None:
                                casedict['hdlaminconlosfrm'] = c
                            elif c < casedict['hdlaminconlosfrm']:
                                casedict['hdlaminconlosfrm'] = c
                            c = 0
                    else:
                        casedict['hdlalosfrm'] += 1
                        c += 1
                        cflag = True
                #整个循环出来结果仍旧为none，一种情况是完全没丢帧，另一种情况是直到末尾才开始连续丢帧
                if casedict['hdlalosfrm'] == 0:
                    casedict['hdlamaxconlosfrm'] = 0
                    casedict['hdlaminconlosfrm'] = 0
                elif cflag:
                    if casedict['hdlamaxconlosfrm'] is None:
                        casedict['hdlamaxconlosfrm'] = c
                    elif c > casedict['hdlamaxconlosfrm']:
                        casedict['hdlamaxconlosfrm'] = c
                    if casedict['hdlaminconlosfrm'] is None:
                        casedict['hdlaminconlosfrm'] = c
                    elif c < casedict['hdlaminconlosfrm']:
                        casedict['hdlaminconlosfrm'] = c
                casedict['hdlatolfrm'] = len(casedict['rtmppuhalog'])
                casedict['hdlalosfrmrto'] = float(casedict['hdlalosfrm']) / casedict['hdlatolfrm']
                if casedict['hdlatolfrm'] != casedict['hdlalosfrm']:
                    casedict['hdlaavgdly'] /= (casedict['hdlatolfrm'] - casedict['hdlalosfrm'])

        #hls pull lpg分析
        if casedict['hlspulmta'] is not None:
            casedict['hlsmtarlt'] = 'PASSED'
            for k in casedict['rtmppuhmta'].keys():
                if not (casedict['hlspulmta'].has_key(k) and casedict['hlspulmta'][k] == casedict['rtmppuhmta'][k]):
                    casedict['hlsmtarlt'] = 'FAILED'
                    break
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulfmtctn'] is not None:
            pulfmtctnequ = casedict['hlspulfmtctn']
            if casedict['hlspulfmtctn'] == 'hls,applehttp':
                pulfmtctnequ = 'flv'
            if casedict['rtmppuhfmtctn'] in pulfmtctnequ:
                casedict['hlsfmtctnrlt'] = 'PASSED'
            else:
                casedict['hlsfmtctnrlt'] = 'FAILED'
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulvcdc'] is not None:
            pulvcdcequ = casedict['hlspulvcdc']
            if pulvcdcequ == 'h264':
                pulvcdcequ = 'libx264'
            if pulvcdcequ == casedict['rtmppuhvcdc']:
                casedict['hlsvcdcrlt'] = 'PASSED'
            else:
                casedict['hlsvcdcrlt'] = 'FAILED'
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
##        if casedict['hlspulvbrte'] is not None:
##            pulvbrteequ = float(casedict['hlspulvbrte'].split(' ')[0])
##            if casedict['hlspulvbrte'].split(' ')[1] == '':
##                if 1 <= casedict['rtmppuhvbrte'] < 1000 and casedict['rtmppuhvbrte'] - 1 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1:
##                    casedict['hlsvbrterlt'] = 'PASSED'
##                else:
##                    casedict['hlsvbrterlt'] = 'FAILED'
##            elif casedict['hlspulvbrte'].split(' ')[1] == 'k':
##                pulvbrteequ *= 1000
##                if 1000 <= casedict['rtmppuhvbrte'] < 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1000:
##                    casedict['hlsvbrterlt'] = 'PASSED'
##                else:
##                    casedict['hlsvbrterlt'] = 'FAILED'
##            elif casedict['hlspulvbrte'].split(' ')[1] == 'm':
##                pulvbrteequ *= 1000 * 1000
##                if 1000 * 1000 <= casedict['rtmppuhvbrte'] < 1000 * 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 * 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1000 * 1000:
##                    casedict['hlsvbrterlt'] = 'PASSED'
##                else:
##                    casedict['hlsvbrterlt'] = 'FAILED'
##            elif casedict['hlspulvbrte'].split(' ')[1] == 'g':
##                pulvbrteequ *= 1000 * 1000 * 1000
##                if 1000 * 1000 * 1000 <= casedict['rtmppuhvbrte'] < 1000 * 1000 * 1000 * 1000 and casedict['rtmppuhvbrte'] - 1000 * 1000 * 1000 <= pulvbrteequ <= casedict['rtmppuhvbrte'] + 1000 * 1000 * 1000:
##                    casedict['hlsvbrterlt'] = 'PASSED'
##                else:
##                    casedict['hlsvbrterlt'] = 'FAILED'
##            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
##                casedict['hlspulsptrlt'] = 'PASSED'
##            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
##                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulvfrmrte'] is not None:
            pulvfrmrteequ = float(casedict['hlspulvfrmrte'])
            if casedict['rtmppuhvfrmrte'] - 1 <= pulvfrmrteequ <= casedict['rtmppuhvfrmrte'] + 1:
                casedict['hlsvfrmrterlt'] = 'PASSED'
            else:
                casedict['hlsvfrmrterlt'] = 'FAILED'
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulvres'] is not None:
            if casedict['hlspulvres'] == casedict['rtmppuhvres']:
                casedict['hlsvresrlt'] = 'PASSED'
            else:
                casedict['hlsvresrlt'] = 'FAILED'
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulacdc'] is not None:
            pulacdcequ = casedict['hlspulacdc']
            if pulacdcequ == 'mp3':
                pulacdcequ = 'libmp3lame'
            if pulacdcequ == casedict['rtmppuhacdc']:
                casedict['hlsacdcrlt'] = 'PASSED'
            else:
                casedict['hlsacdcrlt'] = 'FAILED'
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulabrte'] is not None:
            pulabrteequ = float(casedict['hlspulabrte'].split(' ')[0])
            if casedict['hlspulabrte'].split(' ')[1] == '':
                if 1 <= casedict['rtmppuhabrte'] < 1000 and casedict['rtmppuhabrte'] - 1 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1:
                    casedict['hlsabrterlt'] = 'PASSED'
                else:
                    casedict['hlsabrterlt'] = 'FAILED'
            elif casedict['hlspulabrte'].split(' ')[1] == 'k':
                pulabrteequ *= 1000
                if 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000:
                    casedict['hlsabrterlt'] = 'PASSED'
                else:
                    casedict['hlsabrterlt'] = 'FAILED'
            elif casedict['hlspulabrte'].split(' ')[1] == 'm':
                pulabrteequ *= 1000 * 1000
                if 1000 * 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 * 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000 * 1000:
                    casedict['hlsabrterlt'] = 'PASSED'
                else:
                    casedict['hlsabrterlt'] = 'FAILED'
            elif casedict['hlspulabrte'].split(' ')[1] == 'g':
                pulabrteequ *= 1000 * 1000 * 1000
                if 1000 * 1000 * 1000 <= casedict['rtmppuhabrte'] < 1000 * 1000 * 1000 * 1000 and casedict['rtmppuhabrte'] - 1000 * 1000 * 1000 <= pulabrteequ <= casedict['rtmppuhabrte'] + 1000 * 1000 * 1000:
                    casedict['hlsabrterlt'] = 'PASSED'
                else:
                    casedict['hlsabrterlt'] = 'FAILED'
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulasplrte'] is not None:
            pulasplrteequ = float(casedict['hlspulasplrte'])
            if casedict['rtmppuhasplrte'] - 1 <= pulasplrteequ <= casedict['rtmppuhasplrte'] + 1:
                casedict['hlsasplrterlt'] = 'PASSED'
            else:
                casedict['hlsasplrterlt'] = 'FAILED'
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulachn'] is not None:
            pulchnequ = casedict['hlspulachn']
            if pulchnequ == 'mono':
                pulchnequ = 1.0
            elif pulchnequ == 'stereo':
                pulchnequ = 2.0
            else:
                pulchnequ = float(casedict['hlspulachn'])
            if pulchnequ == casedict['rtmppuhachn']:
                casedict['hlsachnrlt'] = 'PASSED'
            else:
                casedict['hlsachnrlt'] = 'FAILED'
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
        if casedict['hlspulvfld'] is not None:
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
            if casedict['rtmppuhvfld'] is not None:
                casedict['hlsvflddly'] = casedict['hlspulvfld'] - casedict['rtmppuhvfld']
        if casedict['hlspulafld'] is not None:
            if casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'PASSED'
            elif not casedict['hlspulspt'] and casedict['hlspulsptrlt'] is None:
                casedict['hlspulsptrlt'] = 'FAILED'
            if casedict['rtmppuhafld'] is not None:
                casedict['hlsaflddly'] = casedict['hlspulafld'] - casedict['rtmppuhafld']

        #log落盘
        for k, v in casedict.iteritems():
            if v is None:
                v = 'UNDEFINED'
            elif type(v) is collections.OrderedDict:
                dictv = v
                v = json.dumps(v)
                del dictv
            elif type(v) is not str:
                v = str(v)

            logfile.write(''.join([k, ' :', ' ' * (20 - len(k) - 2), v]))
            logfile.write('\n')

        logfile.write('\n')

    #主逻辑入口
    while True:
        line = casefile.readline()
        if line == '':
            if casedict['casename'] is not None:
                flow()
                time.sleep(7)
            break
        comoutlist = re.findall(r'^\s*#.*$', line, flags = re.DOTALL | re.IGNORECASE)
        if len(comoutlist) != 0:
            del comoutlist
            continue
        del comoutlist
        casenamelist = re.findall(r'^\s*casename\s*:\s*([^#]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
        if len(casenamelist) != 0:
            if casedict['casename'] is not None:
                flow()
                time.sleep(170)
            casedict.clear()
            casedict['casetime'] = ''
            casedict['casename'] = casenamelist[0].rstrip()
            casedict['rtmppuhspt'] = True
            casedict['rtmppuhurl'] = ''
            casedict['rtmppulspt'] = True
            casedict['rtmppulurl'] = ''
            casedict['hdlpulspt'] = True
            casedict['hdlpulurl'] = ''
            casedict['hlspulspt'] = True
            casedict['hlspulurl'] = ''
            casedict['rtmppuhmta'] = collections.OrderedDict()
            casedict['rtmppuhmta']['extra_metadata_1'] = 'extra_metadata_1'
            casedict['rtmppuhmta']['extra_metadata_2'] = 'extra_metadata_2'
            casedict['rtmppuhmta']['extra_metadata_3'] = 'extra_metadata_3'
            casedict['rtmppuhmta']['extra_metadata_4'] = 'extra_metadata_4'
            casedict['rtmppuhmta']['extra_metadata_5'] = 'extra_metadata_5'
            casedict['rtmppuhmta']['extra_metadata_6'] = 'extra_metadata_6'
            casedict['rtmppuhmta']['extra_metadata_7'] = 'extra_metadata_7'
            casedict['rtmppuhfmtctn'] = 'flv'
            casedict['rtmppuhvcdc'] = 'libx264'
            casedict['rtmppuhvbrte'] = '800000'
            casedict['rtmppuhvfrmrte'] = '24'
            casedict['rtmppuhvres'] = '854x480'
            casedict['rtmppuhacdc'] = 'aac'
            casedict['rtmppuhabrte'] = '64000'
            casedict['rtmppuhasplrte'] = '44100'
            casedict['rtmppuhachn'] = '2'
            casedict['rtmppuhdrt'] = None
            casedict['rtmppuhvfld'] = None
            casedict['rtmppuhafld'] = None
            casedict['rtmppuhvlog'] = collections.OrderedDict()
            casedict['rtmppuhalog'] = collections.OrderedDict()
            casedict['rtmppuhsptrlt'] = None
            casedict['rtmppulmta'] = None
            casedict['rtmppulfmtctn'] = None
            casedict['rtmppulvcdc'] = None
            casedict['rtmppulvbrte'] = None
            casedict['rtmppulvfrmrte'] = None
            casedict['rtmppulvres'] = None
            casedict['rtmppulacdc'] = None
            casedict['rtmppulabrte'] = None
            casedict['rtmppulasplrte'] = None
            casedict['rtmppulachn'] = None
            casedict['rtmppulvfld'] = None
            casedict['rtmppulafld'] = None
            casedict['rtmppulvlog'] = None
            casedict['rtmppulalog'] = None
            casedict['rtmppulsptrlt'] = None
            casedict['rtmpmtarlt'] = None
            casedict['rtmpfmtctnrlt'] = None
            casedict['rtmpvcdcrlt'] = None
            casedict['rtmpvbrterlt'] = None
            casedict['rtmpvfrmrterlt'] = None
            casedict['rtmpvresrlt'] = None
            casedict['rtmpacdcrlt'] = None
            casedict['rtmpabrterlt'] = None
            casedict['rtmpasplrterlt'] = None
            casedict['rtmpachnrlt'] = None
            casedict['rtmpvlosfrm'] = None
            casedict['rtmpvtolfrm'] = None
            casedict['rtmpvlosfrmrto'] = None
            casedict['rtmpvmaxconlosfrm'] = None
            casedict['rtmpvminconlosfrm'] = None
            casedict['rtmpvflddly'] = None
            casedict['rtmpvavgdly'] = None
            casedict['rtmpvmaxdly'] = None
            casedict['rtmpvmindly'] = None
            casedict['rtmpalosfrm'] = None
            casedict['rtmpatolfrm'] = None
            casedict['rtmpalosfrmrto'] = None
            casedict['rtmpamaxconlosfrm'] = None
            casedict['rtmpaminconlosfrm'] = None
            casedict['rtmpaflddly'] = None
            casedict['rtmpaavgdly'] = None
            casedict['rtmpamaxdly'] = None
            casedict['rtmpamindly'] = None
            casedict['hdlpulmta'] = None
            casedict['hdlpulfmtctn'] = None
            casedict['hdlpulvcdc'] = None
            casedict['hdlpulvbrte'] = None
            casedict['hdlpulvfrmrte'] = None
            casedict['hdlpulvres'] = None
            casedict['hdlpulacdc'] = None
            casedict['hdlpulabrte'] = None
            casedict['hdlpulasplrte'] = None
            casedict['hdlpulachn'] = None
            casedict['hdlpulvfld'] = None
            casedict['hdlpulafld'] = None
            casedict['hdlpulvlog'] = None
            casedict['hdlpulalog'] = None
            casedict['hdlpulsptrlt'] = None
            casedict['hdlmtarlt'] = None
            casedict['hdlfmtctnrlt'] = None
            casedict['hdlvcdcrlt'] = None
            casedict['hdlvbrterlt'] = None
            casedict['hdlvfrmrterlt'] = None
            casedict['hdlvresrlt'] = None
            casedict['hdlacdcrlt'] = None
            casedict['hdlabrterlt'] = None
            casedict['hdlasplrterlt'] = None
            casedict['hdlachnrlt'] = None
            casedict['hdlvlosfrm'] = None
            casedict['hdlvtolfrm'] = None
            casedict['hdlvlosfrmrto'] = None
            casedict['hdlvmaxconlosfrm'] = None
            casedict['hdlvminconlosfrm'] = None
            casedict['hdlvflddly'] = None
            casedict['hdlvavgdly'] = None
            casedict['hdlvmaxdly'] = None
            casedict['hdlvmindly'] = None
            casedict['hdlalosfrm'] = None
            casedict['hdlatolfrm'] = None
            casedict['hdlalosfrmrto'] = None
            casedict['hdlamaxconlosfrm'] = None
            casedict['hdlaminconlosfrm'] = None
            casedict['hdlaflddly'] = None
            casedict['hdlaavgdly'] = None
            casedict['hdlamaxdly'] = None
            casedict['hdlamindly'] = None
            casedict['hlspulmta'] = None
            casedict['hlspulfmtctn'] = None
            casedict['hlspulvcdc'] = None
##            casedict['hlspulvbrte'] = None
            casedict['hlspulvfrmrte'] = None
            casedict['hlspulvres'] = None
            casedict['hlspulacdc'] = None
            casedict['hlspulabrte'] = None
            casedict['hlspulasplrte'] = None
            casedict['hlspulachn'] = None
            casedict['hlspulvfld'] = None
            casedict['hlspulafld'] = None
            casedict['hlspulsptrlt'] = None
            casedict['hlsmtarlt'] = None
            casedict['hlsfmtctnrlt'] = None
            casedict['hlsvcdcrlt'] = None
##            casedict['hlsvbrterlt'] = None
            casedict['hlsvfrmrterlt'] = None
            casedict['hlsvresrlt'] = None
            casedict['hlsacdcrlt'] = None
            casedict['hlsabrterlt'] = None
            casedict['hlsasplrterlt'] = None
            casedict['hlsachnrlt'] = None
            casedict['hlsvflddly'] = None
            casedict['hlsaflddly'] = None
            del casenamelist
            continue
        del casenamelist
        if casedict['casename'] is not None:
            rtmppuhsptlist = re.findall(r'^\s*rtmppushsupport\s*:\s*(false)(?!\S).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhsptlist) != 0:
                casedict['rtmppuhspt'] = False
                del rtmppuhsptlist
                continue
            del rtmppuhsptlist
            rtmppuhurllist = re.findall(r'^\s*rtmppushurl\s*:\s*(rtmp://[a-z0-9A-Z.:/?=&-_]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhurllist) != 0:
                casedict['rtmppuhurl'] = rtmppuhurllist[0]
                del rtmppuhurllist
                continue
            del rtmppuhurllist
            rtmppulsptlist = re.findall(r'^\s*rtmppullsupport\s*:\s*(false)(?!\S).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppulsptlist) != 0:
                casedict['rtmppulspt'] = False
                del rtmppulsptlist
                continue
            del rtmppulsptlist
            rtmppulurllist = re.findall(r'^\s*rtmppullurl\s*:\s*(rtmp://[a-z0-9A-Z.:/?=&-_]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppulurllist) != 0:
                casedict['rtmppulurl'] = rtmppulurllist[0]
                del rtmppulurllist
                continue
            del rtmppulurllist
            hdlpulsptlist = re.findall(r'^\s*hdlpullsupport\s*:\s*(false)(?!\S).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(hdlpulsptlist) != 0:
                casedict['hdlpulspt'] = False
                del hdlpulsptlist
                continue
            del hdlpulsptlist
            hdlpulurllist = re.findall(r'^\s*hdlpullurl\s*:\s*(http://[a-z0-9A-Z.:/?=&-_]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(hdlpulurllist) != 0:
                casedict['hdlpulurl'] = hdlpulurllist[0]
                del hdlpulurllist
                continue
            del hdlpulurllist
            hlspulsptlist = re.findall(r'^\s*hlspullsupport\s*:\s*(false)(?!\S).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(hlspulsptlist) != 0:
                casedict['hlspulspt'] = False
                del hlspulsptlist
                continue
            del hlspulsptlist
            hlspulurllist = re.findall(r'^\s*hlspullurl\s*:\s*(http://[a-z0-9A-Z.:/?=&-_]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(hlspulurllist) != 0:
                casedict['hlspulurl'] = hlspulurllist[0]
                del hlspulurllist
                continue
            del hlspulurllist
            rtmppuhfmtctnlist = re.findall(r'^\s*formatcontainer\s*:\s*(flv)(?!\S).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhfmtctnlist) != 0:
                casedict['rtmppuhfmtctn'] = rtmppuhfmtctnlist[0].lower()
                del rtmppuhfmtctnlist
                continue
            del rtmppuhfmtctnlist
            rtmppuhvcdclist = re.findall(r'^\s*videocodec\s*:\s*(libx264|libx263)(?!\S).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhvcdclist) != 0:
                casedict['rtmppuhvcdc'] = rtmppuhvcdclist[0].lower()
                del rtmppuhvcdclist
                continue
            del rtmppuhvcdclist
            rtmppuhvbrtelist = re.findall(r'^\s*videiobitrate\s*:\s*(\d+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhvbrtelist) != 0:
                casedict['rtmppuhvbrte'] = rtmppuhvbrtelist[0]
                del rtmppuhvbrtelist
                continue
            del rtmppuhvbrtelist
            rtmppuhvfrmrtelist = re.findall(r'^\s*videoframerate\s*:\s*(\d+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhvfrmrtelist) != 0:
                casedict['rtmppuhvfrmrte'] = rtmppuhvfrmrtelist[0]
                del rtmppuhvfrmrtelist
                continue
            del rtmppuhvfrmrtelist
            rtmppuhvreslist = re.findall(r'^\s*videoresolution\s*:\s*(\d+x\d+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhvreslist) != 0:
                casedict['rtmppuhvres'] = rtmppuhvreslist[0].lower()
                del rtmppuhvreslist
                continue
            del rtmppuhvreslist
            rtmppuhacdclist = re.findall(r'^\s*audiocodec\s*:\s*(aac|libmp3lame)(?!\S).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhacdclist) != 0:
                casedict['rtmppuhacdc'] = rtmppuhacdclist[0].lower()
                del rtmppuhacdclist
                continue
            del rtmppuhacdclist
            rtmppuhabrtelist = re.findall(r'^\s*audiobitrate\s*:\s*(\d+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhabrtelist) != 0:
                casedict['rtmppuhabrte'] = rtmppuhabrtelist[0]
                del rtmppuhabrtelist
                continue
            del rtmppuhabrtelist
            rtmppuhasplrtelist = re.findall(r'^\s*audiosamplerate\s*:\s*(\d+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhasplrtelist) != 0:
                casedict['rtmppuhasplrte'] = rtmppuhasplrtelist[0]
                del rtmppuhasplrtelist
                continue
            del rtmppuhasplrtelist
            rtmppuhachnlist = re.findall(r'^\s*audiosamplerate\s*:\s*(2).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppuhachnlist) != 0:
                casedict['rtmppuhachn'] = rtmppuhachnlist[0]
                del rtmppuhachnlist
                continue
            del rtmppuhachnlist

    exitreq = urllib2.Request(''.join(['http://', pullservip, ':', pullservport, '/exit']), headers = talkhead)
    for i in range(0, 7):
        try:
            urllib2.urlopen(exitreq, timeout = 17)
            break
        except:
            time.sleep(7)
            continue

    casefile.close()
    logfile.close()

if __name__ == '__main__':
    main()
