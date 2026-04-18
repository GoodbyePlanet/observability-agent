from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass

from server.config import ServiceConfig, settings


@dataclass
class DiscoveredFile:
    abs_path: str
    rel_path: str   # relative to code_base_path
    service_name: str
    language: str


def _matches_any(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        # Also try matching just the filename
        if fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


_EXT_TO_LANGUAGE = {
    ".java": "java",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "typescript",
    ".jsx": "typescript",
}


def discover_files(services: list[ServiceConfig]) -> list[DiscoveredFile]:
    base = settings.code_base_path
    result: list[DiscoveredFile] = []

    for svc in services:
        svc_abs = os.path.join(base, svc.path)
        if not os.path.isdir(svc_abs):
            continue

        for root, dirs, files in os.walk(svc_abs):
            # Prune excluded directories early
            dirs[:] = [
                d for d in dirs
                if not _matches_any(
                    os.path.relpath(os.path.join(root, d), svc_abs),
                    svc.exclude,
                )
            ]

            for fname in files:
                abs_path = os.path.join(root, fname)
                rel_to_svc = os.path.relpath(abs_path, svc_abs)
                rel_to_base = os.path.relpath(abs_path, base)

                ext = os.path.splitext(fname)[1]
                language = _EXT_TO_LANGUAGE.get(ext)
                if language is None:
                    continue
                if language not in svc.languages:
                    continue

                # Check include patterns (relative to service root)
                if svc.include:
                    if not _matches_any(rel_to_svc, svc.include):
                        continue

                # Check exclude patterns
                if _matches_any(rel_to_svc, svc.exclude):
                    continue

                result.append(DiscoveredFile(
                    abs_path=abs_path,
                    rel_path=rel_to_base,
                    service_name=svc.name,
                    language=language,
                ))

    return result
