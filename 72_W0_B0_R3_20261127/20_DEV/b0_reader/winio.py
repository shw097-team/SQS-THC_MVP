"""Windows same-handle I/O and file identity using ctypes only.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass
from typing import Any

if os.name != "nt":  # pragma: no cover - the bounded target is Windows.
    raise RuntimeError("winio requires Windows")

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
FILE_ATTRIBUTE_DIRECTORY = 0x00000010
FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
ERROR_ACCESS_DENIED = 5
ERROR_SHARING_VIOLATION = 32
ERROR_LOCK_VIOLATION = 33
ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3
ERROR_INVALID_NAME = 123
ERROR_INVALID_PARAMETER = 87
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
TOKEN_QUERY = 0x0008
TokenUser = 1


class HANDLE(wintypes.HANDLE):
    pass


class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


class FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
    _fields_ = [
        ("FileAttributes", wintypes.DWORD),
        ("ReparseTag", wintypes.DWORD),
    ]


class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Sid", ctypes.c_void_p),
        ("Attributes", wintypes.DWORD),
    ]


class TOKEN_USER(ctypes.Structure):
    _fields_ = [("User", SID_AND_ATTRIBUTES)]


_kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    HANDLE,
]
_kernel32.CreateFileW.restype = HANDLE
_kernel32.CloseHandle.argtypes = [HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL
_kernel32.GetFinalPathNameByHandleW.argtypes = [
    HANDLE,
    wintypes.LPWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
]
_kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
_kernel32.GetFileInformationByHandle.argtypes = [
    HANDLE,
    ctypes.POINTER(BY_HANDLE_FILE_INFORMATION),
]
_kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
_kernel32.GetFileInformationByHandleEx.argtypes = [
    HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD,
]
_kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
_kernel32.SetFilePointerEx.argtypes = [
    HANDLE,
    ctypes.c_longlong,
    ctypes.POINTER(ctypes.c_longlong),
    wintypes.DWORD,
]
_kernel32.SetFilePointerEx.restype = wintypes.BOOL
_kernel32.ReadFile.argtypes = [
    HANDLE,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
_kernel32.ReadFile.restype = wintypes.BOOL
_kernel32.GetCurrentProcess.restype = HANDLE
_advapi32.OpenProcessToken.argtypes = [
    HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(HANDLE),
]
_advapi32.OpenProcessToken.restype = wintypes.BOOL
_advapi32.GetTokenInformation.argtypes = [
    HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
_advapi32.GetTokenInformation.restype = wintypes.BOOL
_advapi32.LookupAccountSidW.argtypes = [
    wintypes.LPCWSTR,
    ctypes.c_void_p,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(ctypes.c_int),
]
_advapi32.LookupAccountSidW.restype = wintypes.BOOL


@dataclass(frozen=True, slots=True)
class FileIdentity:
    volume_serial: int
    file_index_high: int
    file_index_low: int
    size: int
    attributes: int
    final_path: str

    @property
    def tuple(self) -> tuple[int, int, int]:
        return (self.volume_serial, self.file_index_high, self.file_index_low)

    @property
    def is_directory(self) -> bool:
        return bool(self.attributes & FILE_ATTRIBUTE_DIRECTORY)

    @property
    def is_reparse(self) -> bool:
        return bool(self.attributes & FILE_ATTRIBUTE_REPARSE_POINT)

    @property
    def is_regular_file(self) -> bool:
        return not self.is_directory and not self.is_reparse


class WinIOError(OSError):
    def __init__(self, message: str, winerror: int) -> None:
        super().__init__(winerror, message)
        self.winerror = winerror


def _windows_path(path: str) -> str:
    normal = os.path.abspath(path)
    if normal.startswith("\\\\?\\"):
        return normal
    return "\\\\?\\" + normal


def _normal_final_path(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


class WinHandle:
    """Owned Windows handle; reads always use this exact handle."""

    __slots__ = ("_handle", "_closed", "path")

    def __init__(self, handle: int | HANDLE, path: str) -> None:
        if isinstance(handle, HANDLE):
            handle = handle.value
        self._handle = HANDLE(handle)
        self._closed = False
        self.path = path

    @classmethod
    def open(
        cls,
        path: str,
        *,
        directory: bool = False,
    ) -> "WinHandle":
        raw_handle = _kernel32.CreateFileW(
            _windows_path(path),
            GENERIC_READ,
            FILE_SHARE_READ,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            None,
        )
        raw_value = None if raw_handle is None else raw_handle.value
        if raw_value in (None, 0, INVALID_HANDLE_VALUE):
            error = ctypes.get_last_error()
            raise WinIOError("CreateFileW failed", error)
        handle = cls(raw_handle, path)
        try:
            identity = handle.identity()
            if directory and not identity.is_directory:
                raise WinIOError("expected directory", ERROR_INVALID_PARAMETER)
            if not directory and not identity.is_regular_file:
                raise WinIOError("expected regular file", ERROR_INVALID_PARAMETER)
        except BaseException:
            handle.close()
            raise
        return handle

    def close(self) -> None:
        if not self._closed and self._handle.value not in (
            None,
            0,
            INVALID_HANDLE_VALUE,
        ):
            _kernel32.CloseHandle(self._handle)
        self._closed = True
        self._handle = HANDLE(INVALID_HANDLE_VALUE)

    def __enter__(self) -> "WinHandle":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def final_path(self) -> str:
        size = 512
        while size <= 32768:
            buffer = ctypes.create_unicode_buffer(size)
            length = _kernel32.GetFinalPathNameByHandleW(
                self._handle, buffer, size, 0
            )
            if length == 0:
                raise WinIOError(
                    "GetFinalPathNameByHandleW failed", ctypes.get_last_error()
                )
            if length < size:
                return _normal_final_path(buffer.value)
            size = length + 1
        raise WinIOError(
            "GetFinalPathNameByHandleW path too long", ERROR_INVALID_PARAMETER
        )

    def identity(self) -> FileIdentity:
        info = BY_HANDLE_FILE_INFORMATION()
        if not _kernel32.GetFileInformationByHandle(
            self._handle, ctypes.byref(info)
        ):
            raise WinIOError(
                "GetFileInformationByHandle failed", ctypes.get_last_error()
            )
        tag = FILE_ATTRIBUTE_TAG_INFO()
        if not _kernel32.GetFileInformationByHandleEx(
            self._handle,
            FILE_ATTRIBUTE_TAG_INFO_CLASS,
            ctypes.byref(tag),
            ctypes.sizeof(tag),
        ):
            raise WinIOError(
                "GetFileInformationByHandleEx failed", ctypes.get_last_error()
            )
        size = (int(info.nFileSizeHigh) << 32) | int(info.nFileSizeLow)
        return FileIdentity(
            volume_serial=int(info.dwVolumeSerialNumber),
            file_index_high=int(info.nFileIndexHigh),
            file_index_low=int(info.nFileIndexLow),
            size=size,
            attributes=int(tag.FileAttributes),
            final_path=self.final_path(),
        )

    def is_reparse(self) -> bool:
        tag = FILE_ATTRIBUTE_TAG_INFO()
        if not _kernel32.GetFileInformationByHandleEx(
            self._handle,
            FILE_ATTRIBUTE_TAG_INFO_CLASS,
            ctypes.byref(tag),
            ctypes.sizeof(tag),
        ):
            raise WinIOError(
                "GetFileInformationByHandleEx failed", ctypes.get_last_error()
            )
        return bool(tag.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)

    def read_all(self) -> bytes:
        before = self.identity()
        if not before.is_regular_file:
            raise WinIOError("not a regular file", ERROR_INVALID_PARAMETER)
        current = ctypes.c_longlong()
        if not _kernel32.SetFilePointerEx(
            self._handle, 0, ctypes.byref(current), 0
        ):
            raise WinIOError("SetFilePointerEx failed", ctypes.get_last_error())
        remaining = before.size
        chunks: list[bytes] = []
        while remaining:
            amount = min(remaining, 1024 * 1024)
            buffer = ctypes.create_string_buffer(amount)
            read = wintypes.DWORD()
            if not _kernel32.ReadFile(
                self._handle,
                buffer,
                amount,
                ctypes.byref(read),
                None,
            ):
                raise WinIOError("ReadFile failed", ctypes.get_last_error())
            if read.value == 0:
                raise WinIOError(
                    "ReadFile made no progress", ERROR_INVALID_PARAMETER
                )
            chunks.append(buffer.raw[: read.value])
            remaining -= read.value
        after = self.identity()
        if (
            before.tuple != after.tuple
            or before.size != after.size
            or sum(len(chunk) for chunk in chunks) != after.size
        ):
            raise WinIOError("file changed during read", ERROR_SHARING_VIOLATION)
        return b"".join(chunks)


def current_principal() -> str:
    process_token = HANDLE()
    if not _advapi32.OpenProcessToken(
        _kernel32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(process_token)
    ):
        raise WinIOError("OpenProcessToken failed", ctypes.get_last_error())
    try:
        needed = wintypes.DWORD()
        _advapi32.GetTokenInformation(
            process_token, TokenUser, None, 0, ctypes.byref(needed)
        )
        buffer = ctypes.create_string_buffer(needed.value)
        if not _advapi32.GetTokenInformation(
            process_token,
            TokenUser,
            buffer,
            needed.value,
            ctypes.byref(needed),
        ):
            raise WinIOError(
                "GetTokenInformation failed", ctypes.get_last_error()
            )
        token_user = ctypes.cast(buffer, ctypes.POINTER(TOKEN_USER)).contents
        name_size = wintypes.DWORD(256)
        domain_size = wintypes.DWORD(256)
        sid_type = ctypes.c_int()
        name = ctypes.create_unicode_buffer(name_size.value)
        domain = ctypes.create_unicode_buffer(domain_size.value)
        if not _advapi32.LookupAccountSidW(
            None,
            token_user.User.Sid,
            name,
            ctypes.byref(name_size),
            domain,
            ctypes.byref(domain_size),
            ctypes.byref(sid_type),
        ):
            raise WinIOError("LookupAccountSidW failed", ctypes.get_last_error())
        return f"{domain.value}\\{name.value}" if domain.value else name.value
    finally:
        _kernel32.CloseHandle(process_token)


def read_optional_file(path: str) -> bytes | None:
    """Read an evidence file through one handle; missing means unknown."""

    try:
        with WinHandle.open(path) as handle:
            return handle.read_all()
    except WinIOError as exc:
        if exc.winerror in (ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND):
            return None
        raise


def map_open_error(error: OSError) -> str:
    code = getattr(error, "winerror", None)
    if code == ERROR_ACCESS_DENIED:
        return "RIGHTS_DENIED"
    if code in (ERROR_SHARING_VIOLATION, ERROR_LOCK_VIOLATION):
        return "SOURCE_UNAVAILABLE"
    if code in (ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND):
        return "PATH_IDENTITY_UNVERIFIED"
    if code in (ERROR_INVALID_NAME, ERROR_INVALID_PARAMETER):
        return "PATH_INVALID"
    return "PATH_IDENTITY_UNVERIFIED"
