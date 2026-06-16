using System;
using System.Drawing;
using ReClassNET.Plugins;

namespace ReclassMcpBridge
{
    public class ReclassMcpBridgeExt : Plugin
    {
        private HttpBridgeServer? _server;

        public override Image Icon
        {
            get
            {
                var bmp = new Bitmap(16, 16);
                using (var g = Graphics.FromImage(bmp))
                {
                    g.Clear(Color.FromArgb(0x2D, 0x9B, 0x56));
                    g.DrawString("M", new Font("Arial", 9, FontStyle.Bold), Brushes.White, 1, 0);
                }
                return bmp;
            }
        }

        public override bool Initialize(IPluginHost host)
        {
            try
            {
                var port = 27015;
                var envPort = Environment.GetEnvironmentVariable("RECLASS_BRIDGE_PORT");
                if (envPort != null && int.TryParse(envPort, out var p))
                    port = p;

                _server = new HttpBridgeServer(host, port);
                _server.Start();

                host.Logger.Log(ReClassNET.Logger.LogLevel.Information,
                    $"[MCP Bridge] HTTP server listening on port {port}");

                return true;
            }
            catch (Exception ex)
            {
                host.Logger.Log(ReClassNET.Logger.LogLevel.Error,
                    $"[MCP Bridge] Failed to start: {ex.Message}");
                return false;
            }
        }

        public override void Terminate()
        {
            _server?.Stop();
            _server = null;
        }
    }
}
