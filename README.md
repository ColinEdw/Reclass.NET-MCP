# reclass-mcp

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that bridges [**ReClass.NET**](https://github.com/ReClassNET/ReClass.NET) to LLMs like Claude, GPT, and others. Built for **game reverse engineering** — especially **IL2CPP/Unity** titles. Let your AI assistant attach to processes, read memory, dump IL2CPP classes, walk pointer chains, map out game structures, and export definitions — all through natural language.

## Why

Reversing large game structures by hand is tedious. You stare at hex, guess field types, chase pointers, and cross-reference with dumped metadata. This MCP server lets you offload that to an LLM:

- **"Find the PlayerStats class and dump all its fields with live values"**
- **"Walk the pointer chain GameAssembly.dll+0x01A0F0B8 -> 0x10 -> 0xB8 -> 0x28 and read as float"**
- **"Scan for all live instances of EnemyController and show their health fields"**
- **"Read the vtable at this address and tell me which methods are virtual"**
- **"Export the struct as a C header so I can use it in my cheat/mod"**

Works with any IL2CPP Unity game, native C++ games, or really any Windows process.

## Architecture

```
┌─────────────┐       stdio        ┌─────────────────┐       HTTP        ┌──────────────────────┐
│  LLM Client │ <=================> │  reclass-mcp    │ <===============> │  ReClass.NET         │
│  (Claude,   │       MCP          │  (Python)       │    localhost     │  + Bridge Plugin     │
│   GPT, etc) │                    │                 │    :27015        │  (C#)                │
└─────────────┘                    └─────────────────┘                  └──────────────────────┘
```

**Two components:**

1. **Python MCP Server** (`src/reclass_mcp/`) — Speaks MCP over stdio to your LLM client. Translates tool calls into HTTP requests to the bridge.
2. **ReClass.NET Bridge Plugin** ([`plugin/`](plugin/)) — A C# plugin that loads inside ReClass.NET and runs a lightweight HTTP server on `localhost:27015`, exposing process memory, IL2CPP metadata, class definitions, and analysis features as a REST API.

## Dependencies

| Component | Link | Description |
|-----------|------|-------------|
| **ReClass.NET** | [github.com/ReClassNET/ReClass.NET](https://github.com/ReClassNET/ReClass.NET) | Memory structure inspection tool. The bridge plugin loads inside it. Download the latest release from the [Releases page](https://github.com/ReClassNET/ReClass.NET/releases). |
| **ReClass.NET Plugin SDK** | Included in ReClass.NET | Plugins implement `ReClassNET.Plugins.Plugin`. The SDK ships as part of `ReClass.NET.exe` — no separate download needed. See the [ReClass.NET plugin docs](https://github.com/ReClassNET/ReClass.NET/wiki/Plugins) for details. |
| **MCP Protocol** | [modelcontextprotocol.io](https://modelcontextprotocol.io) | The protocol that connects LLM clients to tool servers. |
| **Python MCP SDK** | [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | Official Python SDK for building MCP servers. Installed automatically via `pip`/`uv`. |

## Tools

### Process Management

| Tool | Description |
|------|-------------|
| `list_processes` | List running processes, filter by name (find your game) |
| `attach_process` | Attach to a process by PID |
| `detach_process` | Detach from current process |
| `get_modules` | List loaded DLLs (GameAssembly.dll, UnityPlayer.dll, etc.) |
| `get_memory_regions` | Virtual memory map |
| `status` | Check bridge connection and attached process |

### Memory Operations

| Tool | Description |
|------|-------------|
| `read_memory` | Raw hex dump at an address (up to 4096 bytes) |
| `read_typed` | Read as a specific type (int32, float, pointer, utf8, vec3, etc.) |
| `write_memory` | Write raw bytes to an address |
| `write_typed` | Write a typed value |
| `scan_memory` | Scan for a value across process memory |
| `resolve_pointer_chain` | Walk base + offsets through pointer levels (e.g. `GameAssembly.dll+0x1234 -> 0x10 -> 0x28`) |

### IL2CPP / Unity (Game RE)

| Tool | Description |
|------|-------------|
| `il2cpp_list_images` | List loaded assemblies (Assembly-CSharp, UnityEngine, etc.) |
| `il2cpp_find_class` | Find a class by name/namespace across all assemblies |
| `il2cpp_dump_class` | Full class dump — all fields with offsets, all methods with native addresses |
| `il2cpp_class_fields` | List fields, optionally reading live values from an object instance |
| `il2cpp_class_methods` | List methods with compiled native addresses (for hooking/breakpoints) |
| `il2cpp_static_fields` | Read static field values (singletons, managers, global state) |
| `il2cpp_read_string` | Read a `System.String` (Il2CppString) at an address |
| `il2cpp_read_list` | Read a `List<T>` — count + element addresses from `_items` array |
| `il2cpp_read_array` | Read a managed array (`Il2CppArray`) with typed elements |
| `il2cpp_method_address` | Get the native address of a specific method (for hooking) |
| `il2cpp_dump_object` | Dump a live object instance — resolves type, reads all fields, optionally recurses |
| `il2cpp_scan_instances` | Scan GC heap for all live instances of a class (find players, enemies, items, etc.) |
| `unity_find_gameobjects` | Find GameObjects in the scene by name, get components |
| `unity_get_component` | Read a specific component's fields from a GameObject |

### Struct / Class Management

| Tool | Description |
|------|-------------|
| `list_classes` | List all defined ReClass structs |
| `get_class` | Get full struct with fields |
| `create_class` | Create a new struct definition |
| `delete_class` / `rename_class` | Manage structs |
| `add_field` / `modify_field` / `remove_field` | Edit struct fields at specific offsets |

### Analysis

| Tool | Description |
|------|-------------|
| `suggest_types` | Heuristic type detection for a memory region (pointer? float? string?) |
| `dissect_memory` | Auto-generate a struct from raw memory |
| `read_vtable` | Read a C++ virtual function table |

### Export / Import

| Tool | Description |
|------|-------------|
| `export_class` | Export to C header, C#, Rust, Python ctypes, or ReClass XML |
| `import_class` | Import a struct from source code |

## Installation

### Prerequisites

- **Python 3.11+** — [python.org](https://www.python.org/downloads/)
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip
- **ReClass.NET** — Download from [github.com/ReClassNET/ReClass.NET/releases](https://github.com/ReClassNET/ReClass.NET/releases)
- **.NET 8 SDK** — [dotnet.microsoft.com](https://dotnet.microsoft.com/download/dotnet/8.0) (only needed to build the plugin)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/reclass-mcp.git
cd reclass-mcp
```

### 2. Install the Python MCP server

**With uv (recommended):**

```bash
uv sync
```

**With pip:**

```bash
pip install -e .
```

Verify it runs:

```bash
# Should print the MCP server info and exit
uv run reclass-mcp --help
```

### 3. Build and install the ReClass.NET bridge plugin

The bridge plugin is a C# library ([`plugin/ReclassMcpBridge/`](plugin/ReclassMcpBridge/)) that loads inside [ReClass.NET](https://github.com/ReClassNET/ReClass.NET) as a native plugin. When loaded, it starts a lightweight HTTP server on `localhost:27015` that the Python MCP server connects to. This is what lets the LLM actually read process memory, query IL2CPP metadata, and manipulate class definitions through ReClass.NET's internals.

The plugin uses ReClass.NET's [plugin API](https://github.com/ReClassNET/ReClass.NET/wiki/Plugins) — it implements the `Plugin` base class from `ReClassNET.Plugins` and gets access to `IPluginHost`, which provides process attach/detach, memory read/write, class management, and logging.

#### Step-by-step build

**a) Get the ReClass.NET reference assembly**

The plugin compiles against `ReClass.NET.exe`. Copy it from your ReClass.NET install into a `deps/` folder:

```bash
mkdir deps
copy "C:\Tools\ReClass.NET\ReClass.NET.exe" deps\
```

Or edit the `<HintPath>` in [`plugin/ReclassMcpBridge/ReclassMcpBridge.csproj`](plugin/ReclassMcpBridge/ReclassMcpBridge.csproj) to point at your ReClass.NET install directly:

```xml
<Reference Include="ReClassNET">
  <HintPath>C:\Tools\ReClass.NET\ReClass.NET.exe</HintPath>
  <Private>false</Private>
</Reference>
```

**b) Build the plugin**

```bash
cd plugin
dotnet build -c Release
```

This produces `ReclassMcpBridge.dll` in `plugin/ReclassMcpBridge/bin/Release/net48/`.

**c) Install into ReClass.NET**

Copy the built DLL **and** its Newtonsoft.Json dependency into ReClass.NET's `Plugins` folder:

```bash
copy ReclassMcpBridge\bin\Release\net48\ReclassMcpBridge.dll "C:\Tools\ReClass.NET\x64\Plugins\"
copy ReclassMcpBridge\bin\Release\net48\Newtonsoft.Json.dll "C:\Tools\ReClass.NET\x64\Plugins\"
```

> Use the `x64` folder for 64-bit games (most modern games). Use `x86` only if you need to attach to 32-bit processes.
> If the `Plugins` folder doesn't exist, create it next to `ReClass.NET.exe`.

**d) Launch ReClass.NET as administrator**

ReClass.NET needs admin privileges to read other processes' memory. Right-click `ReClass.NET.exe` and select **Run as administrator**, or from PowerShell:

```powershell
Start-Process -FilePath "C:\Tools\ReClass.NET\x64\ReClass.NET.exe" -Verb RunAs
```

**e) Verify the plugin loads**

1. Go to **Plugins** menu in ReClass.NET — you should see **ReclassMcpBridge** in the list
2. Check the log/output window — you should see:
   ```
   [MCP Bridge] HTTP server listening on port 27015
   ```
3. Test with curl or a browser:
   ```bash
   curl http://127.0.0.1:27015/api/status
   ```
   You should get a JSON response like:
   ```json
   {"connected":true,"reclassVersion":"1.2","attachedProcess":null,"classCount":0}
   ```

#### Plugin configuration

The bridge listens on `127.0.0.1:27015` by default. To change the port, set the `RECLASS_BRIDGE_PORT` environment variable before launching ReClass.NET:

```bash
set RECLASS_BRIDGE_PORT=9090
start ReClass.NET.exe
```

Make sure the MCP server's `RECLASS_BRIDGE_PORT` env var matches.

#### How the bridge plugin works

```
ReClass.NET
├── Loads BridgePlugin.cs on startup
│   └── Starts HttpBridgeServer on port 27015
│       ├── /api/status              → connection info
│       ├── /api/process/*           → ProcessController (attach, detach, modules)
│       ├── /api/memory/*            → MemoryController (read, write, scan, pointer chains)
│       ├── /api/classes/*           → ClassController (struct CRUD, export)
│       ├── /api/analysis/*          → AnalysisController (type detection, vtable)
│       ├── /api/il2cpp/*            → Il2CppController (metadata, classes, objects)
│       └── /api/unity/*             → Il2CppController (GameObjects, components)
```

Each controller translates HTTP requests into calls to ReClass.NET's internal APIs via `IPluginHost`. The controllers have `// TODO` markers where ReClass.NET API calls need to be wired in — the HTTP routing and JSON serialization is complete.

#### Troubleshooting the bridge

| Problem | Fix |
|---------|-----|
| Plugin doesn't appear in ReClass.NET | ReClass.NET has strict plugin requirements: the DLL **must** have `AssemblyProduct` set to exactly `"ReClass.NET Plugin"`, the main class **must** be named `<DllName>Ext` (e.g. `ReclassMcpBridgeExt`), and the namespace **must** match the DLL name. All of this is already set up correctly in this repo — if you rename the DLL, you need to update the class name and namespace to match. |
| Plugin still not showing | Make sure both `ReclassMcpBridge.dll` **and** `Newtonsoft.Json.dll` are in the `Plugins/` folder. A missing dependency causes silent load failure. |
| Can't attach to game processes | Run ReClass.NET **as administrator**. Memory inspection requires elevated privileges. |
| "Address already in use" error | Another process is using port 27015. Set `RECLASS_BRIDGE_PORT` to a different port. |
| `curl` returns "connection refused" | ReClass.NET isn't running, or the plugin failed to load. Check the ReClass.NET log. |
| MCP server can't reach bridge | Make sure `RECLASS_BRIDGE_HOST` and `RECLASS_BRIDGE_PORT` match between the MCP server and the plugin. |

## Setup with LLM Clients

### Claude Code

Add to your project's `.claude/settings.json` or global `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "reclass": {
      "command": "uv",
      "args": ["run", "--directory", "C:/path/to/reclass-mcp", "reclass-mcp"],
      "env": {
        "RECLASS_BRIDGE_HOST": "127.0.0.1",
        "RECLASS_BRIDGE_PORT": "27015"
      }
    }
  }
}
```

Then restart Claude Code. You should see the reclass tools available.

### Claude Desktop

Add to your config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "reclass": {
      "command": "uv",
      "args": ["run", "--directory", "C:/path/to/reclass-mcp", "reclass-mcp"],
      "env": {
        "RECLASS_BRIDGE_HOST": "127.0.0.1",
        "RECLASS_BRIDGE_PORT": "27015"
      }
    }
  }
}
```

### Other MCP Clients (Cursor, Windsurf, etc.)

Any MCP-compatible client works. The server communicates over stdio:

```bash
# With uv
uv run --directory /path/to/reclass-mcp reclass-mcp

# With pip install
reclass-mcp
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RECLASS_BRIDGE_HOST` | `127.0.0.1` | Bridge plugin HTTP host |
| `RECLASS_BRIDGE_PORT` | `27015` | Bridge plugin HTTP port |

## Usage Examples

### IL2CPP Game Reversing

```
> "Attach to the game process and list the loaded assemblies"

> "Find the PlayerController class in Assembly-CSharp"

> "Dump all fields and methods of PlayerController"

> "Read the static fields of GameManager — I need the singleton instance address"

> "Dump the live object at 0x1A2B3C4D — show me health, position, and inventory fields"

> "Scan for all live instances of EnemyAI and show their transform positions"

> "Find the TakeDamage method address on PlayerHealth so I can hook it"

> "Read the List<InventoryItem> at the player's inventory field"
```

### General Memory Reversing

```
> "Read 256 bytes at UnityPlayer.dll+0x1A0F0B8 and suggest what the fields might be"

> "Walk the pointer chain GameAssembly.dll+0x01A0F0B8 -> 0x10 -> 0x28 -> 0x30, read as float"

> "Create a struct called WeaponData, add float damage at 0x10, int32 ammo at 0x14, vec3 spread at 0x18"

> "Scan for float value 100.0 between GameAssembly.dll base and base+0x1000000"

> "Export WeaponData as a C header"

> "Read the vtable at 0x7FF6A1000000 — how many virtual methods does this class have?"
```

## Supported Data Types

| Type | Size | Description |
|------|------|-------------|
| `int8` / `uint8` | 1 | Signed/unsigned byte |
| `int16` / `uint16` | 2 | Short |
| `int32` / `uint32` | 4 | Int |
| `int64` / `uint64` | 8 | Long |
| `float` | 4 | 32-bit float |
| `double` | 8 | 64-bit float |
| `bool` | 1 | Boolean |
| `pointer` | 4/8 | Architecture-dependent pointer |
| `utf8` / `utf16` | varies | Strings (specify length) |
| `hex` | varies | Raw hex bytes |
| `vec2` | 8 | 2D float vector (x, y) |
| `vec3` | 12 | 3D float vector (x, y, z) |
| `vec4` | 16 | 4D float vector (x, y, z, w) |
| `matrix4x4` | 64 | 4x4 float matrix (transforms) |

## Project Structure

```
reclass-mcp/
├── src/reclass_mcp/
│   ├── __init__.py          # Entry point
│   ├── __main__.py          # python -m support
│   ├── server.py            # MCP server — all 35+ tool definitions
│   ├── bridge.py            # HTTP client to ReClass.NET plugin
│   └── types.py             # Pydantic models (IL2CPP, Unity, memory, etc.)
├── plugin/                  # ReClass.NET bridge plugin (C#)
│   ├── ReclassMcpBridge.sln
│   └── ReclassMcpBridge/
│       ├── BridgePlugin.cs          # Plugin entry — ReclassMcpBridgeExt : Plugin
│       ├── HttpBridgeServer.cs      # Embedded HTTP server + route dispatch
│       ├── Properties/
│       │   └── AssemblyInfo.cs      # AssemblyProduct = "ReClass.NET Plugin" (required)
│       ├── Controllers/
│       │   ├── ProcessController.cs # Process attach/detach/modules
│       │   ├── MemoryController.cs  # Read/write/scan/pointer chains
│       │   ├── ClassController.cs   # Struct CRUD + export to C/C#/Rust/Python
│       │   ├── AnalysisController.cs # Type suggestion, dissect, vtable
│       │   └── Il2CppController.cs  # IL2CPP metadata, objects, Unity scene
│       └── Models/
│           ├── MemoryRequest.cs
│           └── ClassDefinition.cs
├── examples/
│   ├── claude_code_settings.json
│   └── claude_desktop_config.json
├── pyproject.toml
├── LICENSE
└── README.md
```

## Development

```bash
# Run the MCP server in dev mode
uv run --directory . reclass-mcp

# Build the plugin
cd plugin && dotnet build

# Test the bridge is reachable (ReClass.NET must be running with the plugin)
curl http://127.0.0.1:27015/api/status
```

## Related Projects

- [**ReClass.NET**](https://github.com/ReClassNET/ReClass.NET) — The memory inspection tool this MCP bridges to. Supports plugins, custom node types, and multiple process engines.
- [**Il2CppDumper**](https://github.com/Perfare/Il2CppDumper) — Offline IL2CPP metadata dumper. Useful for generating `dump.cs` which you can cross-reference alongside this MCP's live inspection.
- [**Il2CppInspector**](https://github.com/djkaty/Il2CppInspector) — Another IL2CPP analysis tool with struct generation. Outputs can be imported via `import_class`.
- [**Cpp2IL**](https://github.com/SamboyCoding/Cpp2IL) — IL2CPP analysis framework. Generates type definitions that complement live memory reading.
- [**MCP Protocol Spec**](https://spec.modelcontextprotocol.io) — The protocol specification this server implements.

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

The C# plugin controllers have `// TODO` comments with detailed IL2CPP struct layouts (offsets for `Il2CppClass`, `Il2CppString`, `List<T>._items`, `Il2CppArray`, object headers, etc.) marking exactly where [ReClass.NET's plugin API](https://github.com/ReClassNET/ReClass.NET/wiki/Plugins) calls need to be wired in. The Python MCP server and HTTP bridge routing are fully functional — the main work remaining is the C# implementation.

Key areas for contribution:
- **IL2CPP metadata parsing** — reading `global-metadata.dat` structures from process memory via `IPluginHost.Process`
- **GC heap scanning** — walking the IL2CPP GC to find live object instances
- **Unity scene traversal** — navigating the GameObject/Component hierarchy in memory
- **Additional export formats** — IDA structs, Ghidra data types, Binary Ninja types

## License

MIT
