using System;
using System.Drawing;
using ReClassNET.Plugins;

namespace ReclassMcpBridge
{
    /// <summary>
    /// ReClass.NET plugin entry point. Starts the HTTP bridge server
    /// so the MCP server can communicate with ReClass.NET.
    /// </summary>
    public class BridgePlugin : Plugin
    {
        private HttpBridgeServer? _server;

        public override Image Icon => null!;

        public override bool Initialize(IPluginHost host)
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

        public override void Terminate()
        {
            _server?.Stop();
            _server = null;
        }
    }
}
