// Dedicated local WebView2 client. No script-to-shell bridge.
using System;
using System.IO;
using System.Net;
using System.Drawing;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

class SimplicityWindow : Form {
    readonly WebView2 view = new WebView2();
    readonly Timer timer = new Timer();
    readonly string root = AppDomain.CurrentDomain.BaseDirectory;

    public SimplicityWindow() {
        Text = "SimplicityAI";
        AutoScaleMode = AutoScaleMode.None;
        float scale;
        using (var graphics = Graphics.FromHwnd(IntPtr.Zero)) { scale = graphics.DpiX / 96f; }
        var area = Screen.PrimaryScreen.WorkingArea;
        Size = new Size(Math.Min((int)(1040 * scale), area.Width), Math.Min((int)(820 * scale), area.Height));
        MinimumSize = new Size(Math.Min((int)(560 * scale), area.Width), Math.Min((int)(560 * scale), area.Height));
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.FromArgb(16, 23, 34);
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        view.Dock = DockStyle.Fill;
        view.CreationProperties = new CoreWebView2CreationProperties {
            UserDataFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SimplicityAI", "WebView2")
        };
        Controls.Add(view);
        Shown += Initialize;
        timer.Interval = 1000;
        timer.Tick += CheckService;
    }

    async void Initialize(object sender, EventArgs e) {
        try {
            string url = File.ReadAllText(Path.Combine(root, "..", "session-url.txt")).Trim();
            if (!Regex.IsMatch(url, @"^http://127\.0\.0\.1:8769/#[A-Za-z0-9_-]+$"))
                throw new Exception("Invalid local session address.");
            await view.EnsureCoreWebView2Async(null);
            view.CoreWebView2.Settings.AreDevToolsEnabled = false;
            view.CoreWebView2.Settings.AreDefaultContextMenusEnabled = false;
            view.CoreWebView2.Settings.IsStatusBarEnabled = false;
            view.CoreWebView2.NavigationStarting += (s, args) => {
                if (!Regex.IsMatch(args.Uri, @"^http://127\.0\.0\.1:8769/(?:#.*)?$")) args.Cancel = true;
            };
            view.CoreWebView2.NewWindowRequested += (s, args) => { args.Handled = true; };
            view.Source = new Uri(url);
            timer.Start();
        } catch (Exception error) {
            File.AppendAllText(Path.Combine(root, "..", "logs", "window-error.log"), error.ToString()+Environment.NewLine);
            MessageBox.Show("SimplicityAI could not open its window. Check that Microsoft Edge WebView2 Runtime is installed. Details are in logs/window-error.log.", "SimplicityAI");
            Close();
        }
    }

    async void CheckService(object sender, EventArgs e) {
        timer.Stop();
        try {
            var request = WebRequest.Create("http://127.0.0.1:8769/health");
            request.Timeout = 1000;
            using (var response = await request.GetResponseAsync()) { }
            if (!IsDisposed) timer.Start();
        } catch { if (!IsDisposed) Close(); }
    }

    protected override void Dispose(bool disposing) {
        if (disposing) { timer.Dispose(); view.Dispose(); }
        base.Dispose(disposing);
    }

    [STAThread]
    static void Main() {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new SimplicityWindow());
    }
}
