# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import TypedDict, Optional, Any, Literal, overload

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
    @overload
    def __getitem__(self, key: Literal["module-name"]) -> yangson.instproto.StrInstanceNode: ...
    @overload
    def __getitem__(self, key: Literal["module-revision"]) -> yangson.instproto.StrInstanceNode: ...
    @overload
    def __getitem__(self, key: Literal["sid-file-version"]) -> yangson.instproto.IntInstanceNode: ...
    @overload
    def __getitem__(self, key: Literal["sid-file-status"]) -> yangson.instproto.StrInstanceNode: ...
    @overload
    def __getitem__(self, key: Literal["dependency-revision"]) -> yangson.instproto.ArrayInstanceNode: ...
    @overload
    def __getitem__(self, key: Literal["assignment-range"]) -> yangson.instproto.ArrayInstanceNode: ...
    @overload
    def __getitem__(self, key: Literal["item"]) -> yangson.instproto.ArrayInstanceNode: ...
    @overload
    def __getitem__(self, key: Literal["description"]) -> yangson.instproto.StrInstanceNode: ...

    def __getitem__(self, key: Literal["module-name", "module-revision", "sid-file-version", "sid-file-status", "dependency-revision", "assignment-range", "item", "description"]) -> yangson.instproto.StrInstanceNode | yangson.instproto.IntInstanceNode | yangson.instproto.ArrayInstanceNode:
        return super().__getitem__(key)

class SidFileBuilder(TypedDict, total=False):
    module: str
    revision: Optional[str]
    status: str
    entries: list[Any]
