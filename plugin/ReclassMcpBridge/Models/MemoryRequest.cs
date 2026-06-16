namespace ReclassMcpBridge.Models
{
    public class MemoryReadRequest
    {
        public string Address { get; set; } = "";
        public int Size { get; set; }
    }

    public class MemoryWriteRequest
    {
        public string Address { get; set; } = "";
        public byte[] Bytes { get; set; } = System.Array.Empty<byte>();
    }

    public class TypedReadRequest
    {
        public string Address { get; set; } = "";
        public string Type { get; set; } = "";
        public int? Length { get; set; }
    }

    public class ScanRequest
    {
        public string Type { get; set; } = "";
        public string Value { get; set; } = "";
        public string? StartAddress { get; set; }
        public string? EndAddress { get; set; }
        public int MaxResults { get; set; } = 100;
    }

    public class PointerChainRequest
    {
        public string Base { get; set; } = "";
        public int[] Offsets { get; set; } = System.Array.Empty<int>();
        public string? FinalType { get; set; }
    }
}
