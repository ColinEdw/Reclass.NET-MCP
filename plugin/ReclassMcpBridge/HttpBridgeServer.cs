using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ReClassNET.Plugins;
using ReclassMcpBridge.Controllers;

namespace ReclassMcpBridge
{
    /// <summary>
    /// Lightweight HTTP server embedded in ReClass.NET that exposes
    /// process, memory, class, and analysis operations as REST endpoints.
    /// </summary>
    public class HttpBridgeServer
    {
        private readonly HttpListener _listener = new();
        private readonly IPluginHost _host;
        private readonly CancellationTokenSource _cts = new();

        private readonly ProcessController _process;
        private readonly MemoryController _memory;
        private readonly ClassController _classes;
        private readonly AnalysisController _analysis;
        private readonly Il2CppController _il2cpp;

        public HttpBridgeServer(IPluginHost host, int port)
        {
            _host = host;
            _listener.Prefixes.Add($"http://127.0.0.1:{port}/");

            _process = new ProcessController(host);
            _memory = new MemoryController(host);
            _classes = new ClassController(host);
            _analysis = new AnalysisController(host);
            _il2cpp = new Il2CppController(host);
        }

        public void Start()
        {
            _listener.Start();
            Task.Run(() => ListenLoop(_cts.Token));
        }

        public void Stop()
        {
            _cts.Cancel();
            _listener.Stop();
        }

        private async Task ListenLoop(CancellationToken ct)
        {
            while (!ct.IsCancellationRequested)
            {
                try
                {
                    var ctx = await _listener.GetContextAsync();
                    _ = Task.Run(() => HandleRequest(ctx));
                }
                catch (HttpListenerException) when (ct.IsCancellationRequested)
                {
                    break;
                }
                catch (Exception ex)
                {
                    _host.Logger.Log(ReClassNET.Logger.LogLevel.Error,
                        $"[MCP Bridge] Listener error: {ex.Message}");
                }
            }
        }

        private async Task HandleRequest(HttpListenerContext ctx)
        {
            var req = ctx.Request;
            var res = ctx.Response;
            res.ContentType = "application/json";

            try
            {
                var path = req.Url?.AbsolutePath ?? "";
                var method = req.HttpMethod;
                var body = await ReadBody(req);

                object? result = Route(path, method, body, req);

                var json = JsonConvert.SerializeObject(result ?? new { ok = true });
                var buffer = Encoding.UTF8.GetBytes(json);
                res.StatusCode = 200;
                res.ContentLength64 = buffer.Length;
                await res.OutputStream.WriteAsync(buffer, 0, buffer.Length);
            }
            catch (Exception ex)
            {
                var errJson = JsonConvert.SerializeObject(new { error = ex.Message });
                var buffer = Encoding.UTF8.GetBytes(errJson);
                res.StatusCode = 400;
                res.ContentLength64 = buffer.Length;
                await res.OutputStream.WriteAsync(buffer, 0, buffer.Length);
            }
            finally
            {
                res.Close();
            }
        }

        private object? Route(string path, string method, JObject? body, HttpListenerRequest req)
        {
            // Status
            if (path == "/api/status")
                return GetStatus();

            // Process
            if (path == "/api/process/list")
                return _process.List(req.QueryString["filter"]);
            if (path == "/api/process/attach" && method == "POST")
                return _process.Attach(body!.Value<int>("pid"));
            if (path == "/api/process/detach" && method == "POST")
                return _process.Detach();
            if (path == "/api/process/modules")
                return _process.GetModules();
            if (path == "/api/process/regions")
                return _process.GetRegions();

            // Memory
            if (path == "/api/memory/read" && method == "POST")
                return _memory.Read(body!);
            if (path == "/api/memory/read_typed" && method == "POST")
                return _memory.ReadTyped(body!);
            if (path == "/api/memory/write" && method == "POST")
                return _memory.Write(body!);
            if (path == "/api/memory/write_typed" && method == "POST")
                return _memory.WriteTyped(body!);
            if (path == "/api/memory/scan" && method == "POST")
                return _memory.Scan(body!);
            if (path == "/api/memory/pointer_chain" && method == "POST")
                return _memory.ResolvePointerChain(body!);

            // Classes
            if (path == "/api/classes" && method == "GET")
                return _classes.List();
            if (path == "/api/classes" && method == "POST")
                return _classes.Create(body!);
            if (path.StartsWith("/api/classes/") && path.EndsWith("/export") && method == "POST")
                return _classes.Export(ExtractClassName(path, "/export"), body!);
            if (path == "/api/classes/import" && method == "POST")
                return _classes.Import(body!);
            if (path.StartsWith("/api/classes/") && path.EndsWith("/rename") && method == "POST")
                return _classes.Rename(ExtractClassName(path, "/rename"), body!);
            if (path.StartsWith("/api/classes/") && path.Contains("/fields"))
                return RouteFields(path, method, body);
            if (path.StartsWith("/api/classes/") && method == "GET")
                return _classes.Get(path.Split('/')[3]);
            if (path.StartsWith("/api/classes/") && method == "DELETE")
                return _classes.Delete(path.Split('/')[3]);

            // Analysis
            if (path == "/api/analysis/suggest_types" && method == "POST")
                return _analysis.SuggestTypes(body!);
            if (path == "/api/analysis/dissect" && method == "POST")
                return _analysis.Dissect(body!);
            if (path == "/api/analysis/vtable" && method == "POST")
                return _analysis.ReadVTable(body!);

            // IL2CPP / Unity
            if (path == "/api/il2cpp/images")
                return _il2cpp.ListImages();
            if (path == "/api/il2cpp/find_class" && method == "POST")
                return _il2cpp.FindClass(body!);
            if (path == "/api/il2cpp/dump_class" && method == "POST")
                return _il2cpp.DumpClass(body!);
            if (path == "/api/il2cpp/class_fields" && method == "POST")
                return _il2cpp.ClassFields(body!);
            if (path == "/api/il2cpp/class_methods" && method == "POST")
                return _il2cpp.ClassMethods(body!);
            if (path == "/api/il2cpp/static_fields" && method == "POST")
                return _il2cpp.StaticFields(body!);
            if (path == "/api/il2cpp/read_string" && method == "POST")
                return _il2cpp.ReadString(body!);
            if (path == "/api/il2cpp/read_list" && method == "POST")
                return _il2cpp.ReadList(body!);
            if (path == "/api/il2cpp/read_array" && method == "POST")
                return _il2cpp.ReadArray(body!);
            if (path == "/api/il2cpp/method_address" && method == "POST")
                return _il2cpp.MethodAddress(body!);
            if (path == "/api/il2cpp/dump_object" && method == "POST")
                return _il2cpp.DumpObject(body!);
            if (path == "/api/il2cpp/scan_instances" && method == "POST")
                return _il2cpp.ScanInstances(body!);
            if (path == "/api/unity/find_gameobjects" && method == "POST")
                return _il2cpp.FindGameObjects(body!);
            if (path == "/api/unity/get_component" && method == "POST")
                return _il2cpp.GetComponent(body!);

            throw new Exception($"Unknown route: {method} {path}");
        }

        private object? RouteFields(string path, string method, JObject? body)
        {
            var parts = path.Split('/');
            var className = parts[3];

            if (method == "POST")
                return _classes.AddField(className, body!);

            if (parts.Length > 5 && int.TryParse(parts[5], out var offset))
            {
                if (method == "PATCH")
                    return _classes.ModifyField(className, offset, body!);
                if (method == "DELETE")
                    return _classes.RemoveField(className, offset);
            }

            throw new Exception($"Unknown fields route: {method} {path}");
        }

        private static string ExtractClassName(string path, string suffix)
        {
            var trimmed = path.Replace("/api/classes/", "").Replace(suffix, "");
            return Uri.UnescapeDataString(trimmed);
        }

        private static async Task<JObject?> ReadBody(HttpListenerRequest req)
        {
            if (!req.HasEntityBody) return null;
            using var reader = new StreamReader(req.InputStream, req.ContentEncoding);
            var text = await reader.ReadToEndAsync();
            return string.IsNullOrWhiteSpace(text) ? null : JObject.Parse(text);
        }

        private object GetStatus()
        {
            return new
            {
                connected = true,
                reclassVersion = "1.2",
                attachedProcess = (object?)null, // TODO: wire to actual state
                classCount = 0,
            };
        }
    }
}
