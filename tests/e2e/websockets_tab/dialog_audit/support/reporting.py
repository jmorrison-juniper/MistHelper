"""Restricted, allowlisted evidence. Never save screenshots or private values."""

import json  # Serialize only validated public audit records.
import logging  # Log output actions without report bodies.
import os  # Enforce owner-only artifact permissions.
import re  # Redact identifiers even when a future observation accidentally includes one.
import shlex  # Record the actual process command without unsafe shell interpretation.
import stat  # Reject links and non-file report destinations.
import subprocess  # Record the selected source revision without network access.
import sys  # Obtain the exact interpreter invocation, not a fabricated validation command.
import tempfile  # Stage complete reports before replacing earlier evidence.
from pathlib import Path  # Restrict report destinations to the ignored audit directory.
from typing import Any  # Type the Windows system library handles.

logger = logging.getLogger(__name__)  # Keep artifacts out of log output.


class WindowsAuditReportApis:
    """Configure the Windows APIs that inspect and protect report handles."""

    @staticmethod
    def load() -> tuple[Any, Any, Any]:
        import ctypes  # Load native security APIs only on Windows.
        from ctypes import wintypes  # Match Windows API argument widths.

        library_loader = getattr(ctypes, "WinDLL", None)
        if library_loader is None:
            raise OSError("Windows security APIs are unavailable on this platform.")
        kernel32 = library_loader("kernel32", use_last_error=True)  # Open and inspect native handles.
        advapi32 = library_loader("advapi32", use_last_error=True)  # Build and apply a protected DACL.
        WindowsAuditReportApis._configure_kernel32(kernel32, ctypes, wintypes)
        WindowsAuditReportApis._configure_advapi32(advapi32, ctypes, wintypes)
        return kernel32, advapi32, wintypes

    @staticmethod
    def create_private_directory(path: Path) -> None:
        import ctypes  # Keep the new directory protected from its first instant.

        kernel32, descriptor, attributes = WindowsAuditReportApis._directory_security_attributes()
        try:
            if kernel32.CreateDirectoryW(str(path), ctypes.byref(attributes)):
                return
            get_last_error = getattr(ctypes, "get_last_error", None)
            if get_last_error is None:
                raise OSError("Windows did not provide the native error code.")
            error_code = get_last_error()
            if error_code != 183:
                raise WindowsAuditReportSecurity._windows_error(error_code)
        finally:
            kernel32.LocalFree(descriptor)

    @staticmethod
    def _directory_security_attributes() -> tuple[Any, Any, Any]:
        import ctypes  # Keep the new directory protected from its first instant.
        from ctypes import wintypes  # Match Windows security attribute fields.

        kernel32, advapi32, _ = WindowsAuditReportApis.load()
        descriptor = ctypes.c_void_p()
        sddl = "D:P(A;OICI;FA;;;OW)"
        if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, ctypes.byref(descriptor), None):
            raise WindowsAuditReportSecurity._windows_error()

        class SecurityAttributes(ctypes.Structure):
            """Pass the protected DACL to CreateDirectoryW."""

            _fields_ = [
                ("length", wintypes.DWORD),
                ("descriptor", ctypes.c_void_p),
                ("inherit", wintypes.BOOL),
            ]

        attributes = SecurityAttributes(ctypes.sizeof(SecurityAttributes), descriptor, False)
        return kernel32, descriptor, attributes

    @staticmethod
    def _configure_kernel32(kernel32: Any, ctypes: Any, wintypes: Any) -> None:
        kernel32.CreateFileW.argtypes = [  # Keep path access on the wide-character API.
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel32.CreateFileW.restype = wintypes.HANDLE  # Preserve the native handle width.
        kernel32.CreateDirectoryW.argtypes = [wintypes.LPCWSTR, ctypes.c_void_p]
        kernel32.CreateDirectoryW.restype = wintypes.BOOL
        kernel32.GetFileInformationByHandleEx.argtypes = [  # Read reparse attributes from the opened object.
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL  # Report native query failure.
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]  # Close directory handles.
        kernel32.CloseHandle.restype = wintypes.BOOL  # Report close failure.
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]  # Release the converted security descriptor.

    @staticmethod
    def _configure_advapi32(advapi32: Any, ctypes: Any, wintypes: Any) -> None:
        advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [  # Convert a fixed SDDL policy.
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(wintypes.DWORD),
        ]
        advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
        advapi32.GetSecurityDescriptorDacl.argtypes = [  # Extract only the explicit protected DACL.
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.BOOL),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(wintypes.BOOL),
        ]
        advapi32.GetSecurityDescriptorDacl.restype = wintypes.BOOL
        advapi32.SetSecurityInfo.argtypes = [  # Apply the DACL to the opened handle, not a path.
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        advapi32.SetSecurityInfo.restype = wintypes.DWORD  # Return a Win32 status code.
        advapi32.GetSecurityInfo.argtypes = [  # Read the applied DACL back from the same handle.
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        advapi32.GetSecurityInfo.restype = wintypes.DWORD  # Return a Win32 status code.
        advapi32.GetSecurityDescriptorControl.argtypes = [  # Read the protected and present control bits.
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.WORD),
            ctypes.POINTER(wintypes.DWORD),
        ]
        advapi32.GetSecurityDescriptorControl.restype = wintypes.BOOL  # Report native control read failure.


class WindowsAuditReportSecurity:
    """Apply owner-only access to Windows handles without following reparse points."""

    @staticmethod
    def _windows_apis() -> tuple[Any, Any, Any]:
        return WindowsAuditReportApis.load()

    @staticmethod
    def _windows_error(code: int | None = None) -> OSError:
        import ctypes  # Resolve Windows-only error helpers at runtime.

        get_last_error = getattr(ctypes, "get_last_error", None)
        if get_last_error is None:
            return OSError("A Windows API call failed on a non-Windows platform.")
        error_code = code if code is not None else get_last_error()
        return OSError(int(error_code), "Windows API call failed.")

    @staticmethod
    def _verify_handle(apis: tuple[Any, Any, Any], handle: int, path: Path, directory: bool) -> None:
        import ctypes  # Allocate the fixed file-attribute query buffer.
        from ctypes import wintypes  # Match the Windows attribute fields.

        attributes = (wintypes.DWORD * 2)()  # FileAttributeTagInfo contains two DWORD values.
        kernel32 = apis[0]  # Use the configured native API table.
        if not kernel32.GetFileInformationByHandleEx(handle, 9, attributes, ctypes.sizeof(attributes)):
            raise WindowsAuditReportSecurity._windows_error()
        WindowsAuditReportAccess.verify_attributes(attributes[0], path)
        if bool(attributes[0] & stat.FILE_ATTRIBUTE_DIRECTORY) != directory:
            raise ValueError(f"The report path has an invalid file type: {path}")

    @staticmethod
    def _set_owner_dacl(apis: tuple[Any, Any, Any], handle: int, directory: bool) -> None:
        import ctypes  # Own the converted security descriptor until the native call completes.
        from ctypes import wintypes  # Allocate Windows Boolean values for ACL inspection.

        kernel32, advapi32, _ = apis  # Keep native functions grouped by DLL.
        descriptor = ctypes.c_void_p()  # Receive the descriptor created from fixed SDDL.
        inheritance = "OICI" if directory else ""  # Pass directory access only to its children.
        sddl = f"D:P(A;{inheritance};FA;;;OW)"  # Protect the DACL and grant full access to the owner only.
        convert_descriptor = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW
        if not convert_descriptor(sddl, 1, ctypes.byref(descriptor), None):
            raise WindowsAuditReportSecurity._windows_error()
        try:
            present, defaulted = wintypes.BOOL(), wintypes.BOOL()  # Inspect the explicit DACL.
            dacl = ctypes.c_void_p()  # Receive the owner-only ACL.
            has_dacl = advapi32.GetSecurityDescriptorDacl(
                descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)
            )
            if not has_dacl or not present.value or not dacl.value:
                raise OSError("Windows did not provide the required owner-only DACL.")
            # Native run 43795918169 returned status 5 with WRITE_DAC alone. The handle now adds READ_CONTROL.
            status = advapi32.SetSecurityInfo(handle, 1, 0x80000004, None, None, dacl, None)  # Protected DACL.
            if status:  # A nonzero Win32 status means the DACL was not applied.
                raise WindowsAuditReportSecurity._windows_error(status)  # Fail closed with the native status.
        finally:
            kernel32.LocalFree(descriptor)  # Release the descriptor after success or failure.

    @classmethod
    def restrict(cls, handle: int, path: Path, directory: bool) -> None:
        apis = cls._windows_apis()  # Load only the native functions needed for this handle.
        cls._verify_handle(apis, handle, path, directory)  # Refuse reparse points and wrong object types.
        logger.info("Applying protected owner-only DACL to %s", path.name)  # Trace the native DACL write.
        cls._set_owner_dacl(apis, handle, directory)  # Apply the protected owner-only access rule.
        WindowsAuditReportDaclVerifier.verify(apis, handle, path)  # Prove that Windows kept the protected DACL.
        logger.debug("Applied protected owner-only DACL to %s", path.name)  # Confirm the verified DACL write.


class WindowsAuditReportDaclVerifier:
    """Read the applied DACL back so a silent inheritance change fails closed."""

    @staticmethod
    def _control_bits(apis: tuple[Any, Any, Any], descriptor: Any) -> int:
        import ctypes  # Pass output pointers to the native control query.
        from ctypes import wintypes  # Match the control and revision widths.

        control, revision = wintypes.WORD(), wintypes.DWORD()  # Receive the descriptor control bits.
        if not apis[1].GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)):
            raise WindowsAuditReportSecurity._windows_error()  # Fail closed when the control bits are unknown.
        return int(control.value)  # Return the bits for the protected and present check.

    @classmethod
    def verify(cls, apis: tuple[Any, Any, Any], handle: int, path: Path) -> None:
        import ctypes  # Receive the descriptor and DACL pointers from the native read.

        logger.info("Verifying protected owner-only DACL on %s", path.name)  # Trace the native readback.
        dacl, descriptor = ctypes.c_void_p(), ctypes.c_void_p()  # Receive pointers that Windows allocates.
        status = apis[1].GetSecurityInfo(  # Read DACL information through the same verified handle.
            handle, 1, 0x00000004, None, None, ctypes.byref(dacl), None, ctypes.byref(descriptor)
        )
        if status:  # A nonzero Win32 status means the DACL could not be read.
            raise WindowsAuditReportSecurity._windows_error(status)  # Fail closed with the native status.
        try:
            control = cls._control_bits(apis, descriptor)  # Read the protected and present bits.
            if not dacl.value or control & 0x1004 != 0x1004:  # Require a DACL with both control bits set.
                raise OSError(f"Windows did not keep the protected owner-only DACL: {path}")
        finally:
            apis[0].LocalFree(descriptor)  # Release the descriptor that GetSecurityInfo allocated.
        logger.debug("Verified protected owner-only DACL on %s", path.name)  # Confirm the readback result.


class WindowsAuditReportAccess:
    """Create the approved report directory and validate Windows file attributes."""

    @staticmethod
    def verify_attributes(attributes: int | None, path: Path) -> None:
        if attributes is None:
            raise ValueError(f"Windows file attributes cannot be verified: {path}")
        if attributes & 0x400:  # Windows FILE_ATTRIBUTE_REPARSE_POINT is not defined on other systems.
            raise ValueError(f"Windows report paths cannot use a reparse point: {path}")

    @classmethod
    def reject_reparse_points(cls, path: Path) -> None:
        for candidate in reversed((path, *path.parents)):
            try:
                status = candidate.lstat()
            except FileNotFoundError:
                continue
            cls.verify_attributes(getattr(status, "st_file_attributes", None), candidate)
            if stat.S_ISLNK(status.st_mode):
                raise ValueError(f"Windows report paths cannot use a symbolic link: {candidate}")
            if candidate != path and not stat.S_ISDIR(status.st_mode):
                raise ValueError(f"Windows report path components must be directories: {candidate}")

    @classmethod
    def ensure_private_directory(cls, path: Path) -> None:
        import ctypes  # Raise the native error when Windows cannot open the directory.

        cls.reject_reparse_points(path)
        for candidate in reversed((path, *path.parents)):
            try:
                status = candidate.lstat()
            except FileNotFoundError:
                WindowsAuditReportApis.create_private_directory(candidate)
                continue
            cls.verify_attributes(getattr(status, "st_file_attributes", None), candidate)
            if candidate != path and not stat.S_ISDIR(status.st_mode):
                raise ValueError(f"Windows report path components must be directories: {candidate}")
        kernel32, _, _ = WindowsAuditReportSecurity._windows_apis()
        handle = kernel32.CreateFileW(str(path), 0x00060080, 0x00000007, None, 3, 0x02200000, None)  # READ_CONTROL too.
        if handle == ctypes.c_void_p(-1).value:
            raise WindowsAuditReportSecurity._windows_error()
        try:
            WindowsAuditReportSecurity.restrict(handle, path, True)
        finally:
            if not kernel32.CloseHandle(handle):
                raise WindowsAuditReportSecurity._windows_error()
        cls.reject_reparse_points(path)

    @staticmethod
    def _open_staged_file_handle(path: Path) -> tuple[Any, int]:
        import ctypes  # Compare the native invalid-handle value without platform assumptions.

        logger.info("Opening staged audit report for owner-only access %s", path.name)  # Trace the ACL setup.
        desired_access = 0x00060080  # Request READ_CONTROL, WRITE_DAC, and FILE_READ_ATTRIBUTES for the DACL work.
        share_mode = 0x00000007  # Allow the exclusive creator handle to remain open while permissions change.
        open_existing = 3  # Reopen only the file already created by tempfile.mkstemp.
        open_reparse_point = 0x00200000  # Inspect the file object itself rather than following a reparse point.
        kernel32, _, _ = WindowsAuditReportSecurity._windows_apis()  # Load the native handle functions.
        handle = kernel32.CreateFileW(
            str(path),  # Reopen only the file that the exclusive creator made.
            desired_access,  # Include WRITE_DAC for the following protected DACL update.
            share_mode,  # Keep the original staging descriptor open during the ACL update.
            None,  # Use the inherited private security descriptor.
            open_existing,  # Refuse to create or truncate a different file.
            open_reparse_point,  # Verify the named object without following a reparse point.
            None,  # Do not inherit this security handle.
        )  # Request a handle that can read attributes and update the DACL.
        if handle == ctypes.c_void_p(-1).value:  # Fail closed when Windows cannot open the staged object.
            raise WindowsAuditReportSecurity._windows_error()  # Preserve the native open error.
        logger.debug("Opened staged audit report for owner-only access %s", path.name)  # Confirm the handle request.
        return kernel32, handle  # Keep the API owner for deterministic handle cleanup.

    @staticmethod
    def secure_staged_file(path: Path) -> None:
        logger.info("Applying owner-only access to staged audit report %s", path.name)  # Trace the DACL update.
        try:  # Log native failures while preserving their original type.
            kernel32, handle = WindowsAuditReportAccess._open_staged_file_handle(path)  # Open with ACL rights.
            try:
                WindowsAuditReportSecurity.restrict(handle, path, False)  # Verify and apply the owner-only DACL.
                logger.debug("Applied owner-only access to staged audit report %s", path.name)  # Confirm the update.
            finally:  # Close the native handle even when verification or ACL setup fails.
                logger.info("Closing staged audit report security handle %s", path.name)  # Trace handle cleanup.
                if not kernel32.CloseHandle(handle):  # Report a failed native handle close.
                    raise WindowsAuditReportSecurity._windows_error()  # Preserve the native close error.
                logger.debug("Closed staged audit report security handle %s", path.name)  # Confirm handle cleanup.
        except (OSError, ValueError):
            logger.exception("Could not set owner-only access on staged audit report %s", path.name)  # Record context.
            raise  # Keep the writer fail-closed when Windows cannot protect the staged file.


class AuditReportWriter:
    """Separate isolated form evidence from blocked live stages."""

    _FIELDS = {
        "key",
        "status",
        "observations",
        "sdk_signature_verified",
        "cancel",
        "source",
        "reproduction",
        "selectors",
        "ux_review",
    }  # No arbitrary raw evidence.

    @classmethod
    def build(
        cls,
        inventory: list[str],
        records: list[dict[str, Any]],
        duration_seconds: float = 0,
        sdk_version: str | None = None,
    ) -> dict[str, Any]:
        keys = [record.get("key") for record in records]  # Preserve the complete denominator.
        if not inventory or len(keys) != len(set(keys)) or set(keys) != set(inventory):
            raise ValueError("The report does not cover the complete nonempty inventory.")  # Never hide missing forms.
        if any(set(record) - cls._FIELDS for record in records):
            raise ValueError("The report contains prohibited evidence fields.")  # Reject credentials and screenshots.
        if any(record["status"] not in {"passed", "failed", "blocked", "skipped", "no-data"} for record in records):
            raise ValueError("The report contains an unknown status.")  # Do not widen pass semantics.
        totals = {
            status: sum(record["status"] == status for record in records)
            for status in ("passed", "failed", "blocked", "skipped", "no-data")
        }  # Separate outcomes.
        measured = sum(
            record["status"] in {"passed", "failed"} or "source" in record for record in records
        )  # Rendered forms can have blocked target selection.
        return {
            "inventory": inventory,
            "sdk_version": sdk_version,
            "isolated_inspection": {
                "measured_dialogs": measured,
                "totals": totals,
                "duration_seconds": round(duration_seconds, 3),
                "records": cls.redact(records),
            },
            "live_inspection": {
                "status": "blocked",
                "reason": "This isolated run did not execute live inspection. See the separate live report.",
            },
            "historical_capability": {
                "status": "blocked",
                "reason": "Initial planning: localhost:8055 was unreachable; the worktree environment was absent.",
            },  # Preserve historical evidence without presenting it as the current environment state.
            "live_subscription": {
                "status": "blocked",
                "reason": "This inspection run did not select the opt-in exact-key read-only lifecycle test.",
            },
        }  # Historical blocker, not a new probe.

    @classmethod
    def redact(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: cls.redact(item) for key, item in value.items()}  # Redact all nested observations.
        if isinstance(value, list):
            return [cls.redact(item) for item in value]  # Never serialize raw selector values.
        if not isinstance(value, str):
            return value  # Counts and booleans contain no private identifiers.
        value = re.sub(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b", "<identifier>", value)  # UUIDs.
        value = re.sub(
            r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b|\b(?:\d{1,3}\.){3}\d{1,3}\b", "<identifier>", value
        )  # MACs and IPv4.
        return re.sub(
            r"(?i)\b(token|password|authorization|secret)\s*[:=]\s*\S+", r"\1=<redacted>", value
        )  # Secret-like assignments.

    @staticmethod
    def _prepare_report(report: dict[str, Any], root: Path) -> dict[str, Any]:
        logger.info("Reading the local source revision")  # Log before the local Git query.
        try:
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True
            ).stdout.strip()  # Record only local source state.
        except (OSError, subprocess.CalledProcessError):
            logger.exception("Could not read the local source revision")
            raise
        logger.debug("Read the local source revision")  # Confirm the local query result.
        command = shlex.join(sys.orig_argv)  # Record the actual Python invocation.
        command = re.sub(
            r"--ws-audit-base-url(?:=|\s+)\S+", "--ws-audit-base-url=<authorized-origin>", command
        )  # Never save a real origin.
        return {
            **report,
            "source_revision": revision,
            "command": AuditReportWriter.redact(command),
        }  # Add sanitized execution evidence.

    @staticmethod
    def _documents(report: dict[str, Any]) -> list[tuple[str, str]]:
        summary_lines = [
            "# WebSocket dialog audit",
            "",
            f"Isolated measured dialogs: {report['isolated_inspection']['measured_dialogs']}",
            f"Live measured dialogs: {report['live_inspection'].get('measured_dialogs', 0)}",
            f"Live inspection status: {report['live_inspection']['status']}",
            f"Live subscription: {report['live_subscription']['status']}",
            (
                "Only the reviewed site.stats.devices observation lifecycle was selected."
                if report["live_subscription"].get("key")
                else "No operation was started."
            ),
        ]  # Keep isolated and live evidence separate.
        summary = "\n".join(summary_lines) + "\n"
        prefix = (
            "subscription-report"
            if report["live_subscription"].get("key")
            else "live-report" if "measured_dialogs" in report["live_inspection"] else "report"
        )  # Preserve the report name for each supported run type.
        return [
            (prefix + ".json", json.dumps(report, indent=2)),
            (prefix + ".md", summary),
        ]  # Stage both report formats as one transaction.

    @staticmethod
    def write(report: dict[str, Any], destination: str | Path) -> None:
        root = Path(__file__).resolve().parents[5]  # Bind artifacts to this checkout only.
        expected = root / "test-artifacts" / "websocket-dialog-audit"  # Use the ignored owner-only location.
        path = Path(destination).absolute()  # Reject arbitrary public or external paths.
        if (
            path != expected
            or path.resolve() != expected
            or any(parent.is_symlink() for parent in (path, *path.parents))
        ):
            raise ValueError(
                "Use the restricted worktree test-artifacts/websocket-dialog-audit directory."
            )  # Reject traversal and symlinks.
        logger.info("Preparing the restricted audit report directory")  # Log before filesystem actions.
        if sys.platform == "win32":
            WindowsAuditReportAccess.ensure_private_directory(path)
        else:
            path.mkdir(parents=True, exist_ok=True, mode=0o700)  # Create only the approved owner-only directory.
            path.chmod(0o700)  # Tighten an existing directory before staging files.
        logger.debug("Prepared the restricted audit report directory")  # Confirm the directory action.
        AuditReportFileTransaction.write(report, path, root)


class AuditReportFileTransaction:
    """Stage both report formats and restore earlier files if replacement fails."""

    @classmethod
    def write(cls, report: dict[str, Any], directory: Path, root: Path) -> None:
        safe_report = AuditReportWriter._prepare_report(report, root)
        documents = AuditReportWriter._documents(safe_report)
        staged: list[tuple[Path, Path]] = []
        backups: dict[Path, Path] = {}
        installed: list[Path] = []
        succeeded = False
        try:
            cls._stage_reports(directory, documents, staged)
            cls._backup_destinations(staged, backups)
            for temporary_path, destination in staged:
                logger.info("Installing audit report %s", destination.name)  # Log before atomic replacement.
                os.replace(temporary_path, destination)
                installed.append(destination)
                logger.debug("Installed audit report %s", destination.name)  # Confirm the replacement.
            succeeded = True
        except (OSError, ValueError):
            logger.exception("Could not replace the restricted audit report pair")
            raise
        finally:
            cls._finish(staged, backups, installed, succeeded)

    @staticmethod
    def _stage_reports(
        directory: Path,
        documents: list[tuple[str, str]],
        staged: list[tuple[Path, Path]],
    ) -> None:
        for name, text in documents:
            logger.info("Staging audit report %s", name)  # Log before writing each private temporary file.
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".audit-report-stage-", suffix=".tmp", dir=directory
            )  # Create an exclusive file beside the final report.
            staged.append((Path(temporary_name), directory / name))
            try:
                if sys.platform == "win32":
                    WindowsAuditReportAccess.secure_staged_file(staged[-1][0])  # Require ACL rights first.
                else:
                    os.fchmod(descriptor, 0o600)  # Preserve POSIX owner-only file access.
                descriptor, output = -1, os.fdopen(descriptor, "w", encoding="utf-8")
                with output:
                    output.write(text)  # Write the complete report before replacement.
                    output.flush()  # Flush Python buffers before the durability request.
                    os.fsync(output.fileno())  # Persist staged contents before installation.
            finally:
                if descriptor >= 0:
                    os.close(descriptor)  # Close a descriptor when setup fails before fdopen.
            logger.debug("Staged audit report %s", name)  # Confirm the complete staged file.

    @staticmethod
    def _backup_destinations(staged: list[tuple[Path, Path]], backups: dict[Path, Path]) -> None:
        for _, destination in staged:
            logger.info("Checking audit report destination %s", destination.name)
            if sys.platform == "win32":
                WindowsAuditReportAccess.reject_reparse_points(destination)
            AuditReportFileTransaction._backup_one(destination, backups)
            logger.debug("Checked audit report destination %s", destination.name)

    @staticmethod
    def _backup_one(destination: Path, backups: dict[Path, Path]) -> None:
        try:
            status = destination.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
            raise ValueError(f"An existing audit report is not a regular file: {destination}")
        logger.info("Backing up existing audit report %s", destination.name)
        descriptor, backup_name = tempfile.mkstemp(
            prefix=".audit-report-backup-", suffix=".tmp", dir=destination.parent
        )  # Reserve a private same-directory rollback name.
        backup = Path(backup_name)
        try:
            os.close(descriptor)
            os.replace(destination, backup)
        except OSError:
            if backup.exists() and not destination.exists():
                os.replace(backup, destination)
            else:
                backup.unlink(missing_ok=True)
            raise
        backups[destination] = backup
        logger.debug("Backed up existing audit report %s", destination.name)

    @staticmethod
    def _finish(
        staged: list[tuple[Path, Path]],
        backups: dict[Path, Path],
        installed: list[Path],
        succeeded: bool,
    ) -> None:
        if succeeded:
            for backup in backups.values():
                logger.info("Removing an obsolete audit report backup")
                backup.unlink(missing_ok=True)
        else:
            for destination, backup in backups.items():
                if backup.exists():
                    logger.info("Restoring audit report %s", destination.name)
                    os.replace(backup, destination)
            for destination in installed:
                if destination not in backups:
                    logger.info("Removing incomplete audit report %s", destination.name)
                    destination.unlink(missing_ok=True)
        for temporary_path, _ in staged:
            temporary_path.unlink(missing_ok=True)
        logger.debug("Finished audit report transaction cleanup")
