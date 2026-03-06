// Copyright 2026 WheelOS All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "modules/canbus/vehicle/%(car_type_lower)s/%(car_type_lower)s_controller.h"

#include "modules/canbus/vehicle/%(car_type_lower)s/proto/%(car_type_lower)s.pb.h"
#include "modules/common_msgs/basic_msgs/vehicle_signal.pb.h"

#include "cyber/common/log.h"
#include "cyber/time/time.h"
#include "modules/canbus/vehicle/%(car_type_lower)s/%(car_type_lower)s_message_manager.h"
#include "modules/canbus/vehicle/chassis_extension_tools.h"
#include "modules/canbus/vehicle/vehicle_controller.h"
#include "modules/drivers/canbus/can_comm/can_sender.h"
#include "modules/drivers/canbus/can_comm/protocol_data.h"

namespace apollo {
namespace canbus {
namespace %(car_type_lower)s {

using ::apollo::drivers::canbus::ProtocolData;
using ::apollo::common::ErrorCode;
using ::apollo::control::ControlCommand;

namespace {
const int32_t kMaxFailAttempt = 10;
const int32_t CHECK_RESPONSE_STEER_UNIT_FLAG = 1;
const int32_t CHECK_RESPONSE_SPEED_UNIT_FLAG = 2;
}  // namespace

ErrorCode %(car_type_cap)sController::Init(
    const VehicleParameter& params,
    CanSender<::apollo::canbus::ChassisDetail> *const can_sender,
    MessageManager<::apollo::canbus::ChassisDetail> *const message_manager) {
  if (is_initialized_) {
    AINFO << "%(car_type_cap)sController has already been initiated.";
    return ErrorCode::CANBUS_ERROR;
  }

  vehicle_params_.CopyFrom(
      common::VehicleConfigHelper::Instance()->GetConfig().vehicle_param());
  params_.CopyFrom(params);
  if (!params_.has_driving_mode()) {
    AERROR << "Vehicle conf pb not set driving_mode.";
    return ErrorCode::CANBUS_ERROR;
  }

  if (can_sender == nullptr) return ErrorCode::CANBUS_ERROR;
  can_sender_ = can_sender;

  if (message_manager == nullptr) {
    AERROR << "protocol manager is null.";
    return ErrorCode::CANBUS_ERROR;
  }
  message_manager_ = message_manager;

%(protocol_ptr_get_logic)s
%(protocol_sender_add_logic)s

  AINFO << "%(car_type_cap)sController is initialized.";

  is_initialized_ = true;
  return ErrorCode::OK;
}

%(car_type_cap)sController::~%(car_type_cap)sController() {}

bool %(car_type_cap)sController::Start() {
  if (!is_initialized_) {
    AERROR << "%(car_type_cap)sController has NOT been initiated.";
    return false;
  }
  const auto& update_func = [this] { SecurityDogThreadFunc(); };
  thread_.reset(new std::thread(update_func));
  return true;
}

void %(car_type_cap)sController::Stop() {
  if (!is_initialized_) {
    AERROR << "%(car_type_cap)sController stops or starts improperly!";
    return;
  }

  if (thread_ != nullptr && thread_->joinable()) {
    thread_->join();
    thread_.reset();
    AINFO << "%(car_type_cap)sController stopped.";
  }
}

Chassis %(car_type_cap)sController::chassis() {
  chassis_.Clear();

  ChassisDetail chassis_detail;
  message_manager_->GetSensorData(&chassis_detail);

  if (driving_mode() == Chassis::EMERGENCY_MODE) {
    set_chassis_error_code(Chassis::NO_ERROR);
  }

  chassis_.set_driving_mode(driving_mode());
  chassis_.set_error_code(chassis_error_code());
  chassis_.set_engine_started(true);

%(chassis_detail_mapping_logic)s

  return chassis_;
}

void %(car_type_cap)sController::Emergency() {
  set_driving_mode(Chassis::EMERGENCY_MODE);
  ResetProtocol();
}

ErrorCode %(car_type_cap)sController::EnableAutoMode() {
  if (driving_mode() == Chassis::COMPLETE_AUTO_DRIVE) {
    AINFO << "already in COMPLETE_AUTO_DRIVE mode";
    return ErrorCode::OK;
  }

%(enable_auto_mode_impl)s

  can_sender_->Update();
  const int32_t flag = CHECK_RESPONSE_STEER_UNIT_FLAG | CHECK_RESPONSE_SPEED_UNIT_FLAG;
  if (!CheckResponse(flag, true)) {
    AERROR << "Failed to switch to COMPLETE_AUTO_DRIVE mode.";
    Emergency();
    set_chassis_error_code(Chassis::CHASSIS_ERROR);
    return ErrorCode::CANBUS_ERROR;
  }
  set_driving_mode(Chassis::COMPLETE_AUTO_DRIVE);
  AINFO << "Switch to COMPLETE_AUTO_DRIVE mode ok.";
  return ErrorCode::OK;
}

ErrorCode %(car_type_cap)sController::DisableAutoMode() {
  ResetProtocol();
  can_sender_->Update();
  set_driving_mode(Chassis::COMPLETE_MANUAL);
  set_chassis_error_code(Chassis::NO_ERROR);
  AINFO << "Switch to COMPLETE_MANUAL ok.";
  return ErrorCode::OK;
}

ErrorCode %(car_type_cap)sController::EnableSteeringOnlyMode() {
%(enable_steering_only_mode_impl)s
}

ErrorCode %(car_type_cap)sController::EnableSpeedOnlyMode() {
%(enable_speed_only_mode_impl)s
}

void %(car_type_cap)sController::Gear(Chassis::GearPosition gear_position) {
  if (driving_mode() != Chassis::COMPLETE_AUTO_DRIVE &&
      driving_mode() != Chassis::AUTO_SPEED_ONLY) return;
%(gear_impl_logic)s
}

void %(car_type_cap)sController::Brake(double pedal) {
  if (driving_mode() != Chassis::COMPLETE_AUTO_DRIVE &&
      driving_mode() != Chassis::AUTO_SPEED_ONLY) return;
%(brake_impl_logic)s
}

void %(car_type_cap)sController::Throttle(double pedal) {
  if (driving_mode() != Chassis::COMPLETE_AUTO_DRIVE &&
      driving_mode() != Chassis::AUTO_SPEED_ONLY) return;
%(throttle_impl_logic)s
}

void %(car_type_cap)sController::Speed(double speed) {
  if (driving_mode() != Chassis::COMPLETE_AUTO_DRIVE &&
      driving_mode() != Chassis::AUTO_SPEED_ONLY) return;
%(speed_impl_logic)s
}

void %(car_type_cap)sController::Acceleration(double acc) {
  if (driving_mode() != Chassis::COMPLETE_AUTO_DRIVE &&
      driving_mode() != Chassis::AUTO_SPEED_ONLY) return;
%(acceleration_impl_logic)s
}

void %(car_type_cap)sController::Steer(double angle) {
  if (driving_mode() != Chassis::COMPLETE_AUTO_DRIVE &&
      driving_mode() != Chassis::AUTO_STEER_ONLY) return;
%(steer_impl_logic)s
}

void %(car_type_cap)sController::Steer(double angle, double angle_spd) {
  if (driving_mode() != Chassis::COMPLETE_AUTO_DRIVE &&
      driving_mode() != Chassis::AUTO_STEER_ONLY) return;
%(steer_with_spd_impl_logic)s
}

void %(car_type_cap)sController::SetEpbBreak(const ControlCommand& command) {
%(epb_impl_logic)s
}

void %(car_type_cap)sController::SetBeam(const ControlCommand& command) {
%(beam_impl_logic)s
}

void %(car_type_cap)sController::SetHorn(const ControlCommand& command) {
%(horn_impl_logic)s
}

void %(car_type_cap)sController::SetTurningSignal(const ControlCommand& command) {
%(turn_signal_impl_logic)s
}

void %(car_type_cap)sController::ResetProtocol() {
  message_manager_->ResetSendMessages();
}

bool %(car_type_cap)sController::CheckChassisError() {
%(check_chassis_error_impl)s
}

void %(car_type_cap)sController::SecurityDogThreadFunc() {
  int32_t vertical_ctrl_fail = 0;
  int32_t horizontal_ctrl_fail = 0;

  if (can_sender_ == nullptr) return;
  while (!can_sender_->IsRunning()) { std::this_thread::yield(); }

  std::chrono::duration<double, std::micro> default_period{50000};
  while (can_sender_->IsRunning()) {
    int64_t start = ::apollo::cyber::Time::Now().ToMicrosecond();
    const Chassis::DrivingMode mode = driving_mode();
    bool emergency_mode = false;

    // 1. Horizontal control check
    if ((mode == Chassis::COMPLETE_AUTO_DRIVE || mode == Chassis::AUTO_STEER_ONLY) &&
        !CheckResponse(CHECK_RESPONSE_STEER_UNIT_FLAG, false)) {
      ++horizontal_ctrl_fail;
      if (horizontal_ctrl_fail >= kMaxFailAttempt) {
        emergency_mode = true;
        set_chassis_error_code(Chassis::MANUAL_INTERVENTION);
      }
    } else {
      horizontal_ctrl_fail = 0;
    }

    // 2. Vertical control check
    if ((mode == Chassis::COMPLETE_AUTO_DRIVE || mode == Chassis::AUTO_SPEED_ONLY) &&
        !CheckResponse(CHECK_RESPONSE_SPEED_UNIT_FLAG, false)) {
      ++vertical_ctrl_fail;
      if (vertical_ctrl_fail >= kMaxFailAttempt) {
        emergency_mode = true;
        set_chassis_error_code(Chassis::MANUAL_INTERVENTION);
      }
    } else {
      vertical_ctrl_fail = 0;
    }

    if (CheckChassisError()) {
      set_chassis_error_code(Chassis::CHASSIS_ERROR);
      emergency_mode = true;
    }

    if (emergency_mode && mode != Chassis::EMERGENCY_MODE) {
      set_driving_mode(Chassis::EMERGENCY_MODE);
      message_manager_->ResetSendMessages();
    }

    int64_t end = ::apollo::cyber::Time::Now().ToMicrosecond();
    std::chrono::duration<double, std::micro> elapsed{end - start};
    if (elapsed < default_period) {
      std::this_thread::sleep_for(default_period - elapsed);
    } else {
      AERROR << "Too much time consumption in %(car_type_cap)sController loop:" << elapsed.count();
    }
  }
}

bool %(car_type_cap)sController::CheckResponse(const int32_t flags, bool need_wait) {
%(check_response_impl)s
}

void %(car_type_cap)sController::set_chassis_error_mask(const int32_t mask) {
  std::lock_guard<std::mutex> lock(chassis_mask_mutex_);
  chassis_error_mask_ = mask;
}

int32_t %(car_type_cap)sController::chassis_error_mask() {
  std::lock_guard<std::mutex> lock(chassis_mask_mutex_);
  return chassis_error_mask_;
}

Chassis::ErrorCode %(car_type_cap)sController::chassis_error_code() {
  std::lock_guard<std::mutex> lock(chassis_error_code_mutex_);
  return chassis_error_code_;
}

void %(car_type_cap)sController::set_chassis_error_code(const Chassis::ErrorCode& error_code) {
  std::lock_guard<std::mutex> lock(chassis_error_code_mutex_);
  chassis_error_code_ = error_code;
}

}  // namespace %(car_type_lower)s
}  // namespace canbus
}  // namespace apollo
