using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using ReClassNET.Plugins;

namespace ReclassMcpBridge.Controllers
{
    public class ClassController
    {
        private readonly IPluginHost _host;

        // In-memory store; a real implementation reads from ReClass.NET's project
        private readonly Dictionary<string, ClassDef> _classes = new();

        public ClassController(IPluginHost host) => _host = host;

        public object List()
        {
            // TODO: Read from _host.CurrentProject.Classes
            return _classes.Values.Select(c => c.ToJson()).ToList();
        }

        public object Get(string name)
        {
            if (!_classes.TryGetValue(name, out var cls))
                throw new System.Exception($"Class '{name}' not found.");
            return cls.ToJson();
        }

        public object Create(JObject body)
        {
            var name = body.Value<string>("name")!;
            var size = body.Value<int?>("size") ?? 256;
            var address = body.Value<string?>("address");

            var cls = new ClassDef { Name = name, Size = size, Address = address };
            _classes[name] = cls;
            return cls.ToJson();
        }

        public object Delete(string name)
        {
            _classes.Remove(name);
            return new { ok = true };
        }

        public object Rename(string oldName, JObject body)
        {
            var newName = body.Value<string>("newName")!;
            if (!_classes.TryGetValue(oldName, out var cls))
                throw new System.Exception($"Class '{oldName}' not found.");
            _classes.Remove(oldName);
            cls.Name = newName;
            _classes[newName] = cls;
            return cls.ToJson();
        }

        public object AddField(string className, JObject body)
        {
            var cls = GetClass(className);
            cls.Fields.Add(new FieldDef
            {
                Offset = body.Value<int>("offset"),
                Name = body.Value<string>("name")!,
                Type = body.Value<string>("type")!,
                Size = body.Value<int>("size"),
                Comment = body.Value<string?>("comment") ?? "",
            });
            cls.Fields.Sort((a, b) => a.Offset.CompareTo(b.Offset));
            return cls.ToJson();
        }

        public object ModifyField(string className, int offset, JObject body)
        {
            var cls = GetClass(className);
            var field = cls.Fields.FirstOrDefault(f => f.Offset == offset)
                ?? throw new System.Exception($"No field at offset 0x{offset:X}.");
            if (body["name"] != null) field.Name = body.Value<string>("name")!;
            if (body["type"] != null) field.Type = body.Value<string>("type")!;
            if (body["size"] != null) field.Size = body.Value<int>("size");
            if (body["comment"] != null) field.Comment = body.Value<string>("comment")!;
            return cls.ToJson();
        }

        public object RemoveField(string className, int offset)
        {
            var cls = GetClass(className);
            cls.Fields.RemoveAll(f => f.Offset == offset);
            return cls.ToJson();
        }

        public object Export(string className, JObject body)
        {
            var cls = GetClass(className);
            var format = body.Value<string>("format")!;

            var content = format switch
            {
                "c_header" => ExportCHeader(cls),
                "csharp" => ExportCSharp(cls),
                "rust" => ExportRust(cls),
                "python_ctypes" => ExportPythonCtypes(cls),
                _ => throw new System.Exception($"Unsupported format: {format}"),
            };

            return new { format, content };
        }

        public object Import(JObject body)
        {
            // TODO: Parse class definition from source code
            throw new System.NotImplementedException("Import not yet implemented.");
        }

        private ClassDef GetClass(string name)
        {
            if (!_classes.TryGetValue(name, out var cls))
                throw new System.Exception($"Class '{name}' not found.");
            return cls;
        }

        private static string ExportCHeader(ClassDef cls)
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"// Size: 0x{cls.Size:X}");
            sb.AppendLine($"struct {cls.Name} {{");
            foreach (var f in cls.Fields)
                sb.AppendLine($"    {f.Type} {f.Name}; // 0x{f.Offset:X4}");
            sb.AppendLine("};");
            return sb.ToString();
        }

        private static string ExportCSharp(ClassDef cls)
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"// Size: 0x{cls.Size:X}");
            sb.AppendLine("[StructLayout(LayoutKind.Explicit)]");
            sb.AppendLine($"public struct {cls.Name} {{");
            foreach (var f in cls.Fields)
            {
                sb.AppendLine($"    [FieldOffset(0x{f.Offset:X4})]");
                sb.AppendLine($"    public {f.Type} {f.Name};");
            }
            sb.AppendLine("}");
            return sb.ToString();
        }

        private static string ExportRust(ClassDef cls)
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"// Size: 0x{cls.Size:X}");
            sb.AppendLine("#[repr(C)]");
            sb.AppendLine($"pub struct {cls.Name} {{");
            foreach (var f in cls.Fields)
                sb.AppendLine($"    pub {f.Name}: {f.Type}, // 0x{f.Offset:X4}");
            sb.AppendLine("}");
            return sb.ToString();
        }

        private static string ExportPythonCtypes(ClassDef cls)
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"# Size: 0x{cls.Size:X}");
            sb.AppendLine($"class {cls.Name}(ctypes.Structure):");
            sb.AppendLine("    _fields_ = [");
            foreach (var f in cls.Fields)
                sb.AppendLine($"        (\"{f.Name}\", ctypes.c_{f.Type}),  # 0x{f.Offset:X4}");
            sb.AppendLine("    ]");
            return sb.ToString();
        }

        private class ClassDef
        {
            public string Name { get; set; } = "";
            public int Size { get; set; }
            public string? Address { get; set; }
            public List<FieldDef> Fields { get; set; } = new();

            public object ToJson() => new
            {
                name = Name,
                size = Size,
                address = Address,
                fields = Fields.Select(f => f.ToJson()).ToList(),
            };
        }

        private class FieldDef
        {
            public int Offset { get; set; }
            public string Name { get; set; } = "";
            public string Type { get; set; } = "";
            public int Size { get; set; }
            public string Comment { get; set; } = "";

            public object ToJson() => new
            {
                offset = Offset,
                name = Name,
                type = Type,
                size = Size,
                comment = Comment,
            };
        }
    }
}
