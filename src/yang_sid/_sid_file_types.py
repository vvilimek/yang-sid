# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import TypedDict, Optional, Any

DependencyRevision = TypedDict("DependencyRevision", {
    "module-name": str,
    "module-revision": str,
    }, total=True)

AssignmentRangeDict = TypedDict("AssignmentRangeDict", {
    "entry-point": int,
    "size": int,
    }, total=True)

ItemDict = TypedDict("ItemDict", {
    "status": int,
    "namespace": int,
    "identifier": str,
    "sid": int,
    }, total=False)

SidFileDict = TypedDict("SidFileDict", {
    "module-name": str,
    "module-revision": str,
    "sid-file-version": int,
    "sid-file-status": str,
    "dependency-revision": list[DependencyRevision],
    "assignment-range": list[AssignmentRangeDict],
    "item": list[ItemDict],
    }, total=False)

class SidFileBuilder(TypedDict, total=False):
    module: str
    revision: Optional[str]
    status: str
    entries: list[Any]
