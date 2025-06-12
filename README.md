## Gen Vehicle Protocol Tool

`adbctool` is a convinent tool to let you quickly generate a nearly complete code for a new vehicle for [Apollo](https://github.com/ApolloAuto/apollo).

You only have to do is to have the dbc file (which is a communication protocol for the car, which is usually made by the vehicle integrated company), and write a less 10 lines config for generate an encode/decode.

## How to get vehicle's DBC file

- [opendbc](https://github.com/commaai/opendbc) is a project that opens the vehicle dbc protocol.
- [openvehicles](https://docs.openvehicles.com/en/latest/index.html) is an open car project that contains any vehicle information you want to know.
- [whl-vehicles](https://github.com/daohu527/vehicles) Apollo vehicle protocols based by opendbc.

## Quick start

#### Install

You can install adbctool by following cmd.

```shell
pip3 install adbctool
```

## Example

Generate c++ code based on dbc file.

- `vehicle dbc file `: vehicle's dbc file
- `vehicle type`: vehicle type
- `sender`: the sender of the message, the control protocol template will be used for sender

```shell
# adbctool -f <vehicle.dbc> -t <vehicle_type> --sender <sender>
adbctool -f test/acura_ilx_2016_nidec.dbc -t acura_ilx --sender ADAS
```
