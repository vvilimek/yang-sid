# yang-sid

Python 3 library built on top of yangson adding support for parsing SID Files and assigning loaded SIDs to schema nodes.
SID are formally defined in document RFC9254, SID Files are defined in RFC9595.

[[RFC9595](https://datatracker.ietf.org/doc/rfc9595/)]: YANG Schema Item iDentifier (YANG SID)
[[RFC9254](https://datatracker.ietf.org/doc/rfc9254/>)]: Encoding of Data Modeled with YANG in the Concise Binary Object Representation (CBOR)

# Installation

### pip
```
pip install git+https://github.com/vvilimek/yang-sid
```

### uv
```
uv add git+https://github.com/vvilimek/yang-sid
```

### poetry
```
poetry add git+https://github.com/vvilimek/yang-sid
```

# Quick start

```python3
import yang_sid

model = yang_sid.DataModel.from_file("yang_library.json", mod_path=(".", "/path/to/yang-modules"))
model.set_sid_path("/path/to/sid-files")
model.load_all_module_sids()
```

Note that while the package name is `yang-sid`, it is not valid python identifier so you must use `yang_sid` to import the package in python.
