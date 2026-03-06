load("//tools:cpplint.bzl", "cpplint")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "canbus_%(car_type)s_protocol",
    srcs = glob([
        "*.cc",
    ]),
    hdrs = glob([
        "*.h",
    ]),
    deps = [
        "//modules/common_msgs/chassis_msgs:chassis_detail_cc_proto",
        "//modules/canbus/vehicle/%(car_type)s/proto:%(car_type)s_cc_proto",
        "//modules/canbus/vehicle:chassis_extension_tools",
        "//modules/drivers/canbus/can_comm:message_manager_base",
        "//modules/drivers/canbus/common:canbus_common",
    ],
)

cpplint()
