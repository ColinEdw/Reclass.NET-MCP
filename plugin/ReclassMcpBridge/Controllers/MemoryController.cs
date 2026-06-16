using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using Newtonsoft.Json.Linq;
using ReClassNET.Plugins;

namespace ReclassMcpBridge.Controllers
{
    public class MemoryController
    {
        private readonly IPluginHost _host;

        public MemoryController(IPluginHost host) => _host = host;

        public object Read(JObject body)
        {
            var address = ParseAddress(body.Value<string>("address")!);
            var size = body.Value<int>("size");

            // TODO: Replace with _host.Process.ReadRemoteMemory(address, size)
            var bytes = new byte[size];
            var hex = BitConverter.ToString(bytes).Replace("-", " ");
            var ascii = new string(bytes.Select(b => b >= 0x20 && b <= 0x7E ? (char)b : '.').ToArray());

            return new
            {
                address = $"0x{address:X}",
                hex,
                ascii,
                bytes = bytes.Select(b => (int)b).ToArray(),
            };
        }

        public object ReadTyped(JObject body)
        {
            var address = ParseAddress(body.Value<string>("address")!);
            var type = body.Value<string>("type")!;

            // TODO: Read from process memory and interpret as the given type
            return new
            {
                address = $"0x{address:X}",
                type,
                value = (object)0,
                rawHex = "00000000",
            };
        }

        public object Write(JObject body)
        {
            var address = ParseAddress(body.Value<string>("address")!);
            var bytes = body["bytes"]!.Select(t => (byte)t.Value<int>()).ToArray();

            // TODO: _host.Process.WriteRemoteMemory(address, bytes)
            return new { ok = true, written = bytes.Length };
        }

        public object WriteTyped(JObject body)
        {
            var address = ParseAddress(body.Value<string>("address")!);
            var type = body.Value<string>("type")!;
            var value = body["value"]!.ToString();

            // TODO: Convert value to bytes based on type and write
            return new { ok = true };
        }

        public object Scan(JObject body)
        {
            var type = body.Value<string>("type")!;
            var value = body["value"]!.ToString();
            var maxResults = body.Value<int?>("maxResults") ?? 100;

            // TODO: Implement memory scanning via ReClass.NET API
            return new List<object>();
        }

        public object ResolvePointerChain(JObject body)
        {
            var baseAddr = body.Value<string>("base")!;
            var offsets = body["offsets"]!.Select(t => t.Value<int>()).ToList();

            // TODO: Walk pointer chain using _host.Process.ReadRemoteMemory
            var resolved = new List<string> { $"0x{ParseAddress(baseAddr):X}" };
            foreach (var off in offsets)
                resolved.Add($"0x{off:X}");

            return new
            {
                @base = baseAddr,
                offsets,
                resolvedAddresses = resolved,
                finalAddress = resolved.Last(),
                finalValue = (object?)null,
            };
        }

        private static long ParseAddress(string addr)
        {
            addr = addr.Trim();
            if (addr.StartsWith("0x", StringComparison.OrdinalIgnoreCase))
                addr = addr.Substring(2);
            return long.Parse(addr, NumberStyles.HexNumber);
        }
    }
}
