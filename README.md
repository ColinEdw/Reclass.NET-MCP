# reclass-mcp

[MCP](https://modelcontextprotocol.io) server that bridges [ReClass.NET](https://github.com/ReClassNET/ReClass.NET) to LLMs. Built for game RE — especially IL2CPP/Unity. Attach to processes, read memory, dump IL2CPP classes, walk pointer chains, and export struct definitions through natural language.

```
LLM Client  ←— MCP (stdio) —→  reclass-mcp (Python)  ←— HTTP :27015 —→  ReClass.NET + Bridge Plugin (C#)
```

## Tools

### Process
| Tool | Description |
|------|-------------|
| `list_processes` | List/filter running processes |
| `attach_process` | Attach by PID |
| `detach_process` | Detach |
| `get_modules` | Loaded DLLs |
| `get_memory_regions` | Virtual memory map |

### Memory
| Tool | Description |
|------|-------------|
| `read_memory` | Hex dump (up to 4096 bytes) |
| `read_typed` | Read as int32, float, pointer, utf8, vec3, etc. |
| `write_memory` / `write_typed` | Write raw bytes or typed values |
| `scan_memory` | Scan for a value |
| `resolve_pointer_chain` | Walk base + offsets (e.g. `GameAssembly.dll+0x1234 -> 0x10 -> 0x28`) |

### IL2CPP / Unity
| Tool | Description |
|------|-------------|
| `il2cpp_list_images` | Loaded assemblies (Assembly-CSharp, etc.) |
| `il2cpp_find_class` | Find class by name/namespace |
| `il2cpp_dump_class` | All fields with offsets + methods with native addresses |
| `il2cpp_class_fields` / `il2cpp_class_methods` | List fields or methods separately |
| `il2cpp_static_fields` | Read static field values (singletons, managers) |
| `il2cpp_read_string` | Read System.String |
| `il2cpp_read_list` / `il2cpp_read_array` | Read List\<T\> or managed arrays |
| `il2cpp_method_address` | Get native address for hooking |
| `il2cpp_dump_object` | Dump live object — resolve type, read all fields |
| `il2cpp_scan_instances` | Scan GC heap for all instances of a class |
| `unity_find_gameobjects` | Find GameObjects by name |
| `unity_get_component` | Read component fields |

### Structs
| Tool | Description |
|------|-------------|
| `list_classes` / `get_class` | List or get struct definitions |
| `create_class` / `delete_class` / `rename_class` | Manage structs |
| `add_field` / `modify_field` / `remove_field` | Edit fields |
| `export_class` | Export to C header, C#, Rust, Python ctypes, ReClass XML |
| `import_class` | Import from source |

### Analysis
| Tool | Description |
|------|-------------|
| `suggest_types` | Heuristic type detection |
| `dissect_memory` | Auto-generate struct from raw memory |
| `read_vtable` | Read C++ virtual function table |

## Installation

### Prerequisites

- Python 3.11+ / [uv](https://docs.astral.sh/uv/)
- [ReClass.NET](https://github.com/ReClassNET/ReClass.NET/releases)
- .NET SDK (to build the plugin)

### 1. Install the MCP server

```bash
git clone https://github.com/ColinEdw/Reclass.NET-MCP.git
cd Reclass.NET-MCP
uv sync          # or: pip install -e .
```

### 2. Build the bridge plugin

```bash
mkdir deps
copy "C:\path\to\ReClass.NET\x64\ReClass.NET.exe" deps\
cd plugin
dotnet build -c Release
```

### 3. Install the plugin into ReClass.NET

Copy **both** DLLs to the Plugins folder:

```bash
copy ReclassMcpBridge\bin\Release\net48\ReclassMcpBridge.dll "C:\path\to\ReClass.NET\x64\Plugins\"
copy ReclassMcpBridge\bin\Release\net48\Newtonsoft.Json.dll "C:\path\to\ReClass.NET\x64\Plugins\"
```

### 4. Launch ReClass.NET as admin

```powershell
Start-Process -FilePath "C:\path\to\ReClass.NET\x64\ReClass.NET.exe" -Verb RunAs
```

Verify: go to **Plugins** menu — you should see **ReclassMcpBridge**. Test with:

```bash
curl http://127.0.0.1:27015/api/status
```

## Setup with LLM Clients

Add to your MCP config (Claude Code, Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "reclass": {
      "command": "uv",
      "args": ["run", "--directory", "C:/path/to/Reclass.NET-MCP", "reclass-mcp"],
      "env": {
        "RECLASS_BRIDGE_HOST": "127.0.0.1",
        "RECLASS_BRIDGE_PORT": "27015"
      }
    }
  }
}
```

**Claude Code:** `.claude/settings.json` or `~/.claude/settings.json`
**Claude Desktop:** `%APPDATA%\Claude\claude_desktop_config.json`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Plugin not showing | Make sure both `ReclassMcpBridge.dll` **and** `Newtonsoft.Json.dll` are in `Plugins/`. If you rename the DLL, the class name must be `<DllName>Ext` and `AssemblyProduct` must be `"ReClass.NET Plugin"`. |
| Can't attach to processes | Run ReClass.NET **as administrator**. |
| Connection refused on :27015 | ReClass.NET isn't running or plugin didn't load. |
| Port conflict | Set `RECLASS_BRIDGE_PORT` env var to a different port (both ReClass.NET and MCP server). |

## Related Projects

- [ReClass.NET](https://github.com/ReClassNET/ReClass.NET) — Memory inspection tool
- [Il2CppDumper](https://github.com/Perfare/Il2CppDumper) — Offline IL2CPP metadata dumper
- [Cpp2IL](https://github.com/SamboyCoding/Cpp2IL) — IL2CPP analysis framework

## License

MIT
