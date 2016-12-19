[usage]
pull.py/push.py is intented to verify streaming profile, frame loss and delay based on pts
play.exe is used for downstreaming playback and human observation

[proposition]
pull.py/push.py works much worse on widows than it does on linux due to windows' poor management of child-processes and stderr/stdout redirection, therefore highly recommend runing pull.py/push.py on linux
before runing pull.py/push.py on windows, please turn off "Windows Error Reporting" in case of jamming ffmpeg/ffprob.exe from exit, or by simply double-clicking dontshowui.reg to disable that reporting

[step]
1. extract multi-volume-zip ffmpeg/mp4.mp4
2. edit case/stream.ini
3. run pull.py
4. run push.py
5. run play.exe if need be
6. read log/stream.log

[system requirement]
linux :             linux a64
windows :           >= windows xp i386/a64

[runtime requirement]
python :            >= python 2.7.1; linux a64, windows i386/a64
.net framework :    >= .net framework 2.0, windows i386/a64

[pull's parameter]
-pullserverport :   optional; will bind random port if not passed; legal range: 49152-65535
-talkpair :         optional; will generate uuid if not passed

[push's paramter]
-pullserverport :   required; legal range: 49152-65535
-talkpair :         required
-pullserverip :     optional; will connect to 127.0.0.1 if not passed
-logrefer :         optional; will rename log/stream.log refer to talkpair

[case/stream.ini]
casename :          unique casename                                     #each casename must be unique
rtmppushsupport :   true                                                #default is true; legal range: true, false
rtmppushurl :       rtmp://rtmppuh.host.domain.com/app/stream           #must in the form of rtmp://......., after urlencode
rtmppullsupport :   true                                                #default is true; legal range: true, false
rtmppullurl :       rtmp://rtmppul.host.domain.com/app/stream           #must in the form of rtmp://......., after urlencode
hdlpullsupport :    true                                                #default is true; legal range: true, false
hdlpullurl :        http://hdlpul.host.domain.com/app/stream.flv        #must in the form of http://......., after urlencode
hlspullsupport :    true                                                #default is true; legal range: true, false
hlspullurl :        http://hlspul.host.domain.com/app/stream/index.m3u8 #must in the form of http://......., after urlencode
formatcontainer :   flv                                                 #default is flv; legal range: flv
videocodec :        libx264                                             #default is libx264; legal range: libx264
videiobitrate :     800000                                              #default is 800000; legal range: positive int, multiples of 1000, <= ffmpeg/mp4.mp4's profile
videoframerate :    24                                                  #default is 24; legal range: positive int, <= ffmpeg/mp4.mp4's profile
videoresolution :   854x480                                             #default is 854x480; legal range: positiveInt x positiveInt,  <= ffmpeg/mp4.mp4's profile
audiocodec :        aac                                                 #default is aac; legal range: aac, libmp3lame
audiobitrate :      64000                                               #default is 64000; legal range: positive int, multiples of 1000, <= ffmpeg/mp4.mp4's profile
audiosamplerate :   44100                                               #default is 44100; legal range: 44100, 22050
audiochannel :      2                                                   #default is 2; legal range: 2, 1

[log/stream.log]
casetime :          string                                              #case start time string
casename :          string                                              #casename frome case/stream.ini
rtmppuhspt :        True|False                                          #rtmppushsupport from case/stream.ini
rtmppuhurl :        string                                              #rtmppushurl from case/stream.ini
rtmppulspt :        True|False                                          #rtmppullsupport from case/stream.ini
rtmppulurl :        string                                              #rtmppullurl from case/stream.ini
hdlpulspt :         True|False                                          #hdlpullsupport from case/stream.ini
hdlpulurl :         string                                              #hdlpullurl from case/stream.ini
hlspulspt :         True|False                                          #hlspullsupport from case/stream.ini
hlspulurl :         string                                              #hlspullurl from case/stream.ini
rtmppuhmta :        json                                                #rtmp push metadata from ffmpeg/metadata.txt
rtmppuhfmtctn :     string                                              #rtmp push formatcontainer from case/stream.ini
rtmppuhvcdc :       string                                              #rtmp push videocodec from case/stream.ini
rtmppuhvbrte :      float                                               #rtmp push videiobitrate from case/stream.ini
rtmppuhvfrmrte :    float                                               #rtmp push videoframerate from case/stream.ini
rtmppuhvres :       int x int                                           #rtmp push videoresolution from case/stream.ini
rtmppuhacdc :       string                                              #rtmp push audiocodec from case/stream.ini
rtmppuhabrte :      float                                               #rtmp push audiobitrate from case/stream.ini
rtmppuhasplrte :    float                                               #rtmp push audiosamplerate from case/stream.ini
rtmppuhachn :       float                                               #rtmp push audiochannel from case/stream.ini
rtmppuhdrt :        float                                               #rtmp push duration
rtmppuhvfld :       float|UNDEFINED                                     #rtmp push video first screen timestamp
rtmppuhafld :       float|UNDEFINED                                     #rtmp push audio first screen timestamp
rtmppuhvlog :       json|UNDEFINED                                      #rtmp push video log
rtmppuhalog :       json|UNDEFINED                                      #rtmp push audio log
rtmppuhsptrlt :     PASSED|FAILED|UNDEFINED                             #if rtmppushsupport is true, and it has successfully upstreamed to rtmppushurl, rtmppuhsptrlt is PASSED; otherwise FAILED
rtmppulmta :        json|UNDEFINED                                      #rtmp pull metadata
rtmppulfmtctn :     string|UNDEFINED                                    #rtmp pull format container
rtmppulvcdc :       string|UNDEFINED                                    #rtmp pull video codec
rtmppulvbrte :      float|UNDEFINED                                     #rtmp pull video bitrate
rtmppulvfrmrte :    float|UNDEFINED                                     #rtmp pull video framerate
rtmppulvres :       string|UNDEFINED                                    #rtmp pull video resolution
rtmppulacdc :       string|UNDEFINED                                    #rtmp pull audio codec
rtmppulabrte :      float|UNDEFINED                                     #rtmp pull audio bitrate
rtmppulasplrte :    float|UNDEFINED                                     #rtmp pull audio samplerate
rtmppulachn :       float|UNDEFINED                                     #rtmp pull audio channel
rtmppulvfld :       float|UNDEFINED                                     #rtmp pull video first screen timestamp
rtmppulafld :       float|UNDEFINED                                     #rtmp pull audio first screen timestamp
rtmppulvlog :       json|UNDEFINED                                      #rtmp pull vidio log
rtmppulalog :       json|UNDEFINED                                      #rtmp pull audio log
rtmppulsptrlt :     PASSED|FAILED|UNDEFINED                             #if rtmppullsupport is true, and it has successfully downstreamed from rtmppullurl, rtmppulsptrlt is PASSED; otherwise FAILED
rtmpmtarlt :        PASSED|FAILED|UNDEFINED                             #rtmp pull metadata compare result
rtmpfmtctnrlt :     PASSED|FAILED|UNDEFINED                             #rtmp pull format container compare result
rtmpvcdcrlt :       PASSED|FAILED|UNDEFINED                             #rtmp pull video codec compare result
rtmpvbrterlt :      PASSED|FAILED|UNDEFINED                             #rtmp pull video bitrate compare result
rtmpvfrmrterlt :    PASSED|FAILED|UNDEFINED                             #rtmp pull video framerate compare result
rtmpvresrlt :       PASSED|FAILED|UNDEFINED                             #rtmp pull video resolution compare result
rtmpacdcrlt :       PASSED|FAILED|UNDEFINED                             #rtmp pull audio codec compare result
rtmpabrterlt :      PASSED|FAILED|UNDEFINED                             #rtmp pull audio bitrate compare result
rtmpasplrterlt :    PASSED|FAILED|UNDEFINED                             #rtmp pull audio samplerate compare result
rtmpachnrlt :       PASSED|FAILED|UNDEFINED                             #rtmp pull audio channel compare result
rtmpvlosfrm :       int|UNDEFINED                                       #rtmp pull video loss frame count
rtmpvtolfrm :       int|UNDEFINED                                       #rtmp pull video total frame count
rtmpvlosfrmrto :    float|UNDEFINED                                     #rtmp pull video loss frame ratio
rtmpvmaxconlosfrm : int|UNDEFINED                                       #rtmp pull video max consecutive loss frame count
rtmpvminconlosfrm : int|UNDEFINED                                       #rtmp pull video min consecutive loss frame count
rtmpvflddly :       float|UNDEFINED                                     #rtmp pull video first screen delay
rtmpvavgdly :       float|UNDEFINED                                     #rtmp pull video average delay
rtmpvmaxdly :       float|UNDEFINED                                     #rtmp pull video max delay
rtmpvmindly :       float|UNDEFINED                                     #rtmp pull video min delay
rtmpalosfrm :       int|UNDEFINED                                       #rtmp pull audio loss frame count
rtmpatolfrm :       int|UNDEFINED                                       #rtmp pull audio total frame count
rtmpalosfrmrto :    float|UNDEFINED                                     #rtmp pull audio loss frame ratio
rtmpamaxconlosfrm : int|UNDEFINED                                       #rtmp pull audio max consecutive loss frame count
rtmpaminconlosfrm : int|UNDEFINED                                       #rtmp pull audio min consecutive loss frame count
rtmpaflddly :       float|UNDEFINED                                     #rtmp pull audio first screen delay
rtmpaavgdly :       float|UNDEFINED                                     #rtmp pull audio average delay
rtmpamaxdly :       float|UNDEFINED                                     #rtmp pull audio max delay
rtmpamindly :       float|UNDEFINED                                     #rtmp pull audio min delay
hdlpulmta :         json|UNDEFINED                                      #hdl pull log section
hdlpulfmtctn :      string|UNDEFINED
hdlpulvcdc :        string|UNDEFINED
hdlpulvbrte :       float|UNDEFINED
hdlpulvfrmrte :     float|UNDEFINED
hdlpulvres :        string|UNDEFINED
hdlpulacdc :        string|UNDEFINED
hdlpulabrte :       float|UNDEFINED
hdlpulasplrte :     float|UNDEFINED
hdlpulachn :        float|UNDEFINED
hdlpulvfld :        float|UNDEFINED
hdlpulafld :        float|UNDEFINED
hdlpulvlog :        json|UNDEFINED
hdlpulalog :        json|UNDEFINED
hdlpuhsptrlt :      PASSED|FAILED|UNDEFINED
hdlmtarlt :         PASSED|FAILED|UNDEFINED
hdlfmtctnrlt :      PASSED|FAILED|UNDEFINED
hdlvcdcrlt :        PASSED|FAILED|UNDEFINED
hdlvbrterlt :       PASSED|FAILED|UNDEFINED
hdlvfrmrterlt :     PASSED|FAILED|UNDEFINED
hdlvresrlt :        PASSED|FAILED|UNDEFINED
hdlacdcrlt :        PASSED|FAILED|UNDEFINED
hdlabrterlt :       PASSED|FAILED|UNDEFINED
hdlasplrterlt :     PASSED|FAILED|UNDEFINED
hdlachnrlt :        PASSED|FAILED|UNDEFINED
hdlvlosfrm :        int|UNDEFINED
hdlvtolfrm :        int|UNDEFINED
hdlvlosfrmrto :     float|UNDEFINED
hdlvmaxconlosfrm :  int|UNDEFINED
hdlvminconlosfrm :  int|UNDEFINED
hdlvflddly :        float|UNDEFINED
hdlvavgdly :        float|UNDEFINED
hdlvmaxdly :        float|UNDEFINED
hdlvmindly :        float|UNDEFINED
hdlalosfrm :        int|UNDEFINED
hdlatolfrm :        int|UNDEFINED
hdlalosfrmrto :     float|UNDEFINED
hdlamaxconlosfrm :  int|UNDEFINED
hdlaminconlosfrm :  int|UNDEFINED
hdlaflddly :        float|UNDEFINED
hdlaavgdly :        float|UNDEFINED
hdlamaxdly :        float|UNDEFINED
hdlamindly :        float|UNDEFINED
hlspulmta :         json|UNDEFINED                                      #hls pull log section
hlspulfmtctn :      string|UNDEFINED
hlspulvcdc :        string|UNDEFINED
#hlspulvbrte :       float||UNDEFINED
hlspulvfrmrte :     float||UNDEFINED
hlspulvres :        string|UNDEFINED
hlspulacdc :        string|UNDEFINED
hlspulabrte :       float|UNDEFINED
hlspulasplrte :     float|UNDEFINED
hlspulachn :        float|UNDEFINED
hlspulvfld :        float|UNDEFINED
hlspulafld :        float|UNDEFINED
hlspuhsptrlt :      PASSED|FAILED|UNDEFINED
hlsmtarlt :         PASSED|FAILED|UNDEFINED
hlsfmtctnrlt :      PASSED|FAILED|UNDEFINED
hlsvcdcrlt :        PASSED|FAILED|UNDEFINED
#hlsvbrterlt :       PASSED|FAILED|UNDEFINED
hlsvfrmrterlt :     PASSED|FAILED|UNDEFINED
hlsvresrlt :        PASSED|FAILED|UNDEFINED
hlsacdcrlt :        PASSED|FAILED|UNDEFINED
hlsabrterlt :       PASSED|FAILED|UNDEFINED
hlsasplrterlt :     PASSED|FAILED|UNDEFINED
hlsachnrlt :        PASSED|FAILED|UNDEFINED
hlsvflddly :        float|UNDEFINED
hlsaflddly :        float|UNDEFINED
