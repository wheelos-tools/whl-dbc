# adbctool

## Overview

`adbctool` is a Python command-line tool for generating vehicle protocol
source files from a CAN DBC file. It parses message and signal metadata,
classifies messages as control or report messages, and generates:

- a protobuf file for the vehicle protocols;
- C++ protocol header and source files;
- vehicle controller, message manager, and vehicle factory files;
- `BUILD` files for the generated directories.

The parser runs in strict DBC mode by default. Non-standard comment lines such
as `# ...` and `// ...` are rejected; use standard `CM_ ...` DBC comment entries
instead.

## Role in WheelOS

This repository is a **Tools** component in WheelOS. It converts a vehicle's
DBC definition into source artifacts that can be incorporated into the
vehicle CAN bus integration layer.

```text
WheelOS
 |
+--- Tools
     |
     +--- adbctool
```

## Architecture

```text
vehicle.dbc
    |
    v
extract_dbc_meta
    |
    +--> dbc.yml
            |
            +--> gen_proto_file
            |       +--> vehicle/<car_type>/proto/<car_type>.proto
            |       +--> vehicle/<car_type>/proto/BUILD
            |
            +--> gen_protocols
            |       +--> vehicle/<car_type>/protocol/*.h
            |       +--> vehicle/<car_type>/protocol/*.cc
            |       +--> vehicle/<car_type>/protocol/BUILD
            |
            +--> gen_vehicle_controller_and_manager
                    +--> vehicle/<car_type>/*_controller.*
                    +--> vehicle/<car_type>/*_message_manager.*
                    +--> vehicle/<car_type>/*_vehicle_factory.*
                    +--> vehicle/<car_type>/BUILD
```

The `adbctool` entry point in `pyproject.toml` invokes `adbctool.gen:main`.
The generated output directory defaults to `output/`.

## Installation

The package requires Python `>=3.6` and declares the runtime dependencies
`pyyaml` and `chardet`.

For local development, install the repository in editable mode:

```shell
python -m pip install -U pip setuptools
python -m pip install -e .
```

The package is also published as `adbctool`:

```shell
pip3 install adbctool
```

## Examples

Generate artifacts using the sender node name:

```shell
adbctool \
  -f test/acura_ilx_2016_nidec.dbc \
  -t acura_ilx \
  --sender ADAS
```

Alternatively, classify control messages by CAN message IDs. IDs are
hexadecimal:

```shell
adbctool \
  -f test/acura_ilx_2016_nidec.dbc \
  -t acura_ilx \
  --sender_list 0x400
```

The generated files are written below
`output/vehicle/acura_ilx/` by default. The command also writes the
intermediate `dbc.yml` in the current working directory.

Run the repository tests with:

```shell
python -m unittest discover -s test
```

## Documentation

- [Package configuration and CLI entry point](pyproject.toml)
- [DBC metadata extraction](adbctool/extract_dbc_meta.py)
- [Generation pipeline](adbctool/gen.py)
- [Generated-file tests](test/test_generation_pipeline.py)
- [CLI tests](test/test_gen_cli.py)
- [DBC parser tests](test/test_extract_dbc_meta.py)
- [Apache License 2.0](LICENSE)
- [opendbc](https://github.com/commaai/opendbc)
- [Open Vehicles documentation](https://docs.openvehicles.com/en/latest/index.html)
- [WheelOS vehicle protocols](https://github.com/daohu527/vehicles)
