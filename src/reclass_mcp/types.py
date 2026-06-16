from __future__ import annotations
from pydantic import BaseModel


class ProcessInfo(BaseModel):
    pid: int
    name: str
    path: str
    architecture: str
    modules: list[ModuleInfo] = []


class ModuleInfo(BaseModel):
    name: str
    base: str
    size: int
    path: str


class MemoryRegion(BaseModel):
    address: str
    size: int
    protection: str
    type: str
    state: str


class RawMemory(BaseModel):
    address: str
    hex: str
    ascii: str
    bytes_: list[int] = []

    class Config:
        populate_by_name = True


class TypedValue(BaseModel):
    address: str
    type: str
    value: str | int | float | bool
    raw_hex: str


class FieldDefinition(BaseModel):
    offset: int
    name: str
    type: str
    size: int
    comment: str = ""
    value: str | None = None


class ClassDefinition(BaseModel):
    name: str
    size: int
    address: str | None = None
    fields: list[FieldDefinition] = []


class PointerChainResult(BaseModel):
    base: str
    offsets: list[int]
    resolved_addresses: list[str]
    final_address: str
    final_value: TypedValue | None = None


class ScanResult(BaseModel):
    address: str
    value: str
    module_name: str | None = None
    module_offset: str | None = None


class TypeSuggestion(BaseModel):
    offset: int
    suggested_type: str
    confidence: float
    reason: str
    value: str


class VTableEntry(BaseModel):
    index: int
    address: str
    function_name: str | None = None


class Il2CppClass(BaseModel):
    name: str
    namespace: str
    parent: str | None = None
    address: str
    static_fields_address: str | None = None
    instance_size: int
    fields: list[Il2CppField] = []
    methods: list[Il2CppMethod] = []


class Il2CppField(BaseModel):
    name: str
    type: str
    offset: int
    is_static: bool = False
    value: str | None = None


class Il2CppMethod(BaseModel):
    name: str
    address: str
    return_type: str
    parameters: list[str] = []
    is_virtual: bool = False


class Il2CppImage(BaseModel):
    name: str
    class_count: int
    address: str


class Il2CppStringResult(BaseModel):
    address: str
    length: int
    value: str


class GameObjectInfo(BaseModel):
    address: str
    name: str
    tag: str | None = None
    layer: int = 0
    active: bool = True
    components: list[str] = []


class MonoListInfo(BaseModel):
    address: str
    type_name: str
    count: int
    items: list[str] = []


class BridgeStatus(BaseModel):
    connected: bool
    reclass_version: str | None = None
    attached_process: ProcessInfo | None = None
    class_count: int = 0


DATA_TYPES = [
    "int8", "uint8", "int16", "uint16",
    "int32", "uint32", "int64", "uint64",
    "float", "double",
    "bool", "pointer",
    "utf8", "utf16", "hex",
    "vec2", "vec3", "vec4", "matrix4x4",
]

EXPORT_FORMATS = ["c_header", "csharp", "rust", "python_ctypes", "reclass_xml"]
