"""Bootstrap grant matching and atomic at-most-once consumption for pipeline-topology."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

import yaml

VALID_BOOTSTRAP_GRANT_INVOCATIONS = (
    'orchestrator_pre_route',
    'ship_pre_branch',
    'ship_pre_claim',
)
_BOOTSTRAP_GRANT_PHASE = 'pre_claim'
_SHIPMENT_ID_PATTERN = re.compile(r'^\d+(?:\.\d+)*-[A-Z]+$')
_DRIVE_PREFIX_PATTERN = re.compile(r'^[A-Za-z]:')
_UNC_PREFIXES = ('\\\\', '//')
_BOOTSTRAP_GRANTS_ROOT = Path('.autoharness') / 'bootstrap-grants'
_CONSUMPTION_ROOT = Path('.autoharness') / 'gates' / 'bootstrap-grant-consumption'
_REPARSE_POINT_ATTRIBUTE = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
_UNKNOWN_RECORD_ERROR = 'record schema is malformed or unsupported'


def _is_reparse_point(stat_result: os.stat_result) -> bool:
    """Return True only when the stat result actually carries Windows file
    attributes and the reparse-point bit is set.

    ``stat.FILE_ATTRIBUTE_REPARSE_POINT`` is exposed as a plain integer
    constant by CPython's ``stat`` module on every platform (it is not
    gated to Windows), so ``_REPARSE_POINT_ATTRIBUTE`` is truthy even on
    POSIX. The ``st_file_attributes`` attribute on ``os.stat_result`` is
    the part that is genuinely Windows-only; probe for it explicitly
    instead of assuming its presence, so shared code paths reached from
    both ``_claim_record_posix`` and ``_claim_record_windows`` (for
    example ``_scan_existing_records``) do not raise ``AttributeError``
    on POSIX.
    """
    if not _REPARSE_POINT_ATTRIBUTE:
        return False
    attributes = getattr(stat_result, 'st_file_attributes', None)
    if attributes is None:
        return False
    return bool(attributes & _REPARSE_POINT_ATTRIBUTE)


def _read_bytes_no_follow(path: Path) -> bytes:
    """Read a file's bytes without transparently following a symlink or
    reparse point at the final path component, failing closed instead of
    reading through it to an unexpected external file.

    On platforms exposing ``os.O_NOFOLLOW`` (POSIX), the open itself
    refuses to traverse a final-component symlink, so the check and the
    read are atomic. Windows' ``os`` module does not expose
    ``O_NOFOLLOW``, so the fallback there verifies via ``os.lstat`` (both
    the Windows reparse-point bit and the POSIX-style ``st_mode`` symlink
    bit, since a Windows Python build's ``lstat`` can in principle report
    either) immediately before a pathname-based read, matching the
    verify-then-open convention already used for directory traversal
    elsewhere in this module (for example ``_windows_open_directory_handle``).
    """
    if hasattr(os, 'O_NOFOLLOW'):
        flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, 'O_BINARY'):
            flags |= os.O_BINARY
        fd = os.open(path, flags)
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            return b''.join(chunks)
        finally:
            os.close(fd)
    stat_result = os.lstat(path)
    if _is_reparse_point(stat_result) or stat.S_ISLNK(stat_result.st_mode):
        raise OSError(f'{path} is a symlink/reparse point and cannot be read')
    return path.read_bytes()


def _read_bytes_no_follow_walked(
    workspace: Path, relative_dir_components: tuple[str, ...], filename: str
) -> bytes:
    """Read ``workspace/<relative_dir_components>/<filename>`` after
    verifying every directory component -- not just the final file -- is
    not a symlink/reparse point.

    ``_read_bytes_no_follow`` only protects the final path component: a
    symlinked intermediate directory (for example a swapped
    ``.autoharness`` or ``bootstrap-grants`` component) would still be
    followed before the final-component check ever runs, letting a crafted
    workspace redirect the read to an arbitrary external file. This walks
    every directory component relative to a workspace-rooted descriptor
    with ``O_NOFOLLOW`` (POSIX) -- mirroring ``append_no_follow`` /
    ``_claim_record_posix`` -- or verifies each component via ``os.lstat``
    plus a held-open directory handle (Windows), before opening the final
    file with the same no-follow discipline as ``_read_bytes_no_follow``.

    Raises ``FileNotFoundError`` if any directory component or the target
    file does not exist (the caller treats this as "no grant present", not
    a containment violation). Raises ``OSError``/``ValueError`` on any
    symlink/reparse-point containment violation or unsupported platform;
    callers must fail closed rather than falling back to an unprotected
    pathname-based read.
    """
    resolved_workspace = Path(workspace).resolve()

    if _supports_posix_claim_strategy():
        flags_dir = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
        root_fd = os.open(str(resolved_workspace), flags_dir)
        opened_fds = [root_fd]
        current_fd = root_fd
        try:
            for component in relative_dir_components:
                next_fd = os.open(component, flags_dir | os.O_NOFOLLOW, dir_fd=current_fd)
                opened_fds.append(next_fd)
                current_fd = next_fd
            flags_file = os.O_RDONLY | os.O_NOFOLLOW
            if hasattr(os, 'O_BINARY'):
                flags_file |= os.O_BINARY
            file_fd = os.open(filename, flags_file, dir_fd=current_fd)
            try:
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(file_fd, 65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                return b''.join(chunks)
            finally:
                os.close(file_fd)
        finally:
            for fd in reversed(opened_fds):
                os.close(fd)

    if not _supports_windows_claim_strategy():
        raise OSError(
            'no-follow walked-read strategy is unavailable on this platform; refusing to fall '
            'back to an unprotected pathname-based read'
        )

    handles: list[tuple[Any, Any]] = []
    partial = resolved_workspace
    try:
        for component in relative_dir_components:
            partial = partial / component
            stat_result = os.lstat(partial)
            if _is_reparse_point(stat_result):
                raise ValueError(f'path component {partial} is a reparse point and cannot be used')
            kernel32, handle = _windows_open_directory_handle(partial)
            handles.append((kernel32, handle))
        file_path = partial / filename
        stat_result = os.lstat(file_path)
        if _is_reparse_point(stat_result) or stat.S_ISLNK(stat_result.st_mode):
            raise OSError(f'{file_path} is a symlink/reparse point and cannot be read')
        return file_path.read_bytes()
    finally:
        for kernel32, handle in reversed(handles):
            _windows_close_handle(kernel32, handle)


class BootstrapGrantArgumentError(ValueError):
    """Raised when bootstrap-grant CLI inputs are syntactically unsafe."""


@dataclass(frozen=True)
class ShipmentManifest:
    shipment_id: str
    ordered_items: tuple[str, ...]
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'shipment_id': self.shipment_id,
            'items': list(self.ordered_items),
            'digest': self.digest,
        }


@dataclass(frozen=True)
class BootstrapGrant:
    path: Path
    relative_path: str
    grant_digest: str
    shipment_id: str
    authorized_invocations: tuple[str, ...]
    expected_token: str
    expected_predecessor_id: str
    manifest_digest: str
    authorizing_decision: str
    operator: str
    expires_on_claim: bool


@dataclass(frozen=True)
class BootstrapGrantConsumptionRecord:
    workspace: Path
    path: Path
    relative_path: str
    schema_version: int
    grant_digest: str
    grant_path: str
    shipment_id: str
    label: str
    phase: str
    actor: str
    session_id: str
    head_sha: str
    manifest_digest: str
    manifest_items: tuple[str, ...]
    blocking_token: str
    inferred_predecessor_id: str | None
    claimed_at: str
    status: Literal['claimed', 'consumed']
    audit_ref: dict[str, Any] | None
    authorizing_decision: str
    operator: str
    observed_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'grant_digest': self.grant_digest,
            'grant_path': self.grant_path,
            'shipment_id': self.shipment_id,
            'label': self.label,
            'phase': self.phase,
            'actor': self.actor,
            'session_id': self.session_id,
            'head_sha': self.head_sha,
            'manifest_digest': self.manifest_digest,
            'manifest_items': list(self.manifest_items),
            'blocking_token': self.blocking_token,
            'inferred_predecessor_id': self.inferred_predecessor_id,
            'claimed_at': self.claimed_at,
            'status': self.status,
            'audit_ref': self.audit_ref,
            'authorizing_decision': self.authorizing_decision,
            'operator': self.operator,
            'observed_payload': self.observed_payload,
        }


@dataclass(frozen=True)
class BootstrapGrantHooks:
    before_claim_validation: Callable[[Path], None] | None = None
    after_claim_persisted: Callable[[BootstrapGrantConsumptionRecord], None] | None = None


@dataclass(frozen=True)
class BootstrapGrantMatchResult:
    applied: bool
    warnings: tuple[str, ...] = ()
    grant: BootstrapGrant | None = None
    claim_record: BootstrapGrantConsumptionRecord | None = None


def compute_manifest_digest(ordered_items: tuple[str, ...] | list[str]) -> str:
    payload = json.dumps(list(ordered_items), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def derive_shipment_manifest(shipments: list[Any] | tuple[Any, ...], shipment_id: str) -> ShipmentManifest | None:
    for shipment in shipments:
        candidate_id = getattr(shipment, 'shipment_id', None)
        if candidate_id != shipment_id:
            continue
        ordered_items = tuple(str(item) for item in getattr(shipment, 'manifest_item_ids', ()) or ())
        return ShipmentManifest(
            shipment_id=shipment_id,
            ordered_items=ordered_items,
            digest=compute_manifest_digest(ordered_items),
        )
    return None


def _relative_repo_path(path: Path, workspace: Path) -> str:
    return path.resolve().relative_to(workspace.resolve()).as_posix()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _write_all(fd: int, data: bytes) -> None:
    """Write every byte of ``data`` to ``fd``, looping until fully written.

    ``os.write()`` may legally return fewer bytes than requested without
    raising (a short write). Every caller in this module treats a completed
    write as proof the full payload was persisted before the subsequent
    ``os.fsync()`` and before returning success -- silently accepting a
    short write would let a truncated, corrupt record be fsynced and
    reported as a successful claim/append/consume. Raises ``OSError`` if a
    write returns a non-positive byte count without raising, since that
    can never represent forward progress.
    """
    view = memoryview(data)
    total = 0
    length = len(view)
    while total < length:
        written = os.write(fd, view[total:])
        if written <= 0:
            raise OSError(
                f'os.write() returned {written} bytes for a {length}-byte payload; '
                'refusing to treat a non-positive write as progress'
            )
        total += written


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _contains_unsafe_path_syntax(value: str) -> bool:
    return (
        '\x00' in value
        or '/' in value
        or '\\' in value
        or '..' in value.split('/')
        or '..' in value.split('\\')
        or bool(_DRIVE_PREFIX_PATTERN.match(value))
        or value.startswith(_UNC_PREFIXES)
    )


def validate_bootstrap_grant_inputs(shipment_id: str, invocation_label: str) -> None:
    if not isinstance(shipment_id, str) or not shipment_id.strip():
        raise BootstrapGrantArgumentError('bootstrap grant requires a non-empty shipment id')
    if not isinstance(invocation_label, str) or not invocation_label.strip():
        raise BootstrapGrantArgumentError('bootstrap grant requires a non-empty invocation label')
    normalized_shipment_id = shipment_id.strip()
    normalized_label = invocation_label.strip()
    if _contains_unsafe_path_syntax(normalized_shipment_id) or not _SHIPMENT_ID_PATTERN.match(normalized_shipment_id):
        raise BootstrapGrantArgumentError(
            f'unsafe bootstrap-grant shipment id: {shipment_id!r}'
        )
    if _contains_unsafe_path_syntax(normalized_label) or normalized_label not in VALID_BOOTSTRAP_GRANT_INVOCATIONS:
        raise BootstrapGrantArgumentError(
            f'unsafe bootstrap-grant invocation label: {invocation_label!r}'
        )


def _warning(message: str) -> tuple[str, ...]:
    return (f'bootstrap grant warning: {message}',)


def load_bootstrap_grant(workspace: Path, shipment_id: str) -> tuple[BootstrapGrant | None, tuple[str, ...]]:
    validate_bootstrap_grant_inputs(shipment_id, VALID_BOOTSTRAP_GRANT_INVOCATIONS[0])
    grant_path = Path(workspace) / _BOOTSTRAP_GRANTS_ROOT / f'{shipment_id}.yaml'
    try:
        raw_bytes = _read_bytes_no_follow_walked(
            workspace, _BOOTSTRAP_GRANTS_ROOT.parts, f'{shipment_id}.yaml'
        )
    except FileNotFoundError:
        return None, ()
    except (OSError, ValueError) as exc:
        return None, _warning(f'grant file {grant_path} is unreadable: {exc}')
    try:
        loaded = yaml.safe_load(raw_bytes.decode('utf-8'))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        return None, _warning(f'grant file {grant_path} is invalid: {exc}')
    if not isinstance(loaded, dict):
        return None, _warning(f'grant file {grant_path} is invalid: expected a mapping')

    required_fields = (
        'schema_version',
        'shipment_id',
        'authorized_invocations',
        'expected_token',
        'expected_predecessor_id',
        'manifest_digest',
        'authorizing_decision',
        'operator',
        'expires_on_claim',
    )
    missing = [field for field in required_fields if field not in loaded]
    if missing:
        return None, _warning(
            f'grant file {grant_path} is invalid: missing required fields {", ".join(missing)}'
        )
    if loaded.get('schema_version') != 1:
        return None, _warning(f'grant file {grant_path} is invalid: schema_version must be 1')

    authorized = loaded.get('authorized_invocations')
    if not isinstance(authorized, list) or not authorized:
        return None, _warning(
            f'grant file {grant_path} is invalid: authorized_invocations must be a non-empty list'
        )
    normalized_authorized: list[str] = []
    for label in authorized:
        if not isinstance(label, str) or label not in VALID_BOOTSTRAP_GRANT_INVOCATIONS:
            return None, _warning(
                f'grant file {grant_path} is invalid: unsupported invocation label {label!r}'
            )
        if label in normalized_authorized:
            return None, _warning(
                f'grant file {grant_path} is invalid: duplicate invocation label {label!r}'
            )
        normalized_authorized.append(label)

    string_fields = (
        'shipment_id',
        'expected_token',
        'expected_predecessor_id',
        'manifest_digest',
        'authorizing_decision',
        'operator',
    )
    normalized_strings: dict[str, str] = {}
    for field in string_fields:
        value = loaded.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, _warning(
                f'grant file {grant_path} is invalid: {field} must be a non-empty string'
            )
        normalized_strings[field] = value.strip()
    if loaded.get('expires_on_claim') is not True:
        return None, _warning(f'grant file {grant_path} is invalid: expires_on_claim must be true')

    return BootstrapGrant(
        path=grant_path,
        relative_path=_relative_repo_path(grant_path, Path(workspace)),
        grant_digest=_sha256_bytes(raw_bytes),
        shipment_id=normalized_strings['shipment_id'],
        authorized_invocations=tuple(normalized_authorized),
        expected_token=normalized_strings['expected_token'],
        expected_predecessor_id=normalized_strings['expected_predecessor_id'],
        manifest_digest=normalized_strings['manifest_digest'],
        authorizing_decision=normalized_strings['authorizing_decision'],
        operator=normalized_strings['operator'],
        expires_on_claim=True,
    ), ()


def _single_blocking_check(observed_payload: dict[str, Any]) -> dict[str, Any] | None:
    checks = observed_payload.get('checks')
    if not isinstance(checks, list):
        return None
    blocked = [check for check in checks if isinstance(check, dict) and check.get('status') == 'blocked']
    if len(blocked) != 1:
        return None
    return blocked[0]


def _record_path_for(workspace: Path, shipment_id: str, label: str) -> Path:
    return Path(workspace) / _CONSUMPTION_ROOT / shipment_id / f'{label}.json'


def _record_relative_path(shipment_id: str, label: str) -> str:
    return (_CONSUMPTION_ROOT / shipment_id / f'{label}.json').as_posix()


def _post_create_identity_error(fd: int, path: Path) -> str | None:
    stat_fd = os.fstat(fd)
    stat_path = os.lstat(path)
    if _REPARSE_POINT_ATTRIBUTE and stat_path.st_file_attributes & _REPARSE_POINT_ATTRIBUTE:
        return 'created record path unexpectedly resolved to a reparse point'
    if stat_fd.st_dev != stat_path.st_dev or stat_fd.st_ino != stat_path.st_ino:
        return 'created record identity did not match the expected path'
    return None


def _parse_consumption_record_bytes(
    raw: bytes, *, path: Path, workspace: Path
) -> BootstrapGrantConsumptionRecord:
    try:
        data = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'record is invalid JSON: {exc}') from exc
    if not isinstance(data, dict):
        raise ValueError(_UNKNOWN_RECORD_ERROR)
    if data.get('schema_version') != 1:
        raise ValueError(_UNKNOWN_RECORD_ERROR)
    required = (
        'grant_digest',
        'grant_path',
        'shipment_id',
        'label',
        'phase',
        'actor',
        'session_id',
        'head_sha',
        'manifest_digest',
        'manifest_items',
        'blocking_token',
        'claimed_at',
        'status',
        'authorizing_decision',
        'operator',
        'observed_payload',
    )
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f'{_UNKNOWN_RECORD_ERROR}: missing {", ".join(missing)}')
    shipment_id = data.get('shipment_id')
    label = data.get('label')
    if not isinstance(shipment_id, str) or not isinstance(label, str):
        raise ValueError(_UNKNOWN_RECORD_ERROR)
    if path.parent.name != shipment_id or path.name != f'{label}.json':
        raise ValueError('record path does not match its shipment_id/label payload')
    status = data.get('status')
    if status not in ('claimed', 'consumed'):
        raise ValueError(_UNKNOWN_RECORD_ERROR)
    manifest_items = data.get('manifest_items')
    if not isinstance(manifest_items, list) or any(not isinstance(item, str) for item in manifest_items):
        raise ValueError(_UNKNOWN_RECORD_ERROR)
    observed_payload = data.get('observed_payload')
    if not isinstance(observed_payload, dict):
        raise ValueError(_UNKNOWN_RECORD_ERROR)
    audit_ref = data.get('audit_ref')
    if audit_ref is not None and not isinstance(audit_ref, dict):
        raise ValueError(_UNKNOWN_RECORD_ERROR)
    inferred_predecessor_id = data.get('inferred_predecessor_id')
    if inferred_predecessor_id is not None and not isinstance(inferred_predecessor_id, str):
        raise ValueError(_UNKNOWN_RECORD_ERROR)
    return BootstrapGrantConsumptionRecord(
        workspace=Path(workspace),
        path=path,
        relative_path=_relative_repo_path(path, Path(workspace)),
        schema_version=1,
        grant_digest=str(data['grant_digest']),
        grant_path=str(data['grant_path']),
        shipment_id=shipment_id,
        label=label,
        phase=str(data['phase']),
        actor=str(data['actor']),
        session_id=str(data['session_id']),
        head_sha=str(data['head_sha']),
        manifest_digest=str(data['manifest_digest']),
        manifest_items=tuple(manifest_items),
        blocking_token=str(data['blocking_token']),
        inferred_predecessor_id=inferred_predecessor_id,
        claimed_at=str(data['claimed_at']),
        status=status,
        audit_ref=audit_ref,
        authorizing_decision=str(data['authorizing_decision']),
        operator=str(data['operator']),
        observed_payload=observed_payload,
    )


def _read_consumption_record(path: Path, *, workspace: Path) -> BootstrapGrantConsumptionRecord:
    try:
        raw = _read_bytes_no_follow(path)
    except OSError as exc:
        raise ValueError(f'record is unreadable: {exc}') from exc
    return _parse_consumption_record_bytes(raw, path=path, workspace=Path(workspace))



def _existing_record_warning(path: Path, *, workspace: Path, grant_digest: str) -> tuple[str, ...]:
    relative = _relative_repo_path(path, Path(workspace)) if path.exists() else path.as_posix()
    try:
        record = _read_consumption_record(path, workspace=workspace)
    except ValueError as exc:
        return _warning(f'consumption record {relative} is malformed and remains disqualifying: {exc}')
    if record.grant_digest != grant_digest:
        return _warning(
            f'consumption record {relative} was created under a different grant digest and remains disqualifying'
        )
    return _warning(f'consumption record {relative} already exists and remains disqualifying')


def _windows_kernel32():
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    invalid_handle = wintypes.HANDLE(-1).value

    class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ('dwFileAttributes', wintypes.DWORD),
            ('ftCreationTime', wintypes.FILETIME),
            ('ftLastAccessTime', wintypes.FILETIME),
            ('ftLastWriteTime', wintypes.FILETIME),
            ('dwVolumeSerialNumber', wintypes.DWORD),
            ('nFileSizeHigh', wintypes.DWORD),
            ('nFileSizeLow', wintypes.DWORD),
            ('nNumberOfLinks', wintypes.DWORD),
            ('nFileIndexHigh', wintypes.DWORD),
            ('nFileIndexLow', wintypes.DWORD),
        ]

    kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.GetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(BY_HANDLE_FILE_INFORMATION),
    )
    kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32, BY_HANDLE_FILE_INFORMATION, invalid_handle


def _windows_open_directory_handle(path: Path):
    import ctypes

    kernel32, info_type, invalid_handle = _windows_kernel32()
    FILE_READ_ATTRIBUTES = 0x0080
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    handle = kernel32.CreateFileW(
        str(path),
        FILE_READ_ATTRIBUTES,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if handle == invalid_handle:
        error_code = ctypes.get_last_error()
        raise OSError(error_code, f'CreateFileW failed for {path}')
    info = info_type()
    if not kernel32.GetFileInformationByHandle(handle, info):
        error_code = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error_code, f'GetFileInformationByHandle failed for {path}')
    if _REPARSE_POINT_ATTRIBUTE and info.dwFileAttributes & _REPARSE_POINT_ATTRIBUTE:
        kernel32.CloseHandle(handle)
        raise ValueError(f'path component {path} is a reparse point')
    return kernel32, handle


def _windows_close_handle(kernel32, handle) -> None:
    kernel32.CloseHandle(handle)


def _supports_posix_claim_strategy() -> bool:
    return (
        hasattr(os, 'O_NOFOLLOW')
        and os.open in os.supports_dir_fd
        and os.mkdir in os.supports_dir_fd
    )


def _supports_windows_claim_strategy() -> bool:
    return bool(_REPARSE_POINT_ATTRIBUTE) and hasattr(os, 'lstat') and hasattr(os, 'O_BINARY')


def _scan_existing_records(shipment_dir: Path, *, workspace: Path, grant_digest: str) -> tuple[bool, tuple[str, ...]]:
    if not shipment_dir.exists():
        return False, ()
    try:
        entries = sorted(shipment_dir.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        return True, _warning(f'consumption directory {shipment_dir} is unreadable: {exc}')
    for entry in entries:
        if entry.suffix != '.json':
            continue
        try:
            stat_result = os.lstat(entry)
        except OSError as exc:
            return True, _warning(f'consumption record {entry} is unreadable: {exc}')
        if _is_reparse_point(stat_result):
            return True, _warning(
                f'consumption record {_relative_repo_path(entry, Path(workspace))} is a reparse point and remains disqualifying'
            )
        try:
            record = _read_consumption_record(entry, workspace=workspace)
        except ValueError as exc:
            return True, _warning(
                f'consumption record {_relative_repo_path(entry, Path(workspace))} is malformed and remains disqualifying: {exc}'
            )
        if record.grant_digest != grant_digest:
            return True, _warning(
                f'consumption record {_relative_repo_path(entry, Path(workspace))} was created under a different grant digest and remains disqualifying'
            )
    return False, ()


def _scan_existing_records_posix_dir_fd(
    dir_fd: int, shipment_dir: Path, *, workspace: Path, grant_digest: str
) -> tuple[bool, tuple[str, ...]]:
    """POSIX descriptor-relative variant of ``_scan_existing_records``.

    ``_scan_existing_records`` re-resolves ``shipment_dir`` by pathname,
    which discards the containment guarantee of an already-verified
    ``O_NOFOLLOW`` directory-descriptor walk: if a path component is
    swapped after the walk completes, a pathname-based listing can miss an
    existing record (or find a different one), letting the caller create a
    new label file and defeat the documented rule that editing a grant
    cannot reset consumption. This variant lists and reads every entry
    relative to ``dir_fd`` -- the exact descriptor the walk produced --
    instead of re-resolving anything by pathname.
    """
    try:
        names = sorted(os.listdir(dir_fd))
    except OSError as exc:
        return True, _warning(f'consumption directory {shipment_dir} is unreadable: {exc}')
    for name in names:
        if not name.endswith('.json'):
            continue
        entry_path = shipment_dir / name
        try:
            entry_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
        except OSError as exc:
            return True, _warning(
                f'consumption record {_relative_repo_path(entry_path, Path(workspace))} is unreadable: {exc}'
            )
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(entry_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b''.join(chunks)
        finally:
            os.close(entry_fd)
        try:
            record = _parse_consumption_record_bytes(raw, path=entry_path, workspace=Path(workspace))
        except ValueError as exc:
            return True, _warning(
                f'consumption record {_relative_repo_path(entry_path, Path(workspace))} is malformed and remains disqualifying: {exc}'
            )
        if record.grant_digest != grant_digest:
            return True, _warning(
                f'consumption record {_relative_repo_path(entry_path, Path(workspace))} was created under a different grant digest and remains disqualifying'
            )
    return False, ()


def _claim_record_windows(
    *,
    workspace: Path,
    shipment_id: str,
    label: str,
    raw_payload: bytes,
    hooks: BootstrapGrantHooks,
    grant_digest: str,
) -> tuple[Path | None, tuple[str, ...]]:
    resolved_workspace = Path(workspace).resolve()
    resolved_root = (Path(workspace) / _CONSUMPTION_ROOT).resolve()
    if not _is_relative_to(resolved_root, resolved_workspace):
        return None, _warning(
            'bootstrap-grant consumption root resolves outside the workspace and cannot be used'
        )
    if hooks.before_claim_validation is not None:
        hooks.before_claim_validation(Path(workspace))

    components = ('.autoharness', 'gates', 'bootstrap-grant-consumption', shipment_id)
    partial = resolved_workspace
    handles: list[tuple[Any, Any]] = []
    try:
        for component in components:
            partial = partial / component
            if not partial.exists():
                try:
                    os.mkdir(partial)
                except FileExistsError:
                    pass
            stat_result = os.lstat(partial)
            if _REPARSE_POINT_ATTRIBUTE and stat_result.st_file_attributes & _REPARSE_POINT_ATTRIBUTE:
                return None, _warning(f'path component {partial} is a reparse point and cannot be used')
            kernel32, handle = _windows_open_directory_handle(partial)
            handles.append((kernel32, handle))

        shipment_dir = partial
        disqualifying, warnings = _scan_existing_records(
            shipment_dir,
            workspace=workspace,
            grant_digest=grant_digest,
        )
        if disqualifying:
            return None, warnings

        record_path = shipment_dir / f'{label}.json'
        if record_path.exists():
            stat_result = os.lstat(record_path)
            if _REPARSE_POINT_ATTRIBUTE and stat_result.st_file_attributes & _REPARSE_POINT_ATTRIBUTE:
                return None, _warning(
                    f'consumption record {_relative_repo_path(record_path, workspace)} is a reparse point and remains disqualifying'
                )
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_BINARY
        fd = os.open(record_path, flags, 0o600)
        try:
            _write_all(fd, raw_payload)
            os.fsync(fd)
            identity_error = _post_create_identity_error(fd, record_path)
            if identity_error is not None:
                return None, _warning(
                    f'consumption record {_relative_repo_path(record_path, workspace)} failed identity verification: {identity_error}'
                )
        finally:
            os.close(fd)
        return record_path, ()
    except FileExistsError:
        return None, _existing_record_warning(
            _record_path_for(workspace, shipment_id, label),
            workspace=workspace,
            grant_digest=grant_digest,
        )
    finally:
        for kernel32, handle in reversed(handles):
            _windows_close_handle(kernel32, handle)


def _claim_record_posix(
    *,
    workspace: Path,
    shipment_id: str,
    label: str,
    raw_payload: bytes,
    hooks: BootstrapGrantHooks,
    grant_digest: str,
) -> tuple[Path | None, tuple[str, ...]]:
    resolved_workspace = Path(workspace).resolve()
    resolved_root = (Path(workspace) / _CONSUMPTION_ROOT).resolve()
    if not _is_relative_to(resolved_root, resolved_workspace):
        return None, _warning(
            'bootstrap-grant consumption root resolves outside the workspace and cannot be used'
        )
    if hooks.before_claim_validation is not None:
        hooks.before_claim_validation(Path(workspace))

    flags_dir = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
    root_fd = os.open(str(resolved_workspace), flags_dir)
    current_fd = root_fd
    opened_fds = [root_fd]
    components = ('.autoharness', 'gates', 'bootstrap-grant-consumption', shipment_id)
    shipment_dir = Path(workspace) / _CONSUMPTION_ROOT / shipment_id
    try:
        for component in components:
            try:
                os.mkdir(component, 0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            next_fd = os.open(
                component,
                flags_dir | os.O_NOFOLLOW,
                dir_fd=current_fd,
            )
            opened_fds.append(next_fd)
            current_fd = next_fd

        disqualifying, warnings = _scan_existing_records_posix_dir_fd(
            current_fd,
            shipment_dir,
            workspace=workspace,
            grant_digest=grant_digest,
        )
        if disqualifying:
            return None, warnings

        record_path = shipment_dir / f'{label}.json'
        record_fd = os.open(
            f'{label}.json',
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
            0o600,
            dir_fd=current_fd,
        )
        try:
            _write_all(record_fd, raw_payload)
            os.fsync(record_fd)
        finally:
            os.close(record_fd)
        # fsync the containing directory too: fsync(record_fd) alone only
        # guarantees the file's *data* is durable, not that the new
        # directory entry naming it is durable. Without this, a crash
        # between record creation and this fsync could lose the claim
        # name entirely, allowing the same grant label to be consumed
        # again and contradicting the documented durable at-most-once
        # contract.
        os.fsync(current_fd)
        return record_path, ()
    except FileExistsError:
        return None, _existing_record_warning(
            _record_path_for(workspace, shipment_id, label),
            workspace=workspace,
            grant_digest=grant_digest,
        )
    except OSError as exc:
        # O_NOFOLLOW on a path component that is itself a symlink (or any other
        # unexpected filesystem condition encountered while traversing the
        # consumption-root path, e.g. a component that is not a directory)
        # raises here instead of FileExistsError. Fail closed with a warning
        # rather than letting the containment violation crash the caller,
        # mirroring _claim_record_windows's reparse-point rejection.
        return None, _warning(
            f'bootstrap-grant consumption path could not be safely traversed and remains disqualifying: {exc}'
        )
    finally:
        for fd in reversed(opened_fds):
            try:
                os.close(fd)
            except OSError:
                pass


def append_no_follow(
    workspace: Path,
    relative_dir_components: tuple[str, ...],
    filename: str,
    data: bytes,
) -> Path:
    """Append ``data`` to ``workspace/<relative_dir_components>/<filename>``
    via a containment-checked, no-follow directory walk and file open.

    Mirrors ``_claim_record_posix`` / ``_claim_record_windows``'s no-follow
    directory-descriptor walk so a symlinked directory component -- or the
    target file itself being a symlink/reparse point -- cannot redirect this
    write outside the workspace boundary or onto an unexpected external
    file. Unlike the consumption-record claim path this is a log, not an
    at-most-once claim: the target file is created if missing and appended
    to if it already exists, but every directory component and the final
    file are still verified not to be a symlink/reparse point before being
    traversed or opened.

    Raises ``OSError``/``ValueError`` on any containment violation or
    unexpected filesystem condition; callers must fail closed (propagate,
    not silently widen the write) rather than falling back to an
    unprotected pathname-based append.
    """
    resolved_workspace = Path(workspace).resolve()

    if _supports_posix_claim_strategy():
        flags_dir = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
        root_fd = os.open(str(resolved_workspace), flags_dir)
        opened_fds = [root_fd]
        current_fd = root_fd
        try:
            for component in relative_dir_components:
                try:
                    os.mkdir(component, 0o700, dir_fd=current_fd)
                except FileExistsError:
                    pass
                next_fd = os.open(component, flags_dir | os.O_NOFOLLOW, dir_fd=current_fd)
                opened_fds.append(next_fd)
                current_fd = next_fd
            flags_file = os.O_CREAT | os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW
            file_fd = os.open(filename, flags_file, 0o600, dir_fd=current_fd)
            try:
                _write_all(file_fd, data)
                os.fsync(file_fd)
            finally:
                os.close(file_fd)
            # fsync the containing directory too, mirroring
            # _claim_record_posix's durability rationale for a freshly
            # created (not merely appended-to) log file.
            os.fsync(current_fd)
        finally:
            for fd in reversed(opened_fds):
                os.close(fd)
        return resolved_workspace.joinpath(*relative_dir_components, filename)

    if not _supports_windows_claim_strategy():
        raise OSError(
            'no-follow append strategy is unavailable on this platform; refusing to fall back '
            'to an unprotected pathname-based append'
        )

    handles: list[tuple[Any, Any]] = []
    partial = resolved_workspace
    try:
        for component in relative_dir_components:
            partial = partial / component
            if not partial.exists():
                try:
                    os.mkdir(partial)
                except FileExistsError:
                    pass
            stat_result = os.lstat(partial)
            if _is_reparse_point(stat_result):
                raise ValueError(f'path component {partial} is a reparse point and cannot be used')
            kernel32, handle = _windows_open_directory_handle(partial)
            handles.append((kernel32, handle))

        file_path = partial / filename
        if file_path.exists():
            stat_result = os.lstat(file_path)
            if _is_reparse_point(stat_result):
                raise ValueError(f'{file_path} is a reparse point and cannot be used')
        flags_file = os.O_CREAT | os.O_WRONLY | os.O_APPEND | os.O_BINARY
        fd = os.open(file_path, flags_file, 0o600)
        try:
            _write_all(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        return file_path
    finally:
        for kernel32, handle in reversed(handles):
            _windows_close_handle(kernel32, handle)


def _claim_record(
    *,
    workspace: Path,
    shipment_id: str,
    label: str,
    raw_payload: bytes,
    hooks: BootstrapGrantHooks,
    grant_digest: str,
) -> tuple[Path | None, tuple[str, ...]]:
    if _supports_posix_claim_strategy():
        return _claim_record_posix(
            workspace=workspace,
            shipment_id=shipment_id,
            label=label,
            raw_payload=raw_payload,
            hooks=hooks,
            grant_digest=grant_digest,
        )
    if _supports_windows_claim_strategy():
        return _claim_record_windows(
            workspace=workspace,
            shipment_id=shipment_id,
            label=label,
            raw_payload=raw_payload,
            hooks=hooks,
            grant_digest=grant_digest,
        )
    return None, _warning(
        'bootstrap-grant claim strategy is unavailable on this platform; refusing to fall back'
    )


def evaluate_bootstrap_grant(
    *,
    workspace: Path,
    shipments: list[Any] | tuple[Any, ...],
    observed_payload: dict[str, Any],
    invocation_label: str,
    actor: str,
    session_id: str,
    head_sha: str,
    hooks: BootstrapGrantHooks | None = None,
) -> BootstrapGrantMatchResult:
    target = observed_payload.get('target_shipment_id')
    if not isinstance(target, str):
        raise BootstrapGrantArgumentError('bootstrap grant requires a resolved shipment target')
    validate_bootstrap_grant_inputs(target, invocation_label)
    if observed_payload.get('phase') != _BOOTSTRAP_GRANT_PHASE or observed_payload.get('exit_code') != 1:
        return BootstrapGrantMatchResult(applied=False)

    grant, warnings = load_bootstrap_grant(workspace, target)
    if grant is None:
        return BootstrapGrantMatchResult(applied=False, warnings=warnings)
    if grant.shipment_id != target:
        return BootstrapGrantMatchResult(applied=False, warnings=warnings, grant=grant)
    if invocation_label not in grant.authorized_invocations:
        return BootstrapGrantMatchResult(applied=False, warnings=warnings, grant=grant)

    blocking_check = _single_blocking_check(observed_payload)
    if blocking_check is None:
        return BootstrapGrantMatchResult(applied=False, warnings=warnings, grant=grant)
    token = blocking_check.get('token')
    if token != grant.expected_token:
        return BootstrapGrantMatchResult(applied=False, warnings=warnings, grant=grant)
    details = blocking_check.get('details') if isinstance(blocking_check.get('details'), dict) else {}
    inferred_predecessor_id = details.get('predecessor_id')
    if inferred_predecessor_id != grant.expected_predecessor_id:
        return BootstrapGrantMatchResult(applied=False, warnings=warnings, grant=grant)
    selected_predecessor_ids = details.get('selected_predecessor_ids')
    if isinstance(selected_predecessor_ids, list) and len(selected_predecessor_ids) > 1:
        # The topology check's predecessor loop short-circuits and returns
        # on the first incomplete predecessor it finds; details.predecessor_id
        # names only that one, while selected_predecessor_ids can carry every
        # predecessor the target declares. A grant authorizes exactly one
        # named predecessor -- applying it here would convert the *whole*
        # blocked result into a pass without ever having evaluated whether
        # the remaining declared predecessors are also complete. Fail closed
        # rather than silently widening a single-predecessor authorization
        # into a bypass of the rest of the DAG prerequisites.
        return BootstrapGrantMatchResult(
            applied=False,
            warnings=warnings + _warning(
                'grant refused: target declares multiple blocking predecessors '
                f'{selected_predecessor_ids!r}, but this grant authorizes only '
                f'{grant.expected_predecessor_id!r} and the topology check never evaluated '
                'whether the remaining declared predecessors are also complete'
            ),
            grant=grant,
        )

    manifest = derive_shipment_manifest(shipments, target)
    if manifest is None or manifest.digest != grant.manifest_digest:
        return BootstrapGrantMatchResult(applied=False, warnings=warnings, grant=grant)


    normalized_hooks = hooks or BootstrapGrantHooks()
    claimed_record = BootstrapGrantConsumptionRecord(
        workspace=Path(workspace),
        path=_record_path_for(workspace, target, invocation_label),
        relative_path=_record_relative_path(target, invocation_label),
        schema_version=1,
        grant_digest=grant.grant_digest,
        grant_path=grant.relative_path,
        shipment_id=target,
        label=invocation_label,
        phase=_BOOTSTRAP_GRANT_PHASE,
        actor=actor,
        session_id=session_id,
        head_sha=head_sha,
        manifest_digest=manifest.digest,
        manifest_items=manifest.ordered_items,
        blocking_token=str(token),
        inferred_predecessor_id=str(inferred_predecessor_id),
        claimed_at=_utc_timestamp(),
        status='claimed',
        audit_ref=None,
        authorizing_decision=grant.authorizing_decision,
        operator=grant.operator,
        observed_payload=observed_payload,
    )
    record_path, claim_warnings = _claim_record(
        workspace=workspace,
        shipment_id=target,
        label=invocation_label,
        raw_payload=_json_bytes(claimed_record.to_dict()),
        hooks=normalized_hooks,
        grant_digest=grant.grant_digest,
    )
    warnings = warnings + claim_warnings
    if record_path is None:
        return BootstrapGrantMatchResult(applied=False, warnings=warnings, grant=grant)

    claimed_record = replace(
        claimed_record,
        path=record_path,
        relative_path=_relative_repo_path(record_path, Path(workspace)),
    )
    if normalized_hooks.after_claim_persisted is not None:
        normalized_hooks.after_claim_persisted(claimed_record)
    return BootstrapGrantMatchResult(
        applied=True,
        warnings=warnings,
        grant=grant,
        claim_record=claimed_record,
    )


def _write_consumed_record_posix(
    *,
    workspace: Path,
    shipment_id: str,
    record_name: str,
    raw_payload: bytes,
) -> None:
    # Mirrors _claim_record_posix's O_NOFOLLOW dir-fd traversal so that
    # finalization is verified against the same descriptor-relative path the
    # claim step established, instead of trusting a plain pathname lookup
    # that could resolve through a directory swapped in after claim.
    resolved_workspace = Path(workspace).resolve()
    flags_dir = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
    root_fd = os.open(str(resolved_workspace), flags_dir)
    current_fd = root_fd
    opened_fds = [root_fd]
    components = ('.autoharness', 'gates', 'bootstrap-grant-consumption', shipment_id)
    temp_name = f'.{record_name}.{uuid.uuid4().hex}.tmp'
    try:
        for component in components:
            next_fd = os.open(component, flags_dir | os.O_NOFOLLOW, dir_fd=current_fd)
            opened_fds.append(next_fd)
            current_fd = next_fd
        temp_fd = os.open(
            temp_name,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
            0o600,
            dir_fd=current_fd,
        )
        try:
            _write_all(temp_fd, raw_payload)
            os.fsync(temp_fd)
        finally:
            os.close(temp_fd)
        os.rename(temp_name, record_name, src_dir_fd=current_fd, dst_dir_fd=current_fd)
    finally:
        try:
            os.unlink(temp_name, dir_fd=current_fd)
        except OSError:
            pass
        for fd in reversed(opened_fds):
            try:
                os.close(fd)
            except OSError:
                pass


def mark_consumption_record_consumed(
    record: BootstrapGrantConsumptionRecord,
    audit_ref: dict[str, Any],
) -> BootstrapGrantConsumptionRecord:
    workspace = Path(record.workspace)
    updated = replace(record, status='consumed', audit_ref=dict(audit_ref))
    raw_payload = _json_bytes(updated.to_dict())

    if _supports_posix_claim_strategy():
        _write_consumed_record_posix(
            workspace=workspace,
            shipment_id=record.shipment_id,
            record_name=record.path.name,
            raw_payload=raw_payload,
        )
        return updated

    temp_name = f'.{record.label}.{uuid.uuid4().hex}.tmp'
    shipment_dir = record.path.parent
    temp_path = shipment_dir / temp_name
    handles: list[tuple[Any, Any]] = []
    try:
        if _supports_windows_claim_strategy():
            partial = workspace.resolve()
            for component in ('.autoharness', 'gates', 'bootstrap-grant-consumption', record.shipment_id):
                partial = partial / component
                stat_result = os.lstat(partial)
                if _REPARSE_POINT_ATTRIBUTE and stat_result.st_file_attributes & _REPARSE_POINT_ATTRIBUTE:
                    raise ValueError(f'path component {partial} is a reparse point')
                kernel32, handle = _windows_open_directory_handle(partial)
                handles.append((kernel32, handle))
        with temp_path.open('xb') as handle:
            handle.write(raw_payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, record.path)
        return updated
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        for kernel32, handle in reversed(handles):
            _windows_close_handle(kernel32, handle)


def load_consumption_record(path: Path, *, workspace: Path) -> BootstrapGrantConsumptionRecord:
    return _read_consumption_record(path, workspace=workspace)
