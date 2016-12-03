#-*- coding: utf-8 -*-
#!/usr/bin/env python

import random, uuid, sys, collections, Queue, urllib2, json, time, re, os, socket, BaseHTTPServer, md5, zlib, threading, subprocess




#server class
class server(BaseHTTPServer.HTTPServer):
    def __init__(self, talkpair, pullserverlanip, pullserverwanip, timegap, casedict, jobqueue, logqueue, *args):
        self.allow_reuse_address = False
        try:
            BaseHTTPServer.HTTPServer.__init__(self, *args)
        except:
            self.server_close()
            raise
        self.nowcase = None
        self.pullserverun = True
        self.talkpair = talkpair
        self.pullserverlanip = pullserverlanip
        self.pullserverwanip = pullserverwanip
        self.timegap = timegap
        self.casedict = casedict
        self.jobqueue = jobqueue
        self.logqueue = logqueue

    def start(self):
        while self.pullserverun:
            self.handle_request()




#handle class
class handle(BaseHTTPServer.BaseHTTPRequestHandler):
    #覆盖BaseHTTPServer.BaseHTTPRequestHandler.log_request，缩减输出
    def log_request(self, *args):
        pass

    def do_GET(self):
        #对时time
        if self.path == '/time' and self.headers.get('talkpair') == self.server.talkpair:
            try:
                self.send_response(200)
                self.send_header('talkpair', self.server.talkpair)
                self.send_header('pullserverlanip', self.server.pullserverlanip)
                if self.server.pullserverwanip != '':
                    self.send_header('pullserverwanip', self.server.pullserverwanip)
                self.send_header('nowtime', time.time())
                self.send_header('timegap', self.server.timegap)
                self.end_headers()
            except Exception as e:
                print e, '#/time返回' #debug
                pass

        #下发job
        elif self.path == '/job' and self.headers.get('talkpair') == self.server.talkpair and self.server.casedict.has_key(self.headers.get('casename')):
            print '[job]', self.headers.get('casename') #debug
            if self.headers.get('casename') != self.server.nowcase:
                if self.server.nowcase is not None:
                    del self.server.casedict[self.server.nowcase]
                self.server.nowcase = self.headers.get('casename')

                while not self.server.jobqueue.empty():
                    try:
                        self.server.jobqueue.get(block = True, timeout = 0.7)
                    except:
                        continue

                rtmppuldict = collections.OrderedDict()
                rtmppuldict['pulrun'] = True
                rtmppuldict['casename'] = self.server.nowcase
                rtmppuldict['pulprt'] = 'rtmppul'
                rtmppuldict['pulurl'] = self.server.casedict[self.server.nowcase]['rtmppulurl']
                self.server.jobqueue.put(rtmppuldict.copy(), block = True)
                del rtmppuldict

                hdlpuldict = collections.OrderedDict()
                hdlpuldict['pulrun'] = True
                hdlpuldict['casename'] = self.server.nowcase
                hdlpuldict['pulprt'] = 'hdlpul'
                hdlpuldict['pulurl'] = self.server.casedict[self.server.nowcase]['hdlpulurl']
                self.server.jobqueue.put(hdlpuldict.copy(), block = True)
                del hdlpuldict

                hlspuldict = collections.OrderedDict()
                hlspuldict['pulrun'] = True
                hlspuldict['casename'] = self.server.nowcase
                hlspuldict['pulprt'] = 'hlspul'
                hlspuldict['pulurl'] = self.server.casedict[self.server.nowcase]['hlspulurl']
                self.server.jobqueue.put(hlspuldict.copy(), block = True)
                del hlspuldict

            try:
                self.send_response(200)
                self.send_header('talkpair', self.server.talkpair)
                self.send_header('casename', self.server.nowcase)
                self.end_headers()
                self.wfile.write('job receive')
            except Exception as e:
                print e, '@/job返回' #debug
                pass

        #回收log
        elif self.path == '/log' and self.headers.get('talkpair') == self.server.talkpair and self.server.nowcase is not None and self.headers.get('casename') == self.server.nowcase:
            print '[log]', self.server.nowcase #debug
            stoppuldict = collections.OrderedDict()
            stoppuldict['pulrun'] = False
            stoppuldict['casename'] = self.server.nowcase
            for i in range(0, 3):
                self.server.jobqueue.put(stoppuldict.copy(), block = True)
            del stoppuldict

            while not self.server.logqueue.empty():
                try:
                    pullogdict = self.server.logqueue.get(block = True, timeout = 0.7)
                except:
                    continue

                if pullogdict['casename'] == self.server.nowcase:
                    if pullogdict['pulprt'] == 'rtmppul':
                        if self.server.casedict[self.server.nowcase]['rtmppulmta'] is None and pullogdict['pulmta'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulmta'] = pullogdict['pulmta']
                        if self.server.casedict[self.server.nowcase]['rtmppulfmtctn'] is None and pullogdict['pulfmtctn'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulfmtctn'] = pullogdict['pulfmtctn']
                        if self.server.casedict[self.server.nowcase]['rtmppulvcdc'] is None and pullogdict['pulvcdc'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulvcdc'] = pullogdict['pulvcdc']
                        if self.server.casedict[self.server.nowcase]['rtmppulvbrte'] is None and pullogdict['pulvbrte'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulvbrte'] = pullogdict['pulvbrte']
                        if self.server.casedict[self.server.nowcase]['rtmppulvfrmrte'] is None and pullogdict['pulvfrmrte'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulvfrmrte'] = pullogdict['pulvfrmrte']
                        if self.server.casedict[self.server.nowcase]['rtmppulvres'] is None and pullogdict['pulvres'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulvres'] = pullogdict['pulvres']
                        if self.server.casedict[self.server.nowcase]['rtmppulacdc'] is None and pullogdict['pulacdc'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulacdc'] = pullogdict['pulacdc']
                        if self.server.casedict[self.server.nowcase]['rtmppulabrte'] is None and pullogdict['pulabrte'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulabrte'] = pullogdict['pulabrte']
                        if self.server.casedict[self.server.nowcase]['rtmppulasplrte'] is None and pullogdict['pulasplrte'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulasplrte'] = pullogdict['pulasplrte']
                        if self.server.casedict[self.server.nowcase]['rtmppulachn'] is None and pullogdict['pulachn'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulachn'] = pullogdict['pulachn']
                        if self.server.casedict[self.server.nowcase]['rtmppulvfld'] is None and pullogdict['pulvfld'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulvfld'] = pullogdict['pulvfld']
                        if self.server.casedict[self.server.nowcase]['rtmppulafld'] is None and pullogdict['pulafld'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulafld'] = pullogdict['pulafld']
                        if self.server.casedict[self.server.nowcase]['rtmppulvlog'] is None and pullogdict['pulvlog'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulvlog'] = pullogdict['pulvlog']
                        if self.server.casedict[self.server.nowcase]['rtmppulalog'] is None and pullogdict['pulalog'] is not None:
                            self.server.casedict[self.server.nowcase]['rtmppulalog'] = pullogdict['pulalog']

                    elif pullogdict['pulprt'] == 'hdlpul':
                        if self.server.casedict[self.server.nowcase]['hdlpulmta'] is None and pullogdict['pulmta'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulmta'] = pullogdict['pulmta']
                        if self.server.casedict[self.server.nowcase]['hdlpulfmtctn'] is None and pullogdict['pulfmtctn'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulfmtctn'] = pullogdict['pulfmtctn']
                        if self.server.casedict[self.server.nowcase]['hdlpulvcdc'] is None and pullogdict['pulvcdc'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulvcdc'] = pullogdict['pulvcdc']
                        if self.server.casedict[self.server.nowcase]['hdlpulvbrte'] is None and pullogdict['pulvbrte'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulvbrte'] = pullogdict['pulvbrte']
                        if self.server.casedict[self.server.nowcase]['hdlpulvfrmrte'] is None and pullogdict['pulvfrmrte'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulvfrmrte'] = pullogdict['pulvfrmrte']
                        if self.server.casedict[self.server.nowcase]['hdlpulvres'] is None and pullogdict['pulvres'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulvres'] = pullogdict['pulvres']
                        if self.server.casedict[self.server.nowcase]['hdlpulacdc'] is None and pullogdict['pulacdc'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulacdc'] = pullogdict['pulacdc']
                        if self.server.casedict[self.server.nowcase]['hdlpulabrte'] is None and pullogdict['pulabrte'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulabrte'] = pullogdict['pulabrte']
                        if self.server.casedict[self.server.nowcase]['hdlpulasplrte'] is None and pullogdict['pulasplrte'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulasplrte'] = pullogdict['pulasplrte']
                        if self.server.casedict[self.server.nowcase]['hdlpulachn'] is None and pullogdict['pulachn'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulachn'] = pullogdict['pulachn']
                        if self.server.casedict[self.server.nowcase]['hdlpulvfld'] is None and pullogdict['pulvfld'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulvfld'] = pullogdict['pulvfld']
                        if self.server.casedict[self.server.nowcase]['hdlpulafld'] is None and pullogdict['pulafld'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulafld'] = pullogdict['pulafld']
                        if self.server.casedict[self.server.nowcase]['hdlpulvlog'] is None and pullogdict['pulvlog'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulvlog'] = pullogdict['pulvlog']
                        if self.server.casedict[self.server.nowcase]['hdlpulalog'] is None and pullogdict['pulalog'] is not None:
                            self.server.casedict[self.server.nowcase]['hdlpulalog'] = pullogdict['pulalog']

                    elif pullogdict['pulprt'] == 'hlspul':
                        if self.server.casedict[self.server.nowcase]['hlspulmta'] is None and pullogdict['pulmta'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulmta'] = pullogdict['pulmta']
                        if self.server.casedict[self.server.nowcase]['hlspulfmtctn'] is None and pullogdict['pulfmtctn'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulfmtctn'] = pullogdict['pulfmtctn']
                        if self.server.casedict[self.server.nowcase]['hlspulvcdc'] is None and pullogdict['pulvcdc'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulvcdc'] = pullogdict['pulvcdc']
##                        if self.server.casedict[self.server.nowcase]['hlspulvbrte'] is None and pullogdict['pulvbrte'] is not None:
##                            self.server.casedict[self.server.nowcase]['hlspulvbrte'] = pullogdict['pulvbrte']
                        if self.server.casedict[self.server.nowcase]['hlspulvfrmrte'] is None and pullogdict['pulvfrmrte'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulvfrmrte'] = pullogdict['pulvfrmrte']
                        if self.server.casedict[self.server.nowcase]['hlspulvres'] is None and pullogdict['pulvres'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulvres'] = pullogdict['pulvres']
                        if self.server.casedict[self.server.nowcase]['hlspulacdc'] is None and pullogdict['pulacdc'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulacdc'] = pullogdict['pulacdc']
                        if self.server.casedict[self.server.nowcase]['hlspulabrte'] is None and pullogdict['pulabrte'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulabrte'] = pullogdict['pulabrte']
                        if self.server.casedict[self.server.nowcase]['hlspulasplrte'] is None and pullogdict['pulasplrte'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulasplrte'] = pullogdict['pulasplrte']
                        if self.server.casedict[self.server.nowcase]['hlspulachn'] is None and pullogdict['pulachn'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulachn'] = pullogdict['pulachn']
                        if self.server.casedict[self.server.nowcase]['hlspulvfld'] is None and pullogdict['pulvfld'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulvfld'] = pullogdict['pulvfld']
                        if self.server.casedict[self.server.nowcase]['hlspulafld'] is None and pullogdict['pulafld'] is not None:
                            self.server.casedict[self.server.nowcase]['hlspulafld'] = pullogdict['pulafld']
                del pullogdict

            try:
                pullogtext = json.dumps(self.server.casedict[self.server.nowcase])
            except Exception as e:
                print e, '@反序列化log' #debug
                return
##            print md5.md5(pullogtext).hexdigest(), '@md5 logdict json' #tmp debug
            try:
                pullogzip = zlib.compress(pullogtext, 9)
            except Exception as e:
                print e, '@压缩log' #debug
                return
            try:
                self.send_response(200)
                self.send_header('talkpair', self.server.talkpair)
                self.send_header('casename', self.server.nowcase)
                self.send_header('logmd5', md5.md5(pullogtext).hexdigest())
                self.end_headers()
                self.wfile.write(pullogzip)
            except Exception as e:
                print e, '@/log返回' #debug
                pass

        #获取pull url
        elif self.path == '/play' and self.headers.get('talkpair') == self.server.talkpair:
            try:
                self.send_response(200)
                self.send_header('talkpair', self.server.talkpair)
                if self.server.nowcase is not None:
                    self.send_header('casename', self.server.nowcase)
                    self.send_header('rtmppul', self.server.casedict[self.server.nowcase]['rtmppulurl'])
                    self.send_header('hdlpul', self.server.casedict[self.server.nowcase]['hdlpulurl'])
                    self.send_header('hlspul', self.server.casedict[self.server.nowcase]['hlspulurl'])
                self.end_headers()
            except Exception as e:
                print e, '@/pull返回' #debug
                pass

        #退出exit
        elif self.path == '/exit' and self.headers.get('talkpair') == self.server.talkpair:
            try:
                self.send_response(200)
                self.send_header('talkpair', self.server.talkpair)
                self.end_headers()
            except Exception as e:
                print e, '@/exit返回' #debug
            finally:
                self.server.pullserverun = False





#拉流线程
class pull(threading.Thread):
    def __init__(self, jobqueue, logqueue, timegap):
        threading.Thread.__init__(self)
        self.pulthrdrun = True
        self.jobqueue = jobqueue
        self.logqueue = logqueue
        self.timegap = timegap

    def run(self):
        osname = os.name
        while self.pulthrdrun:
            try:
                puljob = self.jobqueue.get_nowait()
            except:
                continue
            if puljob['pulrun']:
                if puljob['pulprt'] == 'rtmppul':
##                    print 'start rtmppul', puljob['casename'] #tmp debug
                    self.rtmp(osname, puljob['casename'], puljob['pulurl'])
##                    print 'stop rtmppul', puljob['casename'] #tmp debug
                elif puljob['pulprt'] == 'hdlpul':
##                    print 'start hdlpul', puljob['casename'] #tmp debug
                    self.hdl(osname, puljob['casename'], puljob['pulurl'])
##                    print 'stop hdlpul', puljob['casename'] #tmp debug
                elif puljob['pulprt'] == 'hlspul':
##                    print 'start hlspul', puljob['casename'] #tmp debug
                    self.hls(osname, puljob['casename'], puljob['pulurl'])
##                    print 'stop hlspul', puljob['casename'] #tmp debug
            else:
                self.jobqueue.put(puljob.copy(), block = True)
            del puljob

    def rtmp(self, osname, casename, pulurl):
        if osname == 'posix':
            ffprobe = './ffmpeg/ffprobe -hide_banner -show_entries frame=media_type,key_frame,pkt_pts -i'
        elif osname == 'nt':
            ffprobe = 'ffmpeg\\ffprobe.exe -hide_banner -loglevel verbose -show_entries frame=media_type,key_frame,pkt_pts -i'
        logdict = collections.OrderedDict()
        logdict['casename'] = casename
        logdict['pulprt'] = 'rtmppul'
        logdict['pulmta'] = collections.OrderedDict()
        logdict['pulfmtctn'] = None
        logdict['pulvcdc'] = None
        logdict['pulvbrte'] = None
        logdict['pulvfrmrte'] = None
        logdict['pulvres'] = None
        logdict['pulacdc'] = None
        logdict['pulabrte'] = None
        logdict['pulasplrte'] = None
        logdict['pulachn'] = None
        logdict['pulvfld'] = None
        logdict['pulafld'] = None
        logdict['pulvlog'] = collections.OrderedDict()
        logdict['pulalog'] = collections.OrderedDict()

        frmtflag = True
        metaflag = False
        duraflag = False
        vparaflag = True
        aparaflag = True
        vfldflag = True
        afldflag = True
        vflag = False
        aflag = False
        kflag = False
        proc = subprocess.Popen(' '.join([ffprobe, pulurl]), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True)
        while True:
            if not self.pulthrdrun:
                if osname == 'posix' and proc.poll() is None:
                    proc.kill()
                    proc.wait()
                elif osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0:
                    subprocess.call(' '.join(['taskkill.exe /f /t /pid', str(proc.pid), '2>&1>nul']), shell = True)
                    proc.wait()
                del proc
                self.log(logdict)
                break

            try:
                job = self.jobqueue.get_nowait()
                if job['casename'] == casename and not job['pulrun']:
                    if osname == 'posix' and proc.poll() is None:
                        proc.kill()
                        proc.wait()
                    elif osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0:
                        subprocess.call(' '.join(['taskkill.exe /f /t /pid', str(proc.pid), '2>&1>nul']), shell = True)
                        proc.wait()
                    del proc
                    self.log(logdict)
                    break
                else:
                    self.jobqueue.put(job.copy(), block = True)
##                    del job
            except Queue.Empty:
                pass
            except Exception as e:
                print e, '@rtmp线程' #debug
                pass

            if (osname == 'posix' and proc.poll() is not None) or (osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) != 0):
##                del proc
                proc = subprocess.Popen(' '.join([ffprobe, pulurl]), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True)
                vflag = False
                aflag = False
                kflag = False

            if (osname == 'posix' and proc.poll() is None) or (osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0):
                line = proc.stdout.readline()
                if frmtflag:
                    fmtctnlist = re.findall(r'^Input #0, (\S+), from \'' + pulurl + '\':\n$', line)
                    if len(fmtctnlist) != 0:
                        frmtflag = False
                        logdict['pulfmtctn'] = fmtctnlist[0]
##                        del fmtctnlist
                        continue
##                    del fmtctnlist
                if not duraflag:
                    if not metaflag and len(re.findall(r'^  Metadata:\n$', line)) != 0:
                        metaflag = True
                        continue
                    if len(re.findall(r'^  Duration: 00:00:00.00|N/A, start: \d+.\d\d\d\d\d\d, bitrate: N/A|[\d.]+ [kmg]{0,1}b/s\n$', line)) != 0:
                        duraflag = True
                        continue
                    if metaflag:
                        pulmtalist = re.findall(r'^\s*(.+):\s*(.*)\n$', line)
                        if len(pulmtalist) != 0:
                            logdict['pulmta'][pulmtalist[0][0].rstrip()] = pulmtalist[0][1].rstrip()
##                            del pulmtalist
                            continue
##                        del pulmtalist
                if vparaflag:
                    #posix -loglevel info -vcodec libx264
                    vparalist = re.findall(r'^    Stream #0:[01]: Video: (\S+)[^,]*, \S+, (\d+x\d+)[^,]*, ([\d.]+ [kmg]{0,1})b/s, ([\d.]+) fps, [\d.]+[kmg]{0,1} tbr, [\d.]+[kmg]{0,1} tbn, [\d.]+[kmg]{0,1} tbc\n$', line)
                    if len(vparalist) != 0:
                        vparaflag = False
                        logdict['pulvcdc'] = vparalist[0][0]
                        logdict['pulvbrte'] = vparalist[0][2]
                        logdict['pulvfrmrte'] = vparalist[0][3]
                        logdict['pulvres'] = vparalist[0][1]
##                        del vparalist
                        continue
##                    del vparalist
                    #nt -loglevel verbose -vcodec libx264
                    vparalist = re.findall(r'^    Stream #0:[01]: Video: (\S+)[^,]*, [^,]*, \S+, (\d+x\d+)[^,]*, ([\d.]+) fps, [\d.]+[kmg]{0,1} tbr, [\d.]+[kmg]{0,1} tbn, [\d.]+[kmg]{0,1} tbc\n$', line)
                    if len(vparalist) != 0:
                        vparaflag = False
                        logdict['pulvcdc'] = vparalist[0][0]
##                        logdict['pulvbrte'] = vparalist[0][3]
                        logdict['pulvfrmrte'] = vparalist[0][2]
                        logdict['pulvres'] = vparalist[0][1]
##                        del vparalist
                        continue
##                    del vparalist
                if aparaflag:
                    #posix -loglevel info -acodec aac
                    aparalist = re.findall(r'^    Stream #0:[01]: Audio: (\S+)[^,]*, ([\d.]+) Hz, (\S+), \S+, ([\d.]+ [kmg]{0,1})b/s\n$', line)
                    if len(aparalist) != 0:
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
                        logdict['pulabrte'] = aparalist[0][3]
                        logdict['pulasplrte'] = aparalist[0][1]
                        logdict['pulachn'] = aparalist[0][2]
##                        del aparalist
                        continue
##                    del aparalist
                    #nt -loglevel verbose -acodec aac|libmp3lame
                    aparalist = re.findall(r'^    Stream #0:[01]: Audio: (\S+)[^,]*, ([\d.]+) Hz, (\S+), \S+\n$', line)
                    if len(aparalist) != 0:
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
##                        logdict['pulabrte'] = aparalist[0][3]
                        logdict['pulasplrte'] = aparalist[0][1]
                        logdict['pulachn'] = aparalist[0][2]
##                        del aparalist
                        continue
##                    del aparalist
                    #nt -loglevel verbose -acodec libmp3lame
                    aparalist = re.findall(r'^    Stream #0:[01]: Audio: (\S+)[^,]*, ([\d.]+) Hz, (\S+), \S+, ([\d.]+ [kmg]{0,1})b/s\n$', line)
                    if len(aparalist) != 0:
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
                        logdict['pulabrte'] = aparalist[0][3]
                        logdict['pulasplrte'] = aparalist[0][1]
                        logdict['pulachn'] = aparalist[0][2]
##                        del aparalist
                        continue
##                    del aparalist
                if line == 'media_type=video\n':
                    if osname == 'posix':
                        frmtflag = False
                        duraflag = True
                        vparaflag = False
                        aparaflag = False
                    vflag = True
                    aflag = False
                    kflag = False
                    continue
                if line == 'media_type=audio\n':
                    if osname == 'posix':
                        frmtflag = False
                        duraflag = True
                        vparaflag = False
                        aparaflag = False
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
                            logdict['pulvfld'] = time.time() + self.timegap
                        logdict['pulvlog'][line.rstrip().split('=')[1]] = time.time() + self.timegap
                        vflag = False
                        aflag = False
                        kflag = False
                        continue
                    if aflag:
                        if afldflag:
                            afldflag = False
                            logdict['pulafld'] = time.time() + self.timegap
                        logdict['pulalog'][line.rstrip().split('=')[1]] = time.time() + self.timegap
                        vflag = False
                        aflag = False
                        kflag = False
                        continue

    def hdl(self, osname, casename, pulurl):
        if osname == 'posix':
            ffprobe = './ffmpeg/ffprobe -hide_banner -timeout 7000000 -show_entries frame=media_type,key_frame,pkt_pts -i'
        elif osname == 'nt':
            ffprobe = 'ffmpeg\\ffprobe.exe -hide_banner -loglevel debug -timeout 7000000 -show_entries frame=media_type,key_frame,pkt_pts -i'
        logdict = collections.OrderedDict()
        logdict['casename'] = casename
        logdict['pulprt'] = 'hdlpul'
        logdict['pulmta'] = collections.OrderedDict()
        logdict['pulfmtctn'] = None
        logdict['pulvcdc'] = None
        logdict['pulvbrte'] = None
        logdict['pulvfrmrte'] = None
        logdict['pulvres'] = None
        logdict['pulacdc'] = None
        logdict['pulabrte'] = None
        logdict['pulasplrte'] = None
        logdict['pulachn'] = None
        logdict['pulvfld'] = None
        logdict['pulafld'] = None
        logdict['pulvlog'] = collections.OrderedDict()
        logdict['pulalog'] = collections.OrderedDict()

        frmtflag = True
        metaflag = False
        duraflag = False
        vparaflag = True
        aparaflag = True
        vfldflag = True
        afldflag = True
        vflag = False
        aflag = False
        kflag = False
        proc = subprocess.Popen(' '.join([ffprobe, pulurl]), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True)
        while True:
            if not self.pulthrdrun:
                if osname == 'posix' and proc.poll() is None:
                    proc.kill()
                    proc.wait()
                elif osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0:
                    subprocess.call(' '.join(['taskkill.exe /f /t /pid', str(proc.pid), '2>&1>nul']), shell = True)
                    proc.wait()
                del proc
                self.log(logdict)
                break

            try:
                job = self.jobqueue.get_nowait()
                if job['casename'] == casename and not job['pulrun']:
                    if osname == 'posix' and proc.poll() is None:
                        proc.kill()
                        proc.wait()
                    elif osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0:
                        subprocess.call(' '.join(['taskkill.exe /f /t /pid', str(proc.pid), '2>&1>nul']), shell = True)
                        proc.wait()
                    del proc
                    self.log(logdict)
                    break
                else:
                    self.jobqueue.put(job.copy(), block = True)
##                    del job
            except Queue.Empty:
                pass
            except Exception as e:
                print e, '@hdl线程' #debug
                pass

            if (osname == 'posix' and proc.poll() is not None) or (osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) != 0):
##                del proc
                proc = subprocess.Popen(' '.join([ffprobe, pulurl]), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True)
                vflag = False
                aflag = False
                kflag = False

            if (osname == 'posix' and proc.poll() is None) or (osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0):
                line = proc.stdout.readline()
                if frmtflag:
                    fmtctnlist = re.findall(r'^Input #0, (\S+), from \'' + pulurl + '\':\n$', line)
                    if len(fmtctnlist) != 0:
                        frmtflag = False
                        logdict['pulfmtctn'] = fmtctnlist[0]
##                        del fmtctnlist
                        continue
##                    del fmtctnlist
                if not duraflag:
                    if not metaflag and len(re.findall(r'^  Metadata:\n$', line)) != 0:
                        metaflag = True
                        continue
                    if len(re.findall(r'^  Duration: 00:00:00.00|N/A, start: \d+.\d\d\d\d\d\d, bitrate: N/A|[\d.]+ [kmg]{0,1}b/s\n$', line)) != 0:
                        duraflag = True
                        continue
                    if metaflag:
                        pulmtalist = re.findall(r'^\s*(.+):\s*(.*)\n$', line)
                        if len(pulmtalist) != 0:
                            logdict['pulmta'][pulmtalist[0][0].rstrip()] = pulmtalist[0][1].rstrip()
##                            del pulmtalist
                            continue
##                        del pulmtalist
                if vparaflag:
                    #posix -loglevel info -vcodec libx264
                    vparalist = re.findall(r'^    Stream #0:[01]: Video: (\S+)[^,]*, \S+, (\d+x\d+)[^,]*, ([\d.]+ [kmg]{0,1})b/s, ([\d.]+) fps, [\d.]+[kmg]{0,1} tbr, [\d.]+[kmg]{0,1} tbn, [\d.]+[kmg]{0,1} tbc\n$', line)
                    if len(vparalist) != 0:
                        vparaflag = False
                        logdict['pulvcdc'] = vparalist[0][0]
                        logdict['pulvbrte'] = vparalist[0][2]
                        logdict['pulvfrmrte'] = vparalist[0][3]
                        logdict['pulvres'] = vparalist[0][1]
##                        del vparalist
                        continue
##                    del vparalist
                    #nt -loglevel debug -vcodec libx264
                    vparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Video: (\S+)[^,]*, [^,]*, \S+, (\d+x\d+)[^,]*, [\d/]+, ([\d.]+) fps, [\d.]+[kmg]{0,1} tbr, [\d.]+[kmg]{0,1} tbn, [\d.]+[kmg]{0,1} tbc\n$', line)
                    if len(vparalist) != 0:
                        vparaflag = False
                        logdict['pulvcdc'] = vparalist[0][0]
##                        logdict['pulvbrte'] = vparalist[0][3]
                        logdict['pulvfrmrte'] = vparalist[0][2]
                        logdict['pulvres'] = vparalist[0][1]
##                        del vparalist
                        continue
##                    del vparalist
                if aparaflag:
                    #posix -loglevel info -acodec aac|libmp3lame
                    aparalist = re.findall(r'^    Stream #0:[01]: Audio: (\S+)[^,]*, ([\d.]+) Hz, (\S+), \S+, ([\d.]+ [kmg]{0,1})b/s\n$', line)
                    if len(aparalist) != 0:
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
                        logdict['pulabrte'] = aparalist[0][3]
                        logdict['pulasplrte'] = aparalist[0][1]
                        logdict['pulachn'] = aparalist[0][2]
##                        del aparalist
                        continue
##                    del aparalist
                    #nt -loglevel debug -acodec aac
                    aparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Audio: (\S+)[^,]*, ([\d.]+) Hz, (\S+), \S+\n$', line)
                    if len(aparalist) != 0:
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
##                        logdict['pulabrte'] = aparalist[0][3]
                        logdict['pulasplrte'] = aparalist[0][1]
                        logdict['pulachn'] = aparalist[0][2]
##                        del aparalist
                        continue
##                    del aparalist
                    #nt -loglevel debug -acodec libmp3lame
                    aparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Audio: (\S+)[^,]*, ([\d.]+) Hz, (\S+), \S+, ([\d.]+ [kmg]{0,1})b/s\n$', line)
                    if len(aparalist) != 0:
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
##                        logdict['pulabrte'] = aparalist[0][3]
                        logdict['pulasplrte'] = aparalist[0][1]
                        logdict['pulachn'] = aparalist[0][2]
##                        del aparalist
                        continue
##                    del aparalist
                if line == 'media_type=video\n':
                    if osname == 'posix':
                        frmtflag = False
                        duraflag = True
                        vparaflag = False
                        aparaflag = False
                    vflag = True
                    aflag = False
                    kflag = False
                    continue
                if line == 'media_type=audio\n':
                    if osname == 'posix':
                        frmtflag = False
                        duraflag = True
                        vparaflag = False
                        aparaflag = False
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
                            logdict['pulvfld'] = time.time() + self.timegap
                        logdict['pulvlog'][line.rstrip().split('=')[1]] = time.time() + self.timegap
                        vflag = False
                        aflag = False
                        kflag = False
                        continue
                    if aflag:
                        if afldflag:
                            afldflag = False
                            logdict['pulafld'] = time.time() + self.timegap
                        logdict['pulalog'][line.rstrip().split('=')[1]] = time.time() + self.timegap
                        vflag = False
                        aflag = False
                        kflag = False
                        continue

    def hls(self, osname, casename, pulurl):
        if osname == 'posix':
            ffprobe = './ffmpeg/ffprobe -hide_banner -loglevel debug -timeout 7000000 -show_entries frame=media_type,key_frame,pkt_pts -i'
        elif osname == 'nt':
            ffprobe = 'ffmpeg\\ffprobe.exe -hide_banner -loglevel debug -timeout 7000000 -show_entries frame=media_type,key_frame,pkt_pts -i'
        logdict = collections.OrderedDict()
        logdict['casename'] = casename
        logdict['pulmta'] = collections.OrderedDict()
        logdict['pulprt'] = 'hlspul'
        logdict['pulfmtctn'] = None
        logdict['pulvcdc'] = None
##        logdict['pulvbrte'] = None
        logdict['pulvfrmrte'] = None
        logdict['pulvres'] = None
        logdict['pulacdc'] = None
        logdict['pulabrte'] = None
        logdict['pulasplrte'] = None
        logdict['pulachn'] = None
        logdict['pulvfld'] = None
        logdict['pulafld'] = None

        frmtflag = True
        metaflag = False
        duraflag = False
        vparaflag = True
        aparaflag = True
        vfldflag = True
        afldflag = True
        vflag = False
        aflag = False
        kflag = False
        proc = subprocess.Popen(' '.join([ffprobe, pulurl]), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True)
        while True:
            if (not frmtflag and duraflag and not vparaflag and not aparaflag and not vfldflag and not afldflag) or not self.pulthrdrun:
                if osname == 'posix' and proc.poll() is None:
                    proc.kill()
                    proc.wait()
                elif osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0:
                    subprocess.call(' '.join(['taskkill.exe /f /t /pid', str(proc.pid), '2>&1>nul']), shell = True)
                    proc.wait()
                del proc
                self.log(logdict)
                break

            try:
                job = self.jobqueue.get_nowait()
                if job['casename'] == casename and not job['pulrun']:
                    if osname == 'posix' and proc.poll() is None:
                        proc.kill()
                        proc.wait()
                    elif osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0:
                        subprocess.call(' '.join(['taskkill.exe /f /t /pid', str(proc.pid), '2>&1>nul']), shell = True)
                        proc.wait()
                    del proc
                    self.log(logdict)
                    break
                else:
                    self.jobqueue.put(job.copy(), block = True)
##                    del job
            except Queue.Empty:
                pass
            except Exception as e:
                print e, '@hls线程' #debug
                pass

            if (osname == 'posix' and proc.poll() is not None) or (osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) != 0):
##                del proc
                proc = subprocess.Popen(' '.join([ffprobe, pulurl]), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True)
                vflag = False
                aflag = False
                kflag = False

            if (osname == 'posix' and proc.poll() is None) or (osname == 'nt' and subprocess.call(' '.join(['tasklist.exe /fi "pid eq', str(proc.pid) + '"', '| find.exe', '"' + str(proc.pid) + '"', '2>&1>nul']), shell = True) == 0):
                line = proc.stdout.readline()
                if frmtflag:
                    fmtctnlist = re.findall(r'^Input #0, (\S+), from \'' + pulurl + '\':\n$', line)
                    if len(fmtctnlist) != 0:
                        frmtflag = False
                        logdict['pulfmtctn'] = fmtctnlist[0]
##                        del fmtctnlist
                        continue
##                    del fmtctnlist
                if not duraflag:
                    if not metaflag and len(re.findall(r'^    Metadata:\n$', line)) != 0:
                        metaflag = True
                        continue
                if vparaflag:
                    #posix -loglevel debug -vcodec libx264
                    vparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Video: (\S+)[^,]*, [^,]*, \S+, (\d+x\d+)[^,]*, [\d/]+, ([\d.]+) fps, [\d.]+[kmg]{0,1} tbr, [\d.]+[kmg]{0,1} tbn, [\d.]+[kmg]{0,1} tbc\n$', line)
                    if len(vparalist) != 0:
                        duraflag = True
                        vparaflag = False
                        logdict['pulvcdc'] = vparalist[0][0]
##                        logdict['pulvbrte'] = vparalist[0][3]
                        logdict['pulvfrmrte'] = vparalist[0][2]
                        logdict['pulvres'] = vparalist[0][1]
##                        del vparalist
                        continue
##                    del vparalist
                    #nt -loglevel debug -vcodec libx264
                    vparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Video: (\S+)[^,]*, [^,]*, \S+, (\d+x\d+)[^,]*, [\d/]+, [\d.]+[kmg]{0,1} tbr, [\d.]+[kmg]{0,1} tbn, [\d.]+[kmg]{0,1} tbc\n$', line)
                    if len(vparalist) != 0:
                        duraflag = True
                        vparaflag = False
                        logdict['pulvcdc'] = vparalist[0][0]
##                        logdict['pulvbrte'] = vparalist[0][3]
##                        logdict['pulvfrmrte'] = vparalist[0][2]
                        logdict['pulvres'] = vparalist[0][1]
##                        del vparalist
                        continue
##                    del vparalist
                    vparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Video: (\S+)[^,]*, [^,]*, \S+, ([\d.]+) fps, [\d.]+[kmg]{0,1} tbr, [\d.]+[kmg]{0,1} tbn, [\d.]+[kmg]{0,1} tbc\n$', line)
                    if len(vparalist) != 0:
                        duraflag = True
                        vparaflag = False
                        logdict['pulvcdc'] = vparalist[0][0]
##                        logdict['pulvbrte'] = vparalist[0][3]
                        logdict['pulvfrmrte'] = vparalist[0][1]
##                        logdict['pulvres'] = vparalist[0][2]
##                        del vparalist
                        continue
##                    del vparalist
                    vparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Video: (\S+)[^,]*, .*[\d.]+[kmg]{0,1} tbr, [\d.]+[kmg]{0,1} tbn, [\d.]+[kmg]{0,1} tbc\n$', line)
                    if len(vparalist) != 0:
                        duraflag = True
                        vparaflag = False
                        logdict['pulvcdc'] = vparalist[0][0]
##                        logdict['pulvbrte'] = vparalist[0][3]
##                        logdict['pulvfrmrte'] = vparalist[0][1]
##                        logdict['pulvres'] = vparalist[0][2]
##                        del vparalist
                        continue
##                    del vparalist
                if aparaflag:
                    #posix -loglevel debug -acodec aac|libmp3lame
                    aparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Audio: (\S+)[^,]*, ([\d.]+) Hz, (\S+), \S+, ([\d.]+ [kmg]{0,1})b/s\n$', line)
                    if len(aparalist) != 0:
                        duraflag = True
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
                        logdict['pulabrte'] = aparalist[0][3]
                        logdict['pulasplrte'] = aparalist[0][1]
                        logdict['pulachn'] = aparalist[0][2]
##                        del aparalist
                        continue
##                    del aparalist
                    #nt -loglevel debug -acodec aac
                    aparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Audio: (\S+)[^,]*, ([\d.]+) Hz, (\S+), \S+\n$', line)
                    if len(aparalist) != 0:
                        duraflag = True
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
##                        logdict['pulabrte'] = aparalist[0][3]
                        logdict['pulasplrte'] = aparalist[0][1]
                        logdict['pulachn'] = aparalist[0][2]
##                        del aparalist
                        continue
##                    del aparalist
                    aparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Audio: (\S+)[^,]*, (\d+) channels, \S+\n$', line)
                    if len(aparalist) != 0:
                        duraflag = True
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
##                        logdict['pulabrte'] = aparalist[0][3]
##                        logdict['pulasplrte'] = aparalist[0][2]
                        logdict['pulachn'] = aparalist[0][1]
##                        del aparalist
                        continue
##                    del aparalist
                    aparalist = re.findall(r'^    Stream #0:[01], \d+, [\d/]+: Audio: (\S+), .*\n$', line)
                    if len(aparalist) != 0:
                        duraflag = True
                        aparaflag = False
                        logdict['pulacdc'] = aparalist[0][0]
##                        logdict['pulabrte'] = aparalist[0][3]
##                        logdict['pulasplrte'] = aparalist[0][2]
##                        logdict['pulachn'] = aparalist[0][1]
##                        del aparalist
                        continue
##                    del aparalist
                if not duraflag:
                    if metaflag:
                        pulmtalist = re.findall(r'^\s*(.+):\s*(.*)\n$', line)
                        if len(pulmtalist) != 0:
                            logdict['pulmta'][pulmtalist[0][0].rstrip()] = pulmtalist[0][1].rstrip()
##                            del pulmtalist
                            continue
##                        del pulmtalist
                if line == 'media_type=video\n':
                    if osname == 'posix':
                        frmtflag = False
                        duraflag = True
                        vparaflag = False
                        aparaflag = False
                    vflag = True
                    aflag = False
                    kflag = False
                    continue
                if line == 'media_type=audio\n':
                    if osname == 'posix':
                        frmtflag = False
                        duraflag = True
                        vparaflag = False
                        aparaflag = False
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
                            logdict['pulvfld'] = time.time() + self.timegap
                        vflag = False
                        aflag = False
                        kflag = False
                        continue
                    if aflag:
                        if afldflag:
                            afldflag = False
                            logdict['pulafld'] = time.time() + self.timegap
                        vflag = False
                        aflag = False
                        kflag = False
                        continue

    def log(self, logdict):
        for k, v in logdict.iteritems():
            if type(v) is collections.OrderedDict and len(v) == 0:
                del logdict[k]
                logdict[k] = None
        self.logqueue.put(logdict.copy(), block = True)
        del logdict

    def exit(self):
        self.pulthrdrun = False




def main():
    #公共变量
    pullservport = random.randint(49152, 65535)
    talkpair = str(uuid.uuid4())
    for i in range(1, len(sys.argv) - 1):
        if sys.argv[i].lower() == '-pullserverport':
            try:
                pullservport = int(sys.argv[i + 1])
            except:
                print 'please pass -pullservport 49152-65535'
                return
        elif sys.argv[i].lower() == '-talkpair':
            talkpair = sys.argv[i + 1]
    if not 49152 <= pullservport <= 65535:
        print 'please pass -pullservport 49152-65535'
        return

    casefile = open('case/live.ini')
    casedict = collections.OrderedDict()
    casename = None
    casenamedict = collections.OrderedDict()

    jobqueue = Queue.Queue()
    logqueue = Queue.Queue()

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

    #主逻辑入口
    while True:
        line = casefile.readline()
        if line == '':
            if casename is not None:
                casedict.update(casenamedict.copy())
                del casenamedict
            break
        comoutlist = re.findall(r'^\s*#.*$', line, flags = re.DOTALL | re.IGNORECASE)
        if len(comoutlist) != 0:
            del comoutlist
            continue
        del comoutlist
        casenamelist = re.findall(r'^\s*casename\s*:\s*([^#]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
        if len(casenamelist) != 0:
            if casename is not None:
                casedict.update(casenamedict.copy())
            casename = casenamelist[0].rstrip()
            casenamedict.clear()
            casenamedict[casename] = collections.OrderedDict()
            casenamedict[casename]['rtmppulurl'] = ''
            casenamedict[casename]['hdlpulurl'] = ''
            casenamedict[casename]['hlspulurl'] = ''
            casenamedict[casename]['rtmppulmta'] = None
            casenamedict[casename]['rtmppulfmtctn'] = None
            casenamedict[casename]['rtmppulvcdc'] = None
            casenamedict[casename]['rtmppulvbrte'] = None
            casenamedict[casename]['rtmppulvfrmrte'] = None
            casenamedict[casename]['rtmppulvres'] = None
            casenamedict[casename]['rtmppulacdc'] = None
            casenamedict[casename]['rtmppulabrte'] = None
            casenamedict[casename]['rtmppulasplrte'] = None
            casenamedict[casename]['rtmppulachn'] = None
            casenamedict[casename]['rtmppulvfld'] = None
            casenamedict[casename]['rtmppulafld'] = None
            casenamedict[casename]['rtmppulvlog'] = None
            casenamedict[casename]['rtmppulalog'] = None
            casenamedict[casename]['hdlpulmta'] = None
            casenamedict[casename]['hdlpulfmtctn'] = None
            casenamedict[casename]['hdlpulvcdc'] = None
            casenamedict[casename]['hdlpulvbrte'] = None
            casenamedict[casename]['hdlpulvfrmrte'] = None
            casenamedict[casename]['hdlpulvres'] = None
            casenamedict[casename]['hdlpulacdc'] = None
            casenamedict[casename]['hdlpulabrte'] = None
            casenamedict[casename]['hdlpulasplrte'] = None
            casenamedict[casename]['hdlpulachn'] = None
            casenamedict[casename]['hdlpulvfld'] = None
            casenamedict[casename]['hdlpulafld'] = None
            casenamedict[casename]['hdlpulvlog'] = None
            casenamedict[casename]['hdlpulalog'] = None
            casenamedict[casename]['hlspulmta'] = None
            casenamedict[casename]['hlspulfmtctn'] = None
            casenamedict[casename]['hlspulvcdc'] = None
##            casenamedict[casename]['hlspulvbrte'] = None
            casenamedict[casename]['hlspulvfrmrte'] = None
            casenamedict[casename]['hlspulvres'] = None
            casenamedict[casename]['hlspulacdc'] = None
            casenamedict[casename]['hlspulabrte'] = None
            casenamedict[casename]['hlspulasplrte'] = None
            casenamedict[casename]['hlspulachn'] = None
            casenamedict[casename]['hlspulvfld'] = None
            casenamedict[casename]['hlspulafld'] = None
            del casenamelist
            continue
        del casenamelist
        if casename is not None:
            rtmppulurllist = re.findall(r'^\s*rtmppullurl\s*:\s*(rtmp://[a-z0-9A-Z.:/?=&-_]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(rtmppulurllist) != 0:
                casenamedict[casename]['rtmppulurl'] = rtmppulurllist[0]
                del rtmppulurllist
                continue
            del rtmppulurllist
            hdlpulurllist = re.findall(r'^\s*hdlpullurl\s*:\s*(http://[a-z0-9A-Z.:/?=&-_]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(hdlpulurllist) != 0:
                casenamedict[casename]['hdlpulurl'] = hdlpulurllist[0]
                del hdlpulurllist
                continue
            del hdlpulurllist
            hlspulurllist = re.findall(r'^\s*hlspullurl\s*:\s*(http://[a-z0-9A-Z.:/?=&-_]+).*$', line, flags = re.DOTALL | re.IGNORECASE)
            if len(hlspulurllist) != 0:
                casenamedict[casename]['hlspulurl'] = hlspulurllist[0]
                del hlspulurllist
                continue
            del hlspulurllist
    casefile.close()

    pullthread1 = pull(jobqueue, logqueue, timegap)
    pullthread1.start()
    pullthread2 = pull(jobqueue, logqueue, timegap)
    pullthread2.start()
    pullthread3 = pull(jobqueue, logqueue, timegap)
    pullthread3.start()

    #打印lan ip、wan ip、port、talkpair、timegap
    pullserverlanip = socket.gethostbyname(socket.gethostname())
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
    print 'LAN IP :        ', pullserverlanip
    print 'WAN IP :        ', pullserverwanip
    print 'PULLSERVERPORT :', pullservport
    print 'TALKPAIR :      ', talkpair

    try:
        pullserver = server(talkpair, pullserverlanip, pullserverwanip, str(timegap), casedict, jobqueue, logqueue, ('', pullservport), handle)
    except:
        print 'cannot start pullserver', pullservport
        os.kill(os.getpid(), 15) #似乎是python2.7.1的bug，socket无法释放
        return

    try:
        pullserver.start()
    except KeyboardInterrupt:
        pullserver.pullserverun = False

    pullserver.server_close()
    pullthread1.exit()
    pullthread2.exit()
    pullthread3.exit()

if __name__ == '__main__':
    main()
