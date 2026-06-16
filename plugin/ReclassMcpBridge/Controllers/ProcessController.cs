using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using ReClassNET.Plugins;

namespace ReclassMcpBridge.Controllers
{
    public class ProcessController
    {
        private readonly IPluginHost _host;

        public ProcessController(IPluginHost host) => _host = host;

        public object List(string? filter)
        {
            var procs = Process.GetProcesses()
                .Where(p => string.IsNullOrEmpty(filter) ||
                            p.ProcessName.IndexOf(filter, System.StringComparison.OrdinalIgnoreCase) >= 0)
                .Select(p => new
                {
                    pid = p.Id,
                    name = p.ProcessName,
                    path = TryGetPath(p),
                    architecture = System.Environment.Is64BitOperatingSystem ? "x64" : "x86",
                    modules = new List<object>(),
                })
                .OrderBy(p => p.name)
                .Take(200)
                .ToList();

            return procs;
        }

        public object Attach(int pid)
        {
            // TODO: Call _host.Process.Open(pid) or equivalent ReClass.NET API
            var proc = Process.GetProcessById(pid);
            return new
            {
                pid = proc.Id,
                name = proc.ProcessName,
                path = TryGetPath(proc),
                architecture = "x64",
                modules = new List<object>(),
            };
        }

        public object Detach()
        {
            // TODO: Call _host.Process.Close() or equivalent
            return new { ok = true };
        }

        public object GetModules()
        {
            // TODO: Read from the attached process via ReClass.NET API
            return new List<object>();
        }

        public object GetRegions()
        {
            // TODO: Query virtual memory map via ReClass.NET API
            return new List<object>();
        }

        private static string TryGetPath(Process p)
        {
            try { return p.MainModule?.FileName ?? ""; }
            catch { return ""; }
        }
    }
}
