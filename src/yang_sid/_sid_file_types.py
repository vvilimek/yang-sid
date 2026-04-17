# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import TypedDict, Optional, Any

import yangson.instproto


"""
Module with internal typing information for SID Files pieces.
"""

DependencyRevisionDict = TypedDict("DependencyRevisionDict", {
    "module-name": str,
    "module-revision": str,
    }, total=True)

AssignmentRangeDict = TypedDict("AssignmentRangeDict", {
    "entry-point": int,
    "size": int,
    }, total=True)

class ItemDict(TypedDict, total=False):
    status: yangson.instproto.IntInstanceNode
    namespace: yangson.instproto.StrInstanceNode
    identifier: yangson.instproto.StrInstanceNode
    sid: yangson.instproto.IntInstanceNode

class SidFileDict(yangson.instproto.InstanceNodeProtocol):
    def __getitem__(self, key: Literal["module-name", "module-revision", "sid-file-version", "sid-file-status", "dependency-revision", "assignment-range", "item", "description"]) -> yangson.instproto.StrInstanceNode | yangson.instproto.IntInstanceNode | yangson.instproto.ArrayInstanceNode:
        pass

class SidFileBuilder(TypedDict, total=False):
    module: str
    revision: Optional[str]
    status: str
    entries: list[Any]
