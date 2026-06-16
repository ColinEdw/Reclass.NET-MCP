from __future__ import annotations

import httpx

from reclass_mcp.types import (
    BridgeStatus,
    ClassDefinition,
    FieldDefinition,
    GameObjectInfo,
    Il2CppClass,
    Il2CppImage,
    Il2CppStringResult,
    MemoryRegion,
    ModuleInfo,
    MonoListInfo,
    PointerChainResult,
    ProcessInfo,
    RawMemory,
    ScanResult,
    TypedValue,
    TypeSuggestion,
    VTableEntry,
)


class BridgeClient:
    """HTTP client that talks to the ReClass.NET bridge plugin."""

    def __init__(self, host: str = "127.0.0.1", port: int = 27015):
        self.base_url = f"http://{host}:{port}"
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def close(self):
        await self._client.aclose()

    async def _get(self, path: str, **params) -> dict:
        r = await self._client.get(path, params={k: v for k, v in params.items() if v is not None})
        r.raise_for_status()
        return r.json()

    async def _post(self, path: str, body: dict | None = None) -> dict:
        r = await self._client.post(path, json=body or {})
        r.raise_for_status()
        return r.json()

    async def _patch(self, path: str, body: dict) -> dict:
        r = await self._client.patch(path, json=body)
        r.raise_for_status()
        return r.json()

    async def _delete(self, path: str) -> dict:
        r = await self._client.delete(path)
        r.raise_for_status()
        return r.json()

    # ── Status ──

    async def get_status(self) -> BridgeStatus:
        return BridgeStatus(**await self._get("/api/status"))

    # ── Process ──

    async def list_processes(self, filter_: str | None = None) -> list[ProcessInfo]:
        data = await self._get("/api/process/list", filter=filter_)
        return [ProcessInfo(**p) for p in data]

    async def attach_process(self, pid: int) -> ProcessInfo:
        return ProcessInfo(**await self._post("/api/process/attach", {"pid": pid}))

    async def detach_process(self) -> None:
        await self._post("/api/process/detach")

    async def get_modules(self) -> list[ModuleInfo]:
        data = await self._get("/api/process/modules")
        return [ModuleInfo(**m) for m in data]

    async def get_memory_regions(self) -> list[MemoryRegion]:
        data = await self._get("/api/process/regions")
        return [MemoryRegion(**r) for r in data]

    # ── Memory ──

    async def read_memory(self, address: str, size: int) -> RawMemory:
        data = await self._post("/api/memory/read", {"address": address, "size": size})
        if "bytes" in data:
            data["bytes_"] = data.pop("bytes")
        return RawMemory(**data)

    async def read_typed(self, address: str, type_: str, length: int | None = None) -> TypedValue:
        return TypedValue(**await self._post("/api/memory/read_typed", {
            "address": address, "type": type_, "length": length,
        }))

    async def write_memory(self, address: str, bytes_: list[int]) -> None:
        await self._post("/api/memory/write", {"address": address, "bytes": bytes_})

    async def write_typed(self, address: str, type_: str, value) -> None:
        await self._post("/api/memory/write_typed", {
            "address": address, "type": type_, "value": value,
        })

    async def scan_memory(
        self, type_: str, value, start: str | None = None,
        end: str | None = None, max_results: int = 100,
    ) -> list[ScanResult]:
        data = await self._post("/api/memory/scan", {
            "type": type_, "value": value,
            "startAddress": start, "endAddress": end, "maxResults": max_results,
        })
        return [ScanResult(**r) for r in data]

    async def resolve_pointer_chain(
        self, base: str, offsets: list[int], final_type: str | None = None,
    ) -> PointerChainResult:
        return PointerChainResult(**await self._post("/api/memory/pointer_chain", {
            "base": base, "offsets": offsets, "finalType": final_type,
        }))

    # ── Classes ──

    async def list_classes(self) -> list[ClassDefinition]:
        data = await self._get("/api/classes")
        return [ClassDefinition(**c) for c in data]

    async def get_class(self, name: str) -> ClassDefinition:
        return ClassDefinition(**await self._get(f"/api/classes/{name}"))

    async def create_class(self, name: str, size: int = 256, address: str | None = None) -> ClassDefinition:
        return ClassDefinition(**await self._post("/api/classes", {
            "name": name, "size": size, "address": address,
        }))

    async def delete_class(self, name: str) -> None:
        await self._delete(f"/api/classes/{name}")

    async def rename_class(self, old_name: str, new_name: str) -> ClassDefinition:
        return ClassDefinition(**await self._post(f"/api/classes/{old_name}/rename", {"newName": new_name}))

    async def add_field(self, class_name: str, field: dict) -> ClassDefinition:
        return ClassDefinition(**await self._post(f"/api/classes/{class_name}/fields", field))

    async def modify_field(self, class_name: str, offset: int, updates: dict) -> ClassDefinition:
        return ClassDefinition(**await self._patch(f"/api/classes/{class_name}/fields/{offset}", updates))

    async def remove_field(self, class_name: str, offset: int) -> ClassDefinition:
        return ClassDefinition(**await self._delete(f"/api/classes/{class_name}/fields/{offset}"))

    # ── Analysis ──

    async def suggest_types(self, address: str, size: int) -> list[TypeSuggestion]:
        data = await self._post("/api/analysis/suggest_types", {"address": address, "size": size})
        return [TypeSuggestion(**s) for s in data]

    async def dissect_memory(self, address: str, size: int) -> ClassDefinition:
        return ClassDefinition(**await self._post("/api/analysis/dissect", {
            "address": address, "size": size,
        }))

    async def read_vtable(self, address: str, max_entries: int = 50) -> list[VTableEntry]:
        data = await self._post("/api/analysis/vtable", {
            "address": address, "maxEntries": max_entries,
        })
        return [VTableEntry(**e) for e in data]

    # ── Export / Import ──

    async def export_class(self, class_name: str, fmt: str) -> dict:
        return await self._post(f"/api/classes/{class_name}/export", {"format": fmt})

    async def import_class(self, fmt: str, content: str) -> ClassDefinition:
        return ClassDefinition(**await self._post("/api/classes/import", {
            "format": fmt, "content": content,
        }))

    # ── IL2CPP / Unity ──

    async def il2cpp_list_images(self) -> list[Il2CppImage]:
        data = await self._get("/api/il2cpp/images")
        return [Il2CppImage(**img) for img in data]

    async def il2cpp_find_class(self, name: str, namespace: str = "") -> list[Il2CppClass]:
        data = await self._post("/api/il2cpp/find_class", {
            "name": name, "namespace": namespace,
        })
        return [Il2CppClass(**c) for c in data]

    async def il2cpp_dump_class(self, address: str) -> Il2CppClass:
        return Il2CppClass(**await self._post("/api/il2cpp/dump_class", {"address": address}))

    async def il2cpp_list_class_fields(self, address: str, read_values: bool = False) -> Il2CppClass:
        return Il2CppClass(**await self._post("/api/il2cpp/class_fields", {
            "address": address, "readValues": read_values,
        }))

    async def il2cpp_list_class_methods(self, address: str) -> Il2CppClass:
        return Il2CppClass(**await self._post("/api/il2cpp/class_methods", {"address": address}))

    async def il2cpp_read_static_fields(self, class_address: str) -> list[dict]:
        return await self._post("/api/il2cpp/static_fields", {"classAddress": class_address})

    async def il2cpp_read_string(self, address: str) -> Il2CppStringResult:
        return Il2CppStringResult(**await self._post("/api/il2cpp/read_string", {"address": address}))

    async def il2cpp_read_list(self, address: str, max_items: int = 50) -> MonoListInfo:
        return MonoListInfo(**await self._post("/api/il2cpp/read_list", {
            "address": address, "maxItems": max_items,
        }))

    async def il2cpp_read_array(self, address: str, element_type: str, max_items: int = 50) -> dict:
        return await self._post("/api/il2cpp/read_array", {
            "address": address, "elementType": element_type, "maxItems": max_items,
        })

    async def il2cpp_get_method_address(self, class_name: str, method_name: str, namespace: str = "") -> dict:
        return await self._post("/api/il2cpp/method_address", {
            "className": class_name, "methodName": method_name, "namespace": namespace,
        })

    async def il2cpp_dump_object(self, address: str, depth: int = 1) -> dict:
        return await self._post("/api/il2cpp/dump_object", {
            "address": address, "depth": depth,
        })

    async def unity_find_gameobjects(self, name_filter: str = "") -> list[GameObjectInfo]:
        data = await self._post("/api/unity/find_gameobjects", {"nameFilter": name_filter})
        return [GameObjectInfo(**go) for go in data]

    async def unity_get_component(self, gameobject_address: str, component_type: str) -> dict:
        return await self._post("/api/unity/get_component", {
            "gameObjectAddress": gameobject_address, "componentType": component_type,
        })

    async def il2cpp_scan_instances(self, class_name: str, namespace: str = "", max_results: int = 50) -> list[dict]:
        return await self._post("/api/il2cpp/scan_instances", {
            "className": class_name, "namespace": namespace, "maxResults": max_results,
        })
