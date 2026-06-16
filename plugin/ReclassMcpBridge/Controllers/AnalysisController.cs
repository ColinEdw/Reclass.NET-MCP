using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using ReClassNET.Plugins;

namespace ReclassMcpBridge.Controllers
{
    public class AnalysisController
    {
        private readonly IPluginHost _host;

        public AnalysisController(IPluginHost host) => _host = host;

        public object SuggestTypes(JObject body)
        {
            var address = body.Value<string>("address")!;
            var size = body.Value<int>("size");

            // TODO: Read memory, run heuristics (pointer detection, float range checks,
            // string detection, alignment analysis) and return type suggestions
            return new List<object>();
        }

        public object Dissect(JObject body)
        {
            var address = body.Value<string>("address")!;
            var size = body.Value<int>("size");

            // TODO: Auto-analyze memory and build a class definition
            return new
            {
                name = $"AutoClass_{address}",
                size,
                address,
                fields = new List<object>(),
            };
        }

        public object ReadVTable(JObject body)
        {
            var address = body.Value<string>("address")!;
            var maxEntries = body.Value<int?>("maxEntries") ?? 50;

            // TODO: Read pointer-sized values from address, validate each points
            // to executable memory, resolve function names via symbols
            return new List<object>();
        }
    }
}
