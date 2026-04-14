# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from pathlib import Path

import os
import yang_sid

path = Path(yang_sid.__file__).parent.parent.parent / "yang_modules"
path_inpkg = Path(yang_sid.__file__).parent / "yang_modules"

#datamodel = yang_sid.DataModel.from_file("yang-library.json", mod_path=('.', path, path_inpkg))
#datamodel.schema_data.load_all_sid_files(sid_path=("./sid",))

#print("sid assignment complete:", datamodel.schema_data.sid_is_complete())

