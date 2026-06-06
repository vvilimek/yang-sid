# yang-sid

Python 3 library built on top of yangson adding support for parsing SID Files and assigning loaded SIDs to schema nodes.
SID are formally defined in document RFC9254, SID Files are defined in RFC9595. The yang-sid is built on top of [Yangson](https://gitlab.nic.cz/labs/yangson),
more specificaly my own fork with some moficition making the code more extensible [Yangson/extension fork](https://github.com/vvilimek/yangson).

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

# CLI: SID prices

Run from project root directory

```sh
uv run yang-sid -t -p yang_modules:src/yang_sid/yang_modules --sid --sid-price --sid-path sid lib/system-lib.json
```

Explanation: The `-t` argument denotes that a YANG ascii tree representation should be printed.
The `-p` argument specifies YANG Module path. The `--sid` argument enables printing of SID numbers,
the `--sid-price` addes the CBOR encoding prices (in number of bytes). The `--sid-path` is YANG '.sid' File
path, and it is similar to the `-p` argument. The `lib/system-lib.json` is YANG Library as of [RFC7895](https://datatracker.ietf.org/doc/html/rfc7895).

```
+---x ietf-system:set-current-datetime SID(1715) price 3
|  +--ro input SID(1716) price 1
|  |  +--ro current-datetime SID(1717) price 1
|  +--ro output SID(1718) price 1
+--rw ietf-system:system SID(1719) price 3
|  +--rw clock SID(1744) price 2
|  |  +--rw timezone
|  |     +-- timezone-utc-offset
|  |        +--rw timezone-utc-offset SID(1746) price 1
|  +--rw contact SID(1747) price 2
|  +--rw dns-resolver SID(1748) price 2
|  |  +--rw options SID(1749) price 1
|  |  |  +--rw attempts SID(1750) price 1
|  |  |  +--rw timeout SID(1751) price 1
|  |  +--rw search SID(1752) price 1
|  |  +--rw server SID(1753) price 1
|  |     +--rw name SID(1754) price 1
|  |     +--rw transport
|  |        +-- udp-and-tcp
|  |           +--rw udp-and-tcp SID(1755) price 1
|  |              +--rw address SID(1756) price 1
|  +--rw hostname SID(1758) price 2
|  +--rw location SID(1759) price 2
+---x ietf-system:system-restart SID(1720) price 3
|  +--ro input SID(1721) price 1
|  +--ro output SID(1722) price 1
+---x ietf-system:system-shutdown SID(1723) price 3
|  +--ro input SID(1724) price 1
|  +--ro output SID(1725) price 1
+--ro ietf-system:system-state SID(1726) price 3
   +--ro clock SID(1727) price 1
   |  +--ro boot-datetime SID(1728) price 1
   |  +--ro current-datetime SID(1729) price 1
   +--ro platform SID(1730) price 1
      +--ro machine SID(1731) price 1
      +--ro os-name SID(1732) price 1
      +--ro os-release SID(1733) price 1
      +--ro os-version SID(1734) price 1

Total price: 49
```

Note that the current version of the code is not optimal: 
 - Code assumes whole data model to have SID to produce valid prices.
 - No data model restriction is available.
 - List are counted as if they have only a single entry.

