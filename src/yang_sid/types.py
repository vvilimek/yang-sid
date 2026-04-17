# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import NewType, Union

SID = NewType("SID", int)

class AbsoluteSID(int):
    def to_sid(self) -> SID:
        return SID(int(self))

class RelativeSID(int):
    def to_sid(self, base: Union[AbsoluteSID, int]) -> SID:
        return SID(AbsoluteSID(base).to_sid() + int(self))

