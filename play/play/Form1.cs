using System;
using System.Collections.Generic;
using System.ComponentModel;
//using System.Data;
//using System.Drawing;
//using System.Text;
using System.Windows.Forms;
using System.Net;
using System.Threading;
using System.IO;
using System.Diagnostics;


namespace play
{
    public partial class Form1 : Form
    {
        Dictionary<string, string> workArgument = new Dictionary<string,string>(); 
        BackgroundWorker work = new BackgroundWorker();

        public Form1()
        {
            InitializeComponent();

            work.WorkerSupportsCancellation = true;
            work.WorkerReportsProgress = true;
            work.DoWork += new DoWorkEventHandler(workDo);
            work.ProgressChanged += new ProgressChangedEventHandler(workChange);
            work.RunWorkerCompleted += new RunWorkerCompletedEventHandler(workComplete);
        }

        private void startButton_Click(object sender, EventArgs e)
        {
            if (pullServerIpBox.Text.Trim().Length != 0 && pullServerPortBox.Text.Trim().Length != 0 && talkPairBox.Text.Trim().Length != 0)
            {
                pullServerIpBox.ReadOnly = true;
                pullServerPortBox.ReadOnly = true;
                talkPairBox.ReadOnly = true;
                startButton.Enabled = false;
                stopButton.Enabled = true;
                caseNameBox.Clear();
                rtmpBox.Clear();
                hdlBox.Clear();
                hlsBox.Clear();
                label1.Visible = false;
                workArgument["playurl"] = "http://" + pullServerIpBox.Text.Trim() + ":" + pullServerPortBox.Text.Trim() + "/play";
                workArgument["talkpair"] = talkPairBox.Text.Trim();
                work.RunWorkerAsync(workArgument);
            }
        }

        private void stopButton_Click(object sender, EventArgs e)
        {
            work.CancelAsync();
        }

        private void workDo(object sender, DoWorkEventArgs e)
        {
            BackgroundWorker me =  (BackgroundWorker)sender;
            Dictionary<string, string> argument = (Dictionary<string, string>)e.Argument ;
            Dictionary<string, string> result = new Dictionary<string, string>();

            WebRequest request = null;
            WebResponse response = null;
           
            while (!e.Cancel)
            {
                try
                {
                    request = WebRequest.Create(argument["playurl"]);
                    request.Timeout = 17000;
                    request.Headers.Set("talkpair", argument["talkpair"]);

                    response = request.GetResponse();
                    if (response.Headers.Get("talkpair") == argument["talkpair"])
                    {
                        result["casename"] = response.Headers.Get("casename");
                        result["rtmpurl"] = response.Headers.Get("rtmppul");
                        result["hdlurl"] = response.Headers.Get("hdlpul");
                        result["hlsurl"] = response.Headers.Get("hlspul");

                        me.ReportProgress(0, result);
                    }

                    response.Close();
                    request.Abort();
                }
                catch
                {
                }

                if (me.CancellationPending)
                {
                    e.Cancel = true;
                }

                Thread.Sleep(7000);
            }
        }

        private void workChange(object sender,ProgressChangedEventArgs e)
        {
            Dictionary<string, string> result = (Dictionary<string, string>)e.UserState;

            if (result["casename"] != null && result["casename"] != caseNameBox.Text)
            {
                label1.Visible = true;
            }
            else
            {
                label1.Visible = false;
            }

            caseNameBox.Text = result["casename"];
            rtmpBox.Text = result["rtmpurl"];
            hdlBox.Text = result["hdlurl"];
            hlsBox.Text = result["hlsurl"];
        }

        private void workComplete(object sender, RunWorkerCompletedEventArgs e)
        {
            stopButton.Enabled = false;
            startButton.Enabled = true;
            pullServerIpBox.ReadOnly = false;
            pullServerPortBox.ReadOnly = false;
            talkPairBox.ReadOnly = false;
        }

        private void rtmpPlayButton_Click(object sender, EventArgs e)
        {
            if (vlcPathBox.Text.Trim().ToLower().EndsWith("vlc.exe") && File.Exists(vlcPathBox.Text.Trim()) && rtmpBox.Text.Length != 0)
            {
                Process.Start(vlcPathBox.Text.Trim(), "--width=640 --height=480 " + rtmpBox.Text);
                return;
            }
            if (File.Exists("ffplay.exe") && rtmpBox.Text.Length != 0)
            {
                Process.Start("ffplay.exe", "-x 640 -y 480  -window_title \"rtmp " + caseNameBox.Text + " " + rtmpBox.Text + "\" -i \"" + rtmpBox.Text + "\"");
                return;
            }
        }

        private void hdlPlayButton_Click(object sender, EventArgs e)
        {
            if (vlcPathBox.Text.Trim().ToLower().EndsWith("vlc.exe") && File.Exists(vlcPathBox.Text.Trim()) && hdlBox.Text.Length != 0)
            {
                Process.Start(vlcPathBox.Text.Trim(), "--width=640 --height=480 " + hdlBox.Text);
                return;
            }
            if (File.Exists("ffplay.exe") && hdlBox.Text.Length != 0)
            {
                Process.Start("ffplay.exe", "-x 640 -y 480 -window_title \"hdl " + caseNameBox.Text + " " + hdlBox.Text + "\" -i \"" + hdlBox.Text + "\"");
                return;
            }
        }

        private void hlsPlayButton_Click(object sender, EventArgs e)
        {
            if (vlcPathBox.Text.Trim().ToLower().EndsWith("vlc.exe") && File.Exists(vlcPathBox.Text.Trim()) && hdlBox.Text.Length != 0)
            {
                Process.Start(vlcPathBox.Text.Trim(), "--width=640 --height=480 " + hdlBox.Text);
                return;
            }
            if (File.Exists("ffplay.exe") && hlsBox.Text.Length != 0)
            {
                Process.Start("ffplay.exe", "-x 640 -y 480 -window_title \"hls " + caseNameBox.Text + " " + hlsBox.Text + "\" -i \"" + hlsBox.Text + "\"");
                return;
            }
        }

        private void rtmpCopyButton_Click(object sender, EventArgs e)
        {
            if (rtmpBox.Text.Length != 0)
            {
                Clipboard.SetText(rtmpBox.Text);
            }
        }

        private void hdlCopyButton_Click(object sender, EventArgs e)
        {
            if (hdlBox.Text.Length != 0)
            {
                Clipboard.SetText(hdlBox.Text);
            }
        }

        private void hlsCopyButton_Click(object sender, EventArgs e)
        {
            if (hlsBox.Text.Length != 0)
            {
                Clipboard.SetText(hlsBox.Text);
            }
        }

        private void checkBox1_CheckedChanged(object sender, EventArgs e)
        {
            if (!checkBox1.Checked)
            {
                this.TopMost = false;
            }
            else
            {
                this.TopMost = true;
            }
        }

    }
}
