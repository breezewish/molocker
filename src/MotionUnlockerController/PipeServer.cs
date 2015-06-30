using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.IO.Pipes;
using System.Diagnostics;

namespace MotionUnlockerController
{
    // Delegate for passing received message back to caller
    public delegate void DelegateMessage(string Reply);
    public delegate void PipeCreateEvent();

    class PipeServer
    {
        public event DelegateMessage PipeMessage;
        string _pipeName;

        public NamedPipeServerStream pipeServer;

        public void Listen(string PipeName)
        {
            try
            {
                // Set to class level var so we can re-use in the async callback method
                _pipeName = PipeName;
                // Create the new async pipe 
                pipeServer = new NamedPipeServerStream(PipeName, PipeDirection.InOut, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous);

                // Wait for a connection
                pipeServer.BeginWaitForConnection(new AsyncCallback(WaitForConnectionCallBack), pipeServer);
            }
            catch (Exception oEX)
            {
                Debug.WriteLine(oEX.Message);
            }
        }

        public void Close()
        {
            if (pipeServer != null)
            {
                pipeServer.Close();
                pipeServer = null;
            }
        }

        private void WaitForConnectionCallBack(IAsyncResult iar)
        {
            try
            {
                // Get the pipe
                NamedPipeServerStream pipeServer = (NamedPipeServerStream)iar.AsyncState;
                // End waiting for the connection
                pipeServer.EndWaitForConnection(iar);

                byte[] buffer = new byte[255];

                // Read message size
                pipeServer.Read(buffer, 0, 4);

                // Read message body
                int count = BitConverter.ToInt32(buffer, 0);

                // Clear buffer
                pipeServer.Read(buffer, 0, count);

                // Convert byte buffer to string
                string stringData = Encoding.UTF8.GetString(buffer, 0, count);

                try
                {
                    // Pass message back to calling form
                    PipeMessage.Invoke(stringData);
                }
                catch (Exception e)
                {
                    Console.WriteLine(e.Message);
                }

                // Kill original sever and create new wait server
                pipeServer.Close();
                pipeServer = null;
                pipeServer = new NamedPipeServerStream(_pipeName, PipeDirection.In,
                   1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous);

                // Recursively wait for the connection again and again....
                pipeServer.BeginWaitForConnection(
                   new AsyncCallback(WaitForConnectionCallBack), pipeServer);
            }
            catch
            {
                return;
            }
        }
    }
}
