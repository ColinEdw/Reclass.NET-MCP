from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from reclass_mcp.bridge import BridgeClient
from reclass_mcp.types import DATA_TYPES, EXPORT_FORMATS

mcp = FastMCP(
    "reclass-mcp",
    description="MCP server for ReClass.NET — inspect process memory, define structs, analyze data layouts",
)

_bridge: BridgeClient | None = None


def get_bridge() -> BridgeClient:
    global _bridge
    if _bridge is None:
        host = os.environ.get("RECLASS_BRIDGE_HOST", "127.0.0.1")
        port = int(os.environ.get("RECLASS_BRIDGE_PORT", "27015"))
        _bridge = BridgeClient(host, port)
    return _bridge


# ═══════════════════════════════════════════════════════════════════
#  Process tools
# ═══════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_processes(filter: str = "") -> str:
    """List running processes visible to ReClass. Optionally filter by name substring."""
    bridge = get_bridge()
    processes = await bridge.list_processes(filter or None)
    if not processes:
        return "No processes found."
    lines = [f"[{p.pid}] {p.name} ({p.architecture}) — {p.path}" for p in processes]
    return "\n".join(lines)


@mcp.tool()
async def attach_process(pid: int) -> str:
    """Attach to a process by PID for memory inspection."""
    bridge = get_bridge()
    info = await bridge.attach_process(pid)
    mod_lines = [f"  {m.name} @ {m.base} (0x{m.size:X} bytes)" for m in info.modules[:15]]
    return f"Attached to {info.name} [{info.pid}] ({info.architecture})\n\nModules:\n" + "\n".join(mod_lines)


@mcp.tool()
async def detach_process() -> str:
    """Detach from the currently attached process."""
    await get_bridge().detach_process()
    return "Detached."


@mcp.tool()
async def get_modules() -> str:
    """List all loaded modules (DLLs) in the attached process."""
    modules = await get_bridge().get_modules()
    if not modules:
        return "No modules loaded."
    lines = [f"{m.name}\n  Base: {m.base}  Size: 0x{m.size:X}\n  Path: {m.path}" for m in modules]
    return "\n\n".join(lines)


@mcp.tool()
async def get_memory_regions() -> str:
    """List virtual memory regions of the attached process."""
    regions = await get_bridge().get_memory_regions()
    lines = [f"{r.address}  0x{r.size:X}  {r.protection}  {r.type}  {r.state}" for r in regions]
    return "\n".join(lines) or "No regions."


# ═══════════════════════════════════════════════════════════════════
#  Memory tools
# ═══════════════════════════════════════════════════════════════════


@mcp.tool()
async def read_memory(address: str, size: int) -> str:
    """Read raw bytes from a memory address. Returns a hex dump with ASCII. Max 4096 bytes."""
    if size < 1 or size > 4096:
        return "Error: size must be 1–4096."
    mem = await get_bridge().read_memory(address, size)
    hex_lines: list[str] = []
    bpl = 16
    for i in range(0, len(mem.bytes_), bpl):
        chunk = mem.bytes_[i : i + bpl]
        addr = int(mem.address, 16) + i
        hx = " ".join(f"{b:02X}" for b in chunk)
        asc = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in chunk)
        hex_lines.append(f"{addr:016X}  {hx:<47}  {asc}")
    return "\n".join(hex_lines)


@mcp.tool()
async def read_typed(address: str, type: str, length: int | None = None) -> str:
    """Read memory at an address interpreted as a specific type.

    Supported types: int8, uint8, int16, uint16, int32, uint32, int64, uint64,
    float, double, bool, pointer, utf8, utf16, hex, vec2, vec3, vec4, matrix4x4.
    Use 'length' for string types (utf8/utf16).
    """
    if type not in DATA_TYPES:
        return f"Error: unknown type '{type}'. Supported: {', '.join(DATA_TYPES)}"
    val = await get_bridge().read_typed(address, type, length)
    return f"Address: {val.address}\nType:    {val.type}\nValue:   {val.value}\nRaw:     {val.raw_hex}"


@mcp.tool()
async def write_memory(address: str, bytes: list[int]) -> str:
    """Write raw bytes to a memory address. Each byte 0–255."""
    await get_bridge().write_memory(address, bytes)
    return f"Wrote {len(bytes)} bytes to {address}."


@mcp.tool()
async def write_typed(address: str, type: str, value: str) -> str:
    """Write a typed value to a memory address."""
    if type not in DATA_TYPES:
        return f"Error: unknown type '{type}'."
    await get_bridge().write_typed(address, type, value)
    return f"Wrote {type} value to {address}."


@mcp.tool()
async def scan_memory(
    type: str,
    value: str,
    start_address: str = "",
    end_address: str = "",
    max_results: int = 100,
) -> str:
    """Scan process memory for a value. Returns matching addresses."""
    if type not in DATA_TYPES:
        return f"Error: unknown type '{type}'."
    results = await get_bridge().scan_memory(
        type, value,
        start_address or None,
        end_address or None,
        max_results,
    )
    if not results:
        return "No matches found."
    lines = []
    for r in results:
        mod = f" ({r.module_name}+{r.module_offset})" if r.module_name else ""
        lines.append(f"{r.address}: {r.value}{mod}")
    return f"Found {len(results)} matches:\n" + "\n".join(lines)


@mcp.tool()
async def resolve_pointer_chain(
    base: str,
    offsets: list[int],
    final_type: str = "",
) -> str:
    """Walk a pointer chain: base -> [base] + offset[0] -> ... -> final.

    'base' can be a hex address or 'module.dll+0x1234' format.
    Essential for reaching nested game/app structures.
    """
    result = await get_bridge().resolve_pointer_chain(
        base, offsets, final_type or None,
    )
    steps = []
    for i, addr in enumerate(result.resolved_addresses):
        suffix = f" + 0x{offsets[i]:X}" if i < len(offsets) else ""
        steps.append(f"  [{i}] {addr}{suffix}")
    text = f"Base: {result.base}\nChain:\n" + "\n".join(steps) + f"\nFinal: {result.final_address}"
    if result.final_value:
        text += f"\nValue ({result.final_value.type}): {result.final_value.value}"
    return text


# ═══════════════════════════════════════════════════════════════════
#  Class / struct tools
# ═══════════════════════════════════════════════════════════════════


def _format_class(c) -> str:
    header = f"class {c.name}  (size: 0x{c.size:X})"
    if c.address:
        header += f"  @ {c.address}"
    if not c.fields:
        return header + "\n  (no fields)"
    lines = [header]
    for f in c.fields:
        comment = f"  // {f.comment}" if f.comment else ""
        val = f"  = {f.value}" if f.value else ""
        lines.append(f"  0x{f.offset:04X}  {f.type:<14} {f.name} ({f.size}B){val}{comment}")
    return "\n".join(lines)


@mcp.tool()
async def list_classes() -> str:
    """List all defined ReClass classes/structures."""
    classes = await get_bridge().list_classes()
    if not classes:
        return "No classes defined."
    lines = [f"{c.name}  (0x{c.size:X} bytes, {len(c.fields)} fields)" for c in classes]
    return "\n".join(lines)


@mcp.tool()
async def get_class(name: str) -> str:
    """Get a class definition with all fields."""
    c = await get_bridge().get_class(name)
    return _format_class(c)


@mcp.tool()
async def create_class(name: str, size: int = 256, address: str = "") -> str:
    """Create a new class/struct definition."""
    c = await get_bridge().create_class(name, size, address or None)
    return _format_class(c)


@mcp.tool()
async def delete_class(name: str) -> str:
    """Delete a class definition."""
    await get_bridge().delete_class(name)
    return f"Deleted class '{name}'."


@mcp.tool()
async def rename_class(old_name: str, new_name: str) -> str:
    """Rename a class."""
    c = await get_bridge().rename_class(old_name, new_name)
    return _format_class(c)


@mcp.tool()
async def add_field(
    class_name: str,
    offset: int,
    name: str,
    type: str,
    size: int,
    comment: str = "",
) -> str:
    """Add a field to a class at the given offset."""
    c = await get_bridge().add_field(class_name, {
        "offset": offset, "name": name, "type": type, "size": size, "comment": comment,
    })
    return _format_class(c)


@mcp.tool()
async def modify_field(
    class_name: str,
    offset: int,
    name: str = "",
    type: str = "",
    size: int = 0,
    comment: str = "",
) -> str:
    """Modify an existing field at the given offset."""
    updates = {}
    if name:
        updates["name"] = name
    if type:
        updates["type"] = type
    if size:
        updates["size"] = size
    if comment:
        updates["comment"] = comment
    if not updates:
        return "Error: provide at least one field to update (name, type, size, comment)."
    c = await get_bridge().modify_field(class_name, offset, updates)
    return _format_class(c)


@mcp.tool()
async def remove_field(class_name: str, offset: int) -> str:
    """Remove a field from a class at the given offset."""
    c = await get_bridge().remove_field(class_name, offset)
    return _format_class(c)


# ═══════════════════════════════════════════════════════════════════
#  Analysis tools
# ═══════════════════════════════════════════════════════════════════


@mcp.tool()
async def suggest_types(address: str, size: int) -> str:
    """Analyze a memory region and suggest likely data types for each offset."""
    suggestions = await get_bridge().suggest_types(address, size)
    if not suggestions:
        return "No type suggestions."
    lines = []
    for s in suggestions:
        lines.append(
            f"  0x{s.offset:04X}  {s.suggested_type:<14} "
            f"confidence={s.confidence:.0%}  value={s.value}  ({s.reason})"
        )
    return f"Type suggestions for {address} ({size} bytes):\n" + "\n".join(lines)


@mcp.tool()
async def dissect_memory(address: str, size: int) -> str:
    """Auto-analyze a memory region and generate a class definition with guessed fields."""
    c = await get_bridge().dissect_memory(address, size)
    return _format_class(c)


@mcp.tool()
async def read_vtable(address: str, max_entries: int = 50) -> str:
    """Read a C++ virtual function table starting at the given address."""
    entries = await get_bridge().read_vtable(address, max_entries)
    if not entries:
        return "No vtable entries found (address may not point to a vtable)."
    lines = [
        f"  [{e.index:3d}] {e.address}  {e.function_name or '(unknown)'}"
        for e in entries
    ]
    return f"VTable at {address} ({len(entries)} entries):\n" + "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  IL2CPP / Unity tools
# ═══════════════════════════════════════════════════════════════════


@mcp.tool()
async def il2cpp_list_images() -> str:
    """List all IL2CPP images (assemblies) loaded in the process.
    Each image corresponds to a .NET assembly (Assembly-CSharp, etc.)."""
    images = await get_bridge().il2cpp_list_images()
    if not images:
        return "No IL2CPP images found. Is this an IL2CPP game? Is GameAssembly.dll loaded?"
    lines = [f"{img.name}  ({img.class_count} classes) @ {img.address}" for img in images]
    return "\n".join(lines)


@mcp.tool()
async def il2cpp_find_class(name: str, namespace: str = "") -> str:
    """Find an IL2CPP class by name. Searches all loaded assemblies.
    Optionally filter by namespace (e.g. 'UnityEngine', 'GameNamespace').
    Returns the class metadata address, instance size, parent, and field/method counts."""
    classes = await get_bridge().il2cpp_find_class(name, namespace)
    if not classes:
        return f"No IL2CPP class found matching '{namespace}.{name}' (or '{name}')."
    lines = []
    for c in classes:
        parent = f" : {c.parent}" if c.parent else ""
        lines.append(
            f"{c.namespace}.{c.name}{parent}\n"
            f"  Class @ {c.address}  InstanceSize: 0x{c.instance_size:X}\n"
            f"  Fields: {len(c.fields)}  Methods: {len(c.methods)}"
        )
    return "\n\n".join(lines)


@mcp.tool()
async def il2cpp_dump_class(address: str) -> str:
    """Dump full IL2CPP class info from its metadata address.
    Shows all fields with offsets, all methods with RVAs.
    Use il2cpp_find_class first to get the class address."""
    c = await get_bridge().il2cpp_dump_class(address)
    parent = f" : {c.parent}" if c.parent else ""
    header = f"{c.namespace}.{c.name}{parent}  (0x{c.instance_size:X} bytes) @ {c.address}"

    field_lines = []
    for f in c.fields:
        static = " [static]" if f.is_static else ""
        val = f" = {f.value}" if f.value else ""
        field_lines.append(f"  0x{f.offset:04X}  {f.type:<20} {f.name}{static}{val}")

    method_lines = []
    for m in c.methods:
        params = ", ".join(m.parameters)
        virt = " [virtual]" if m.is_virtual else ""
        method_lines.append(f"  {m.address}  {m.return_type} {m.name}({params}){virt}")

    text = header
    if field_lines:
        text += "\n\nFields:\n" + "\n".join(field_lines)
    if method_lines:
        text += "\n\nMethods:\n" + "\n".join(method_lines)
    return text


@mcp.tool()
async def il2cpp_class_fields(address: str, read_values: bool = False) -> str:
    """List all fields of an IL2CPP class. If read_values=True and a process is
    attached, also reads current values from a live object instance."""
    c = await get_bridge().il2cpp_list_class_fields(address, read_values)
    if not c.fields:
        return f"No fields for class at {address}."
    lines = []
    for f in c.fields:
        static = " [static]" if f.is_static else ""
        val = f" = {f.value}" if f.value else ""
        lines.append(f"  0x{f.offset:04X}  {f.type:<20} {f.name}{static}{val}")
    return f"{c.namespace}.{c.name} fields:\n" + "\n".join(lines)


@mcp.tool()
async def il2cpp_class_methods(address: str) -> str:
    """List all methods of an IL2CPP class with their compiled addresses.
    Useful for finding function pointers to hook or analyze."""
    c = await get_bridge().il2cpp_list_class_methods(address)
    if not c.methods:
        return f"No methods for class at {address}."
    lines = []
    for m in c.methods:
        params = ", ".join(m.parameters)
        virt = " [virtual]" if m.is_virtual else ""
        lines.append(f"  {m.address}  {m.return_type} {m.name}({params}){virt}")
    return f"{c.namespace}.{c.name} methods:\n" + "\n".join(lines)


@mcp.tool()
async def il2cpp_static_fields(class_address: str) -> str:
    """Read the current values of all static fields for an IL2CPP class.
    Useful for singletons, managers, and global state."""
    fields = await get_bridge().il2cpp_read_static_fields(class_address)
    if not fields:
        return "No static fields or no values readable."
    lines = [f"  {f.get('name', '?')}: {f.get('type', '?')} = {f.get('value', '?')}" for f in fields]
    return "Static fields:\n" + "\n".join(lines)


@mcp.tool()
async def il2cpp_read_string(address: str) -> str:
    """Read a System.String (Il2CppString) at the given address.
    IL2CPP strings have a length at +0x10 and UTF-16 chars at +0x14."""
    s = await get_bridge().il2cpp_read_string(address)
    return f"String @ {s.address}  length={s.length}\nValue: \"{s.value}\""


@mcp.tool()
async def il2cpp_read_list(address: str, max_items: int = 50) -> str:
    """Read a System.Collections.Generic.List<T> at the given address.
    Returns the count and element addresses from the internal _items array."""
    lst = await get_bridge().il2cpp_read_list(address, max_items)
    lines = [f"  [{i}] {addr}" for i, addr in enumerate(lst.items)]
    return (
        f"List<{lst.type_name}> @ {lst.address}  Count: {lst.count}\n"
        + ("\n".join(lines) if lines else "  (empty)")
    )


@mcp.tool()
async def il2cpp_read_array(address: str, element_type: str = "pointer", max_items: int = 50) -> str:
    """Read a managed array (Il2CppArray) at the given address.
    element_type controls how each element is interpreted."""
    result = await get_bridge().il2cpp_read_array(address, element_type, max_items)
    items = result.get("items", [])
    length = result.get("length", 0)
    lines = [f"  [{i}] {v}" for i, v in enumerate(items)]
    return f"Array[{length}] @ {address}  (showing {len(items)}):\n" + "\n".join(lines)


@mcp.tool()
async def il2cpp_method_address(class_name: str, method_name: str, namespace: str = "") -> str:
    """Get the compiled native address of a specific IL2CPP method.
    Useful for setting breakpoints, hooking, or reading the implementation."""
    result = await get_bridge().il2cpp_get_method_address(class_name, method_name, namespace)
    addr = result.get("address", "not found")
    full = f"{namespace}.{class_name}" if namespace else class_name
    return f"{full}::{method_name} @ {addr}"


@mcp.tool()
async def il2cpp_dump_object(address: str, depth: int = 1) -> str:
    """Dump a live IL2CPP object instance at the given address.
    Reads the class pointer, resolves the type, then reads all instance fields.
    depth > 1 follows reference-type fields recursively (careful with large objects)."""
    result = await get_bridge().il2cpp_dump_object(address, depth)
    class_name = result.get("className", "Unknown")
    namespace = result.get("namespace", "")
    fields = result.get("fields", [])
    full = f"{namespace}.{class_name}" if namespace else class_name

    lines = [f"Object @ {address} — {full}"]
    for f in fields:
        indent = "  " * f.get("depth", 1)
        lines.append(f"{indent}0x{f.get('offset', 0):04X}  {f.get('type', '?'):<20} {f.get('name', '?')} = {f.get('value', '?')}")
    return "\n".join(lines)


@mcp.tool()
async def il2cpp_scan_instances(class_name: str, namespace: str = "", max_results: int = 50) -> str:
    """Scan the GC heap for live instances of an IL2CPP class.
    Finds all objects of the given type currently in memory.
    Useful for finding player objects, enemy lists, item arrays, etc."""
    results = await get_bridge().il2cpp_scan_instances(class_name, namespace, max_results)
    if not results:
        return f"No live instances of '{class_name}' found."
    lines = [f"  {r.get('address', '?')}  {r.get('preview', '')}" for r in results]
    return f"Found {len(results)} instances of {class_name}:\n" + "\n".join(lines)


@mcp.tool()
async def unity_find_gameobjects(name_filter: str = "") -> str:
    """Find Unity GameObjects in the scene. Optionally filter by name.
    Returns addresses, names, active state, and attached components."""
    gos = await get_bridge().unity_find_gameobjects(name_filter)
    if not gos:
        return "No GameObjects found."
    lines = []
    for go in gos:
        active = "active" if go.active else "inactive"
        comps = ", ".join(go.components[:5])
        if len(go.components) > 5:
            comps += f" (+{len(go.components) - 5} more)"
        lines.append(f"  {go.address}  {go.name}  [{active}]  tag={go.tag or 'Untagged'}\n    Components: {comps}")
    return f"GameObjects ({len(gos)}):\n" + "\n".join(lines)


@mcp.tool()
async def unity_get_component(gameobject_address: str, component_type: str) -> str:
    """Get a specific component from a Unity GameObject.
    Returns the component's address and its field values."""
    result = await get_bridge().unity_get_component(gameobject_address, component_type)
    addr = result.get("address", "not found")
    fields = result.get("fields", [])
    lines = [f"Component {component_type} @ {addr}"]
    for f in fields:
        lines.append(f"  0x{f.get('offset', 0):04X}  {f.get('type', '?'):<20} {f.get('name', '?')} = {f.get('value', '?')}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  Export / import tools
# ═══════════════════════════════════════════════════════════════════


@mcp.tool()
async def export_class(class_name: str, format: str) -> str:
    """Export a class definition.

    Formats: c_header, csharp, rust, python_ctypes, reclass_xml
    """
    if format not in EXPORT_FORMATS:
        return f"Error: unknown format '{format}'. Supported: {', '.join(EXPORT_FORMATS)}"
    result = await get_bridge().export_class(class_name, format)
    return result.get("content", str(result))


@mcp.tool()
async def import_class(format: str, content: str) -> str:
    """Import a class definition from source code or XML."""
    if format not in EXPORT_FORMATS:
        return f"Error: unknown format '{format}'."
    c = await get_bridge().import_class(format, content)
    return _format_class(c)


# ═══════════════════════════════════════════════════════════════════
#  Status
# ═══════════════════════════════════════════════════════════════════


@mcp.tool()
async def status() -> str:
    """Check connection status to the ReClass.NET bridge plugin."""
    try:
        s = await get_bridge().get_status()
    except Exception as e:
        return (
            f"Cannot reach ReClass.NET bridge at {get_bridge().base_url}\n"
            f"Error: {e}\n\n"
            "Make sure ReClass.NET is running with the ReclassMcpBridge plugin loaded."
        )
    text = f"Bridge: connected\nReClass.NET: {s.reclass_version or 'unknown'}\nClasses: {s.class_count}"
    if s.attached_process:
        text += f"\nAttached: {s.attached_process.name} [{s.attached_process.pid}]"
    else:
        text += "\nAttached: (none)"
    return text
