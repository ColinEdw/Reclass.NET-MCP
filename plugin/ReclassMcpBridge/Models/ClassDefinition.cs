using System.Collections.Generic;

namespace ReclassMcpBridge.Models
{
    public class ClassCreateRequest
    {
        public string Name { get; set; } = "";
        public int Size { get; set; } = 256;
        public string? Address { get; set; }
    }

    public class FieldRequest
    {
        public int Offset { get; set; }
        public string Name { get; set; } = "";
        public string Type { get; set; } = "";
        public int Size { get; set; }
        public string Comment { get; set; } = "";
    }

    public class ExportRequest
    {
        public string Format { get; set; } = "c_header";
    }

    public class ImportRequest
    {
        public string Format { get; set; } = "c_header";
        public string Content { get; set; } = "";
    }
}
