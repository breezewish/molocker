using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.IO;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Windows.Media.Effects;
using Infragistics.Controls.Interactions;
using System.Windows.Threading;

namespace MotionUnlockerController
{
    /// <summary>
    /// MainWindow.xaml 的交互逻辑
    /// </summary>
    public partial class MainWindow : Window
    {
        [DllImport("shell32.dll", EntryPoint = "#261",
                       CharSet = CharSet.Unicode, PreserveSig = false)]
        public static extern void GetUserTilePath(
              string username,
              UInt32 whatever, // 0x80000000
              StringBuilder picpath, int maxLength);

        PipeServer pipeServer = null;

        String credentialDirectory = @"C:\molocker\credentials";
        String gestureDirectory = @"C:\molocker\gestures";

        public static string GetUserTilePath(string username)
        {
            // username: use null for current user
            var sb = new StringBuilder(1000);
            GetUserTilePath(username, 0x80000000, sb, sb.Capacity);
            return sb.ToString();
        }

        private void switchPlane()
        {
            framePasswordRequired.Visibility = System.Windows.Visibility.Collapsed;
            frameMotionRequired.Visibility = System.Windows.Visibility.Collapsed;
            frameMotionOK.Visibility = System.Windows.Visibility.Collapsed;

            if (!File.Exists(credentialDirectory + "\\" + Environment.UserName))
            {
                framePasswordRequired.Visibility = System.Windows.Visibility.Visible;
                txtCurrentPass.Focus();
                return;
            }
            else if (!File.Exists(gestureDirectory + "\\" + Environment.UserName + ".mat"))
            {

                frameMotionRequired.Visibility = System.Windows.Visibility.Visible;
                btnStartRecording.Focus();
            }
            else
            {
                frameMotionOK.Visibility = System.Windows.Visibility.Visible;
            }
        }

        public static BitmapImage GetUserTile(string username)
        {
            return new BitmapImage(new Uri(GetUserTilePath(username)));
        }


        public MainWindow()
        {
            InitializeComponent();
        }

        private void Window_MouseLeftButtonDown_1(object sender, MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            this.DragMove();
        }

        private void lblExit_MouseDown(object sender, MouseButtonEventArgs e)
        {
            this.Close();
        }

        private void lblExit_Loaded(object sender, RoutedEventArgs e)
        {
            lblUserName.Content = Environment.UserName;
            lblCurrentUser.Content = Environment.UserName;
            picUserFace.Source = GetUserTile(Environment.UserName);
            btnStartRecording.Content = "Record for " + Environment.UserName;

            if (File.Exists(credentialDirectory + "\\" + Environment.UserName))
            {
                txtCurrentPass.Password = File.ReadAllText(credentialDirectory + "\\" + Environment.UserName);
            }

            switchPlane();
        }

        void pipeServer_PipeMessage(string Reply)
        {
            this.Dispatcher.Invoke((Action)(() =>
            {
                if (Reply == "1")
                {
                    SetDialogLabel("Put your hands on leap motion and keep static");
                }
                else if (Reply == "2")
                {
                    SetDialogLabel("Recording now... When you finished, keep static.");
                }
                else if (Reply == "3")
                {
                    SetDialogLabel("First gesture recorded. Please draw another gesture.");
                }
                else if (Reply == "4")
                {
                    SetDialogLabel("Gesture recording complete!");
                }
                else if (Reply == "5")
                {
                    SetDialogLabel("Gesture recording failed :(");
                }

            }));
        }

        void recordEnded(object sender, EventArgs e)
        {
            Console.WriteLine("process end");

            if (pipeServer != null)
            {
                pipeServer.Close();
                pipeServer = null;
            }

            this.Dispatcher.Invoke((Action)(() =>
            {
                switchPlane();
            }));

            p = null;
        }

        private void btnSaveCredential_Click(object sender, RoutedEventArgs e)
        {
            if (!Directory.Exists(credentialDirectory))
            {
                Directory.CreateDirectory(credentialDirectory);
            }
            File.WriteAllText(credentialDirectory + "\\" + Environment.UserName, txtCurrentPass.Password);

            txtCurrentPass.Password = "";

            ShowDialog("Credentials saved successfully!", "Molocker");
            switchPlane();
        }

        private void btnDeleteCredential_Click(object sender, RoutedEventArgs e)
        {
            Console.WriteLine("delete");
            try
            {
                File.Delete(credentialDirectory + "\\" + Environment.UserName);
                ShowDialog("Your login credential has been cleared.", "Molocker");
            }
            catch (Exception) { }
            switchPlane();
        }

        private void btnChangeCredential_Click(object sender, RoutedEventArgs e)
        {
            frameMotionRequired.Visibility = System.Windows.Visibility.Collapsed;
            framePasswordRequired.Visibility = System.Windows.Visibility.Visible;
            txtCurrentPass.Focus();
        }

        Process p = null;

        private void btnStartRecording_Click(object sender, RoutedEventArgs e)
        {
            var startInfo = new ProcessStartInfo(@"C:\Anaconda\python.exe", @"C:\molocker\src\screen_lock.py -s -n " + Environment.UserName);
            startInfo.WorkingDirectory = @"C:\molocker\src";
            startInfo.WindowStyle = ProcessWindowStyle.Hidden;

            pipeServer = new PipeServer();
            pipeServer.Listen("molocker_record");
            pipeServer.PipeMessage += pipeServer_PipeMessage;

            ShowDialog("Connecting to Leap Motion...", "molocker");

            AllowUIToUpdate();

            p = new Process();
            p.StartInfo = startInfo;
            p.EnableRaisingEvents = true;
            p.Exited += recordEnded;
            p.Start();
        }

        private void btnChangeCredential2_Click(object sender, RoutedEventArgs e)
        {
            frameMotionOK.Visibility = System.Windows.Visibility.Collapsed;
            framePasswordRequired.Visibility = System.Windows.Visibility.Visible;
            txtCurrentPass.Focus();
        }

        private void btnChangeGesture_Click(object sender, RoutedEventArgs e)
        {
            btnStartRecording_Click(null, null);
        }

        private void btnClearGesture_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                File.Delete(gestureDirectory + "\\" + Environment.UserName + ".mat");
                ShowDialog("Your gesture has been cleared.", "Molocker");
            }
            catch (Exception) { }
            switchPlane();
        }


        private XamDialogWindow CreateDialogWindow(String header, String content)
        {
            var dialog = new XamDialogWindow()
            {
                Width = 350,
                Height = 100,
                StartupPosition = StartupPosition.Center,
                //CloseButtonVisibility = Visibility.Collapsed,
                Header = header,
                Content = content,
                IsModal = true
            };

            return dialog;
        }

        Label dialogLabel = null;
        XamDialogWindow dialog = null;

        private void ShowDialog(String content, String header)
        {
            var blurEffect = new BlurEffect() { Radius = 5 };
            containerContent.Opacity = 0.4;
            containerContent.Effect = blurEffect;

            dialog = CreateDialogWindow(header, content);
            dialog.IsVisibleChanged += dialog_IsVisibleChanged;
            containerMain.Children.Add(dialog);

            dialogLabel = new Label();
            dialogLabel.Content = content;
            dialogLabel.HorizontalAlignment = System.Windows.HorizontalAlignment.Center;
            dialogLabel.VerticalAlignment = System.Windows.VerticalAlignment.Center;

            dialog.Content = dialogLabel;
        }

        void AllowUIToUpdate()
        {
            DispatcherFrame frame = new DispatcherFrame();
            Dispatcher.CurrentDispatcher.BeginInvoke(DispatcherPriority.Render, new DispatcherOperationCallback(delegate(object parameter)
            {
                frame.Continue = false;
                return null;
            }), null);

            Dispatcher.PushFrame(frame);
        }

        private void SetDialogLabel(String content)
        {
            dialogLabel.Content = content;
            AllowUIToUpdate();
        }

        private void CloseDialog()
        {
            dialog.Close();
        }

        void dialog_IsVisibleChanged(object sender, DependencyPropertyChangedEventArgs e)
        {
            if ((bool)e.NewValue == false)
            {
                var dialog = (XamDialogWindow)sender;
                containerContent.Opacity = 1;
                containerContent.Effect = null;
                containerMain.Children.Remove(dialog);

                if (p != null)
                {
                    p.Close();
                }
            }
        }

    }
}
