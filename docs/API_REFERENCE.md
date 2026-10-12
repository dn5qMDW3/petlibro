# PETLIBRO Cloud API Reference

> Extracted from PETLIBRO Android app v1.7.90 (Flutter/Dart) and verified against live API.
> Re-checked against app v1.9.40 on 2026-10-12 by static analysis only (`blutter` on
> `libapp.so`, Dart 3.11.5) — see [App 1.9.40 Notes](#app-1940-notes). Rows whose method
> is `?` come from that pass: the path and request keys are read from the app's code, but
> the HTTP method and the response have not been seen on the wire. A few of them were then
> read live on 2026-10-12 and carry their real method.
> Base URL: `https://api.us.petlibro.com` (US region)
> Last updated: 2026-10-12

## Table of Contents

- [Authentication](#authentication)
- [Request Format](#request-format)
- [Response Format](#response-format)
- [Endpoints by Category](#endpoints-by-category)
  - [Auth & Account](#auth--account)
  - [Device Management](#device-management)
  - [Device Data (Read)](#device-data-read)
  - [Device Settings (Write)](#device-settings-write)
  - [Device Commands](#device-commands)
  - [Feeding Plans (Dry)](#feeding-plans-dry)
  - [Feeding Plans (Wet)](#feeding-plans-wet)
  - [Feeding Plan Templates](#feeding-plan-templates)
  - [Clean Plans (Litter Box)](#clean-plans-litter-box)
  - [Maintenance & Resets](#maintenance--resets)
  - [Work Records & Events](#work-records--events)
  - [Water/Drinking Data](#waterdrinking-data)
  - [Pet Data](#pet-data)
  - [Pet Management](#pet-management)
  - [Pet Health Care](#pet-health-care)
  - [RFID & Wearables](#rfid--wearables)
  - [Device Sharing](#device-sharing)
  - [Device Audio](#device-audio)
  - [Firmware/OTA](#firmwareota)
  - [Camera/Video (TUTK)](#cameravideo-tutk)
  - [Notifications & Messages](#notifications--messages)
  - [Rooms](#rooms)
  - [App & System](#app--system)
- [Live API Response Examples](#live-api-response-examples)
- [App 1.9.40 Notes](#app-1940-notes)
- [Integration Coverage](#integration-coverage)

---

## Authentication

### Login
```
POST /member/auth/login
```

**Headers:**
```
Content-Type: application/json
source: ANDROID
language: EN
timezone: America/Chicago
version: 1.3.45
```

**Body:**
```json
{
  "appId": 1,
  "appSn": "c35772530d1041699c87fe62348507a8",
  "country": "US",
  "email": "user@example.com",
  "password": "<md5-hashed-password>",
  "phoneBrand": "",
  "phoneSystemVersion": "",
  "timezone": "America/Chicago",
  "thirdId": null,
  "type": null
}
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "token": "0123456789abcdef0123456789abcdef",
    "clientId": "APP_1234567890",
    "memberId": 1234567890,
    "account": "user@example.com",
    "email": "user@example.com",
    "country": "US",
    "area": "US",
    "petCareKind": "FREE"
  }
}
```

**Notes:**
- Password must be MD5-hashed before sending
- Token is passed via `token` header on all subsequent requests
- Code `1009` = `NOT_YET_LOGIN` — trigger re-login
- Code `1025` = `FORCED_LOGOUT` — session expired, must re-login

---

## Request Format

All endpoints use `POST` unless noted. All requests include:

**Headers (required on all requests):**
```
Content-Type: application/json
source: ANDROID
language: EN
timezone: <timezone>
version: 1.3.45
token: <auth-token>
```

**Device-scoped requests typically include:**
```json
{
  "id": "<deviceSn>",
  "deviceSn": "<deviceSn>"
}
```

---

## Response Format

All responses follow:
```json
{
  "code": 0,
  "msg": null,
  "data": { ... }
}
```

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1001` | System error |
| `1002` | Validation error (missing required fields) |
| `1006` | Method not supported |
| `1009` | NOT_YET_LOGIN — token expired |
| `1025` | FORCED_LOGOUT — session invalidated |

**Note:** `data` can be `null`, `{}`, `[]`, or a populated object depending on the endpoint.

---

## Endpoints by Category

### Auth & Account

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/member/auth/login` | POST | Authenticate and get token | ✅ |
| `/member/auth/logout` | POST | Invalidate token | ✅ |
| `/member/auth/register` | POST | Create new account | |
| `/member/auth/checkLogin` | POST | Verify token validity | |
| `/member/auth/checkActive` | POST | Check account activation | |
| `/member/auth/sendActive` | POST | Send activation email | |
| `/member/auth/sendRetrieve` | POST | Password recovery email | |
| `/member/auth/thirdLoginV2` | POST | Third-party OAuth login | |
| `/member/auth/enableCancellation` | POST | Account deletion request | |
| `/member/member/info` | POST | Get account/member info | ✅ |
| `/member/member/updateInfo` | POST | Update account info | ✅ |
| `/member/member/getSetting` | POST | Get account settings | |
| `/member/member/updateSetting` | POST | Update account settings | ✅ |
| `/member/member/getDeviceSetting` | POST | Get device-specific member settings | |
| `/member/member/updateDeviceSetting` | POST | Update device-specific member settings | |
| `/member/member/updatePsw` | POST | Change password | |
| `/member/member/checkChangeEmail` | POST | Verify email change | |
| `/member/member/sendChangeEmail` | POST | Send email change confirmation | |
| `/member/member/sendNewEmail` | POST | Send new email verification | |
| `/member/member/realChangeNewEmail` | POST | Execute email change | |

---

### Device Management

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/device/list` | POST | List all devices on account | ✅ |
| `/device/device/simpleList` | POST | Simplified device list | |
| `/device/device/baseInfo` | POST | Device base settings/config | ✅ |
| `/device/device/realInfo` | POST | Real-time device state | ✅ |
| `/device/device/checkDeviceBind` | POST | Check if device is bound | |
| `/device/device/checkBindFailLog` | POST | Check binding failure logs | |
| `/device/device/boundMessage` | POST | Get device binding messages | |
| `/device/device/unbind` | POST | Unbind/remove device | |
| `/device/device/updateName` | POST | Rename device | |
| `/device/device/updateRoom` | POST | Assign device to room | ✅ |
| `/device/device/updateDeviceImage` | POST | Change device image | |
| `/device/device/wifiInfo` | POST | Get WiFi connection info | |
| `/device/device/wifiChangeService` | POST | Initiate WiFi change | |
| `/device/device/wifiReconnect` | POST | Reconnect WiFi | |
| `/device/device/getSuspendInfo` | POST | Current operation of a litter box: action, state and progress (see [App 1.9.40 Notes](#app-1940-notes)) | ✅ |
| `/device/device/resume` | POST | Resume suspended device | |
| `/device/device/reset` | POST | Factory reset device | |
| `/device/device/hardVersionCompatible` | POST | Check hardware version compatibility | |
| `/device/device/savePurchaseChannel` | POST | Save purchase channel info | |
| `/device/device/getPurchaseChannel` | POST | Get purchase channel info | |
| `/device/device/saveStarRating` | POST | Submit device rating | |
| `/device/device/functionTest` | POST | Run device function test | |
| `/device/device/initializeSDCard` | POST | Format SD card | |
| `/device/product/getByIdentifier` | POST | Get product info by identifier | |
| `/device/product/connectGuide` | POST | Get device setup guide | |
| `/device/product/petlibroCategoryTree` | POST | Get product category tree | |

---

### Device Data (Read)

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/data/data/realInfo` | POST | Extended real-time data (fountains, litter boxes) | ✅ |
| `/device/data/grainStatus` | POST | Feeding statistics (feeders) | ✅ |
| `/device/data/petGrainStatus` | POST | Per-pet feeding statistics | |
| `/device/data/petPeriodGrain` | POST | Per-pet periodic feeding data | |
| `/device/setting/getAttributeSetting` | POST | Device configuration settings | ✅ |
| `/device/setting/getNoticeSetting` | POST | Notification settings | ✅ |

---

### Device Settings (Write)

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/setting/updateLightingSetting` | POST | Light on/off + scheduling | ✅ |
| `/device/setting/updateLightSwitch` | POST | Light switch toggle | ✅ |
| `/device/setting/updateLightEnableSwitch` | POST | Enable/disable light feature | ✅ |
| `/device/setting/updateSoundSetting` | POST | Sound on/off + scheduling | ✅ |
| `/device/setting/updateSoundSwitch` | POST | Sound switch toggle | ✅ |
| `/device/setting/updateSoundEnableSwitch` | POST | Enable/disable sound feature | ✅ |
| `/device/setting/updateVolumeSetting` | POST | Set speaker volume | ✅ |
| `/device/setting/updateCameraSetting` | POST | Camera settings | |
| `/device/setting/updatePCCameraSetting` | POST | PC camera settings | |
| `/device/setting/updateDetectionSetting` | POST | Motion/pet detection | |
| `/device/setting/updateSleepModeSetting` | POST | Sleep mode + sub-settings | ✅ |
| `/device/setting/updateCleanModeSetting` | POST | Auto/manual clean mode | ✅ |
| `/device/setting/updateDeodorizationSetting` | POST | Deodorization mode/speed/switch | ✅ |
| `/device/setting/updateCoverSetting` | POST | Lid open mode/speed/close time | ✅ |
| `/device/setting/updateCloseDoorTimeSetting` | POST | Door close delay time | |
| `/device/setting/updateBowlModeSetting` | POST | Single/dual bowl mode | |
| `/device/setting/updateDisplayMatrixSetting` | POST | LED display matrix config | ✅ |
| `/device/setting/updateAutoUpgradeSwitch` | POST | Auto firmware upgrade toggle | |
| `/device/setting/otaSetting` | ? | Firmware settings. Body `deviceSn`, `upgradeNoticeSwitch`, `autoUpgradeSwitch` | |
| `/device/setting/updateMealCallSetting` | ? | Meal call. Body `deviceSn`, `mealCallSwitch`, `mealCallTimes`, `mealCallApply` | |
| `/device/setting/updateFeedingPlanSwitch` | POST | Enable/disable feeding plans | ✅ |
| `/device/setting/updateRingerMode` | POST | Bell/ringer mode | |
| `/device/setting/updateRadarSetting` | POST | Radar sensing level | ✅ |
| `/device/setting/updateLowWaterSetting` | POST | Low water threshold | ✅ |
| `/device/setting/updateChildLockSwitch` | POST | Child lock toggle | ✅ |
| `/device/setting/updateNoticeSetting` | POST | General notification settings | |
| `/device/setting/updateFeedingNoticeSetting` | POST | Feeding notifications | ✅ |
| `/device/setting/updateOfflineNoticeSetting` | POST | Offline notifications | ✅ |
| `/device/setting/updateLowBatteryNoticeSetting` | POST | Low battery notifications | ✅ |
| `/device/setting/updatePowerChangeNoticeSetting` | POST | Power change notifications | ✅ |
| `/device/setting/updateVacuumSuccessNoticeSetting` | POST | Vacuum success notifications | ✅ |
| `/device/setting/updateVacuumFailedNoticeSetting` | POST | Vacuum fail notifications | ✅ |
| `/device/setting/updateSurplusGrainNoticeSetting` | POST | Food level notifications | ✅ |
| `/device/setting/updateGrainOutletBlockedNoticeSetting` | POST | Food outlet blocked notifications | ✅ |
| `/device/setting/updateMotionDetectionNoticeSetting` | POST | Motion detection notifications | ✅ |
| `/device/setting/updateSoundDetectionNoticeSetting` | POST | Sound detection notifications | ✅ |
| `/device/setting/updateDrinkTrendNoticeSetting` | POST | Drinking trend notifications | ✅ |
| `/device/setting/updateNoDrinkNoticeSetting` | POST | No-drink alert notifications | ✅ |
| `/device/setting/updateLocationReminderSetting` | POST | Location-based reminders | |
| `/device/setting/updateDesiccantNoticeSetting` | POST | Desiccant replacement notifications | ✅ |
| `/device/setting/dailyDrinkGoalSetting` | POST | Set daily drinking goal | |
| `/device/setting/enableDeviceShare` | POST | Enable device sharing | ✅ |
| `/device/setting/enableDeviceAiAssistance` | POST | Enable AI assistant | |
| `/device/setting/enableDrinkingWaterNotice` | POST | Drinking water notifications | ✅ |
| `/device/setting/enableFilterReplacementReminder` | POST | Filter replacement reminder | ✅ |
| `/device/setting/enableMachineCleaningReminder` | POST | Machine cleaning reminder | ✅ |
| `/device/setting/enableLowWaterNotice` | POST | Low water notification | ✅ |
| `/device/setting/enableReachDrinkingWaterAlertNotice` | POST | Drinking goal alert | ✅ |
| `/device/setting/enableTankOverturnedNotice` | POST | Tank overturned notification | ✅ |

---

### Device Commands

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/device/execCmdService` | POST | Execute device command (see actions below) | ✅ |
| `/device/device/manualFeeding` | POST | Manual feed (feeders) | ✅ |
| `/device/device/vacuum` | POST | Set vacuum mode | ✅ |
| `/device/device/doorStateChange` | POST | Open/close door/lid | ✅ |
| `/device/device/displayMatrix` | POST | Set LED display content | ✅ |
| `/device/device/waterModeSetting` | POST | Set water dispensing mode | ✅ |
| `/device/device/wetFoodFeedNow` | POST | Trigger wet food feed | |
| `/device/device/weighingCalibration` | POST | Calibrate weight sensor | |
| `/device/device/weighingPeeling` | POST | Tare/zero the scale | |
| `/device/device/releaseMotorStuck` | ? | Litter box: release a stuck motor. Body `deviceSn` | |
| `/device/device/releaseAntiPinch` | ? | Release the anti-pinch stop. Body `deviceSn`, `type` | |
| `/device/lockedRotor/diagnostics` | ? | Litter box: start stuck-drum diagnostics. Body `deviceSn` | |
| `/device/lockedRotor/diagnosticsResult` | ? | Litter box: poll diagnostics. Body `deviceSn`, `diagId` | |
| `/device/device/pauseFreeFeed` | ? | Pause free feeding. Body `deviceSn`, `step` | |
| `/device/device/stopFeeding` | ? | Stop a feed in progress | |
| `/device/device/playVoice` | ? | Play a sound on the device. Body `deviceSn`, `type` | |
| `/device/device/wakeUpCamera` | ? | Wake a sleeping camera. Body `deviceSn` | |
| `/device/device/bowlWeightClear` | ? | Zero the bowl scale | |

#### `execCmdService` Actions (Litter Box)

```json
{ "deviceSn": "<sn>", "action": "<ACTION>", "requestId": "<uuid>" }
```

| Action | Purpose |
|--------|---------|
| `CLEAN` | Start cleaning cycle |
| `STOP_CLEAN` | Stop cleaning |
| `SUSPEND_CLEAN` | Pause cleaning |
| `RESTART_CLEAN` | Resume cleaning |
| `EMPTY` | Empty waste bin |
| `STOP_EMPTY` | Stop emptying |
| `RESTART_EMPTY` | Resume emptying |
| `LEVELING` | Level litter |
| `RESTART_LEVELING` | Resume leveling |
| `VACUUM` | Run air purifier |
| `OPEN_DOOR` | Open door |
| `CLOSE_DOOR` | Close door |
| `STOP` | Stop current action |
| `CANCEL` | Cancel current action |

---

### Feeding Plans (Dry)

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/feedingPlan/list` | POST | List all feeding plans | ✅ |
| `/device/feedingPlan/todayNew` | POST | Today's feeding plan | ✅ |
| `/device/feedingPlan/add` | POST | Create feeding plan | ✅ |
| `/device/feedingPlan/update` | POST | Update feeding plan | ✅ |
| `/device/feedingPlan/remove` | POST | Delete feeding plan | ✅ |
| `/device/feedingPlan/enable` | POST | Enable/disable single plan | ✅ |
| `/device/feedingPlan/enableTodayAll` | POST | Enable/disable all today | ✅ |
| `/device/feedingPlan/enableTodaySingle` | POST | Enable/disable single plan today | ✅ |
| `/device/feedingPlan/petTodayEat` | POST | Get per-pet today's eating data | |

---

### Feeding Plans (Wet)

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/wetFeedingPlan/wetListV3` | POST | List wet food plans | ✅ |
| `/device/wetFeedingPlan/addFeedingPlanV3` | POST | Create wet food plan | |
| `/device/wetFeedingPlan/editFeedingPlanV3` | POST | Update wet food plan | |
| `/device/wetFeedingPlan/resetFeedingPlan` | POST | Reset all wet plans | |
| `/device/wetFeedingPlan/manualFeedNow` | POST | Manual wet feed | ✅ |
| `/device/wetFeedingPlan/stopFeedNow` | POST | Stop current wet feed | ✅ |
| `/device/wetFeedingPlan/feedAgain` | POST | Repeat last feed | |
| `/device/wetFeedingPlan/feedAudio` | POST | Play feeding audio | ✅ |
| `/device/wetFeedingPlan/feedConfig` | POST | Get feed configuration | |
| `/device/wetFeedingPlan/platePositionChange` | POST | Change plate position | ✅ |
| `/device/wetFeedingPlan/reposition` | POST | Reposition plate schedule | ✅ |
| `/device/wetFeedingPlan/executablePlanList` | POST | Get executable plan list | |
| `/device/wetFeedingPlan/offlineList` | POST | Get offline plan list | |
| `/device/wetFeedingPlan/verifyOffline` | POST | Verify offline plan | |
| `/device/wetFeedingPlan/hardVersionCap` | POST | Hardware version capabilities | |

---

### Feeding Plan Templates

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/feedingPlanTemplate/list` | POST | List templates | |
| `/device/feedingPlanTemplate/update` | POST | Update template | |
| `/device/feedingPlanTemplate/delete` | POST | Delete template | |
| `/device/feedingPlanTemplate/repeat` | POST | Repeat template | |
| `/device/feedingPlanTemplate/state` | POST | Template state | |
| `/device/feedingPlanTemplate/getMaxNumber` | POST | Max template count | |

---

### Clean Plans (Litter Box)

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/cleanPlan/getCleanPlan` | POST | Get scheduled clean plans | ✅ |
| `/device/cleanPlan/addCleanPlan` | POST | Add scheduled clean | ✅ |
| `/device/cleanPlan/updateCleanPlan` | POST | Update scheduled clean | ✅ |
| `/device/cleanPlan/delCleanPlan` | POST | Delete scheduled clean | ✅ |

---

### Maintenance & Resets

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/device/filterReset` | POST | Reset filter replacement timer | ✅ |
| `/device/device/machineCleaningReset` | POST | Reset cleaning timer | ✅ |
| `/device/device/matReset` | POST | Reset mat replacement timer | ✅ |
| `/device/device/desiccantReset` | POST | Reset desiccant timer | ✅ |
| `/device/device/maintenanceFrequencySetting` | POST | Set maintenance frequency | ✅ |
| `/device/device/maintenanceRecord` | GET | Get maintenance history | ✅ |
| `/device/device/maintain` | GET | Get maintenance info | ✅ |

---

### Work Records & Events

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/workRecord/list` | POST | Activity/work record history | ✅ |
| `/device/workRecord/getWorkRecordsCalendar` | POST | Calendar view of records | |
| `/device/workRecord/correct` | POST | Correct a work record | |
| `/device/workRecord/correctAddSample` | POST | Add correction sample | |
| `/device/workRecord/batchDelete` | POST | Batch delete records | |
| `/data/event/deviceEventsV2` | POST | Active events/alerts (v2) | ✅ |
| `/data/event/deviceEventsV3` | POST | Active events/alerts (v3) | |
| `/data/event/deviceSnackbar` | POST | Snackbar notifications | |
| `/data/event/verifyDeviceEvents` | POST | Verify/dismiss events | |

**workRecord/list request body:**
```json
{
  "deviceSn": "<sn>",
  "startTime": 1776000000000,
  "endTime": 1776300000000,
  "size": 25,
  "type": ["GRAIN_OUTPUT_SUCCESS"]
}
```

Record type filters:
- Feeders: `["GRAIN_OUTPUT_SUCCESS"]`
- Fountains: `["DRINK"]`
- Litter boxes: (unfiltered or device-specific types)

---

### Water/Drinking Data

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/data/deviceDrinkWater/todayDrinkData` | POST | Today's drinking stats | ✅ |
| `/data/deviceDrinkWater/history` | POST | Historical drinking data | |
| `/data/deviceDrinkWater/calendarList` | POST | Calendar view of drinking | |
| `/data/deviceDrinkWater/getAvgDailyConsumption` | POST | Average daily consumption | |
| `/data/deviceDrinkWater/achieveGoalsDataV2` | POST | Goal achievement data | |
| `/data/deviceDrinkWater/trendDetail` | POST | Drinking trend details | |
| `/data/deviceDrinkWater/trend` | POST | Drinking trends | |
| `/data/deviceDrinkWater/habitDetail` | POST | Drinking habit details | |
| `/data/deviceDrinkWater/habit` | POST | Drinking habits | |
| `/data/deviceDrinkWater/firstTrend/read` | POST | First trend read | |
| `/data/deviceDrinkWater/record/mark` | POST | Mark drinking record | |

---

### Pet Data

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/data/pet/potty/today` | POST | Today's potty stats (litter box) | ✅ |
| `/data/pet/potty/chart/detail` | POST | Potty chart data | |
| `/data/pet/potty/tipClick` | POST | Potty tip interaction | |
| `/data/pet/weight/today` | POST | Today's pet weight | |
| `/data/pet/weight/weekly` | POST | Weekly weight trends | |
| `/data/pet/activity/today` | POST | Today's pet activity | |
| `/data/pet/infoAndAlert` | POST | Pet health info & alerts | |
| `/data/pet/alert/today` | POST | Today's pet alerts | |
| `/data/pet/confirmWeight` | POST | Confirm pet weight reading | |
| `/data/pet/care/notification/page` | POST | Pet care notifications | |
| `/data/pet/care/notification/unread` | POST | Unread care notifications | |

**potty/today response:**
```json
{
  "code": 0,
  "data": {
    "times": 3,
    "duration": 245,
    "petList": [
      { "petId": 123, "petName": "Luna", "times": 2, "duration": 180 },
      { "petId": 456, "petName": "Max", "times": 1, "duration": 65 }
    ]
  }
}
```

---

### Pet Management

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/member/pet/list` | POST | List all pets | ✅ |
| `/member/pet/petBaseInfoList` | POST | Basic pet info list | |
| `/member/pet/detailV2` | POST | Pet details (v2) | ✅ |
| `/member/pet/saveOrUpdate` | POST | Create/update pet | ✅ |
| `/member/pet/delete` | POST | Delete pet | |
| `/member/pet/getLabels` | POST | Get pet labels | |
| `/member/pet/getCommonLabels` | POST | Get common labels | |
| `/member/pet/waterIntakeSetting` | POST | Set pet water intake | |
| `/device/devicePetRelation/getBoundPets` | POST | Get pets bound to device | ✅ |
| `/device/devicePetRelation/bindPets` | POST | Bind pets to device | |
| `/device/devicePetRelation/removePets` | POST | Remove pets from device | |
| `/device/devicePetRelation/getBoundDevices` | POST | Get devices bound to pet | ✅ |
| `/device/devicePetRelation/getBindableDevices` | POST | Get bindable devices | |

#### Pet AI (Embedding/Recognition)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/member/pet/embedding/addSample` | POST | Add pet recognition sample |
| `/member/pet/embedding/delete` | POST | Delete pet sample |
| `/member/pet/embedding/feedBackByMember` | POST | Feedback on recognition |
| `/member/pet/embedding/fullImageList` | POST | List all sample images |
| `/member/pet/embedding/replaceSample` | POST | Replace recognition sample |
| `/member/pet/embedding/sampleLimit` | POST | Get sample limits |
| `/member/pet/embedding/signedUrlListByFullImageIds` | POST | Get signed image URLs |

---

### Pet Health Care

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/member/healthCare/dashboardList` | POST | Health dashboard list | |
| `/member/healthCare/dashboardDetail` | POST | Health dashboard detail | |
| `/member/healthCare/getDashboardLayout` | POST | Dashboard layout | |
| `/member/healthCare/updateDashboardLayout` | POST | Update dashboard layout | |
| `/member/healthCare/getFirstClassification` | POST | Health categories | |
| `/member/healthCare/getPetGoal` | POST | Pet health goals | |
| `/member/healthCare/goalSetting` | POST | Set health goals | ✅ |
| `/member/healthCare/goalDistCal` | POST | Goal distance calculation | |
| `/member/healthCare/goalRecommendInfo` | POST | Goal recommendations | |
| `/member/healthCare/goalApplyToDevice` | POST | Apply goal to device | |
| `/member/healthCare/planInfo` | POST | Health plan info | |
| `/member/healthCare/addTraceV2` | POST | Add health trace | |
| `/member/healthCare/updateTraceV2` | POST | Update health trace | |
| `/member/healthCare/deleteTrace` | POST | Delete health trace | |
| `/member/healthCare/traceHistory` | POST | Trace history | |
| `/member/healthCare/traceQuantity` | POST | Trace quantities | |
| `/member/healthCare/traceAndCalenderV2` | POST | Traces with calendar | |
| `/member/healthCare/traceCalendarList` | POST | Trace calendar | |
| `/member/healthCare/updateTraceCompletedState` | POST | Mark trace complete | |
| `/member/healthCare/repeatTraceListV2` | POST | Repeating traces | |
| `/member/healthCare/updateRepeatTraceV2` | POST | Update repeating trace | |
| `/member/healthCare/enableRepeatTrace` | POST | Enable repeating trace | |
| `/member/healthCare/deleteRepeatTrace` | POST | Delete repeating trace | |
| `/member/healthCare/petBindDeviceList` | POST | Pet's bound device list | |

#### Pet Care data (per pet)

The app's pet dashboard. In 1.9.40 the per-metric history calls were replaced by one set
of `V2` calls that take a `type` — `WEIGHT`, `FOOD`, `WATER`, `FOOD_DISPENSED`,
`BATHROOM` or `ACTIVITY` (`FOOD_DISPENSED` is new in 1.9.40). The integration uses none
of these yet.

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/data/petCare/overviewV2` | POST | Overview for one metric. Body `petId`, `type` | |
| `/data/petCare/historyV2` | POST | History for one metric. Body `petId`, `type`, `dimension`, `startTime`, `endTime` | |
| `/data/petCare/highlightsV2` | POST | Highlights for one metric. Body `petId`, `type` | |
| `/data/petCare/abnormal/card` | POST | Abnormal-behaviour card. Body `petId`, `type` | |
| `/data/petCare/overview/activity` | POST | Activity overview. Body `petId` | |
| `/data/petCare/overview/bathroom` | POST | Bathroom overview. Body `petId` | |
| `/data/petCare/overview/water` | POST | Water overview. Body `petId` | |
| `/data/petCare/overview/weight` | POST | Weight overview. Body `petId` | |
| `/data/petCare/getInsight` | POST | Insight text. Body `petId` | |
| `/data/petCare/getShowModules` | GET | Which dashboard modules are shown. Returns `moduleOrders`, `hiddenModules`, `customSortMode`. POST is rejected with code 1006 | |
| `/data/petCare/manualSave` | ? | Save a manual entry | |

Read live on 2026-10-12 for one pet that has no device linked to it (`hasDevice: false`),
so every count was zero — the shapes are real, the units are not established:

- `overviewV2` returned data only for `type: "FOOD"`, and answered with
  `"type": "FOOD_DISPENSED"`: `times`, `total`, `trendData` (24 hourly slots, `null` for
  hours still to come), `hasDevice`, `hasG2Device`. Every other type returned `null`.
- `overview/water`: `times`, `total`, `changePercent`, `trendData`, `hasDevice`.
  `overview/bathroom`: `times`, `average`, `changePercent`, `trendDataWithFree`,
  `trendDataWithPay`, `hasDevice`. `overview/activity`: `times`, `trendData`,
  `hasDevice`. `overview/weight`: `weight`, `changePercent`, `trendData`, `hasDevice`.
- `historyV2` (`dimension` `DAY` and `WEEK` both accepted): `averageTimes`,
  `averageIntake`, `averageWeight`, `latestWeight`, `averageDuration`, and the series
  either as `data` (`xValue` / `yValue` pairs) or as `xdate` + `ydata`. For `BATHROOM`,
  `ydata` items are `{poopTimes, peeTimes, times}`.
- `highlightsV2`: `type`, `habit`, `communityRanking`. Rejects `FOOD_DISPENSED` with
  code 1002.
- `abnormal/card`: `hasBaseline`, `hasAbnormal`, `message`. Only `type: "WATER"` was
  accepted; the other types returned code 1002.
- `getInsight` returns a plain string — for this account an upsell for the paid Care
  plan, which the `…WithFree` / `…WithPay` split in the bathroom overview also points to.

These are keyed by the pet profiles in `/member/pet/list`. On the test account that list
held one pet, while the integration shows litter box visits for a second one, so not
every pet the integration knows about has a profile to query here. Where that second pet
comes from was not traced.

Removed from the app in 1.9.40 (present in 1.9.30): `/data/petCare/activity/history`,
`/data/petCare/bathroom/history`, `/data/petCare/food/intake/history`,
`/data/petCare/water/intake/history`, `/data/petCare/weight/history` and
`/data/petCare/overview/food`. Whether the server still answers them is untested.
(`/data/petCare/manualSave` is still method `?` — it is a write and was not called.)

---

### RFID & Wearables

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/device/addRfid` | POST | Add RFID tag | |
| `/device/device/discoveryRfid` | POST | Discover RFID tags | |
| `/device/device/discoveryStop` | POST | Stop RFID discovery | |
| `/device/device/getDefaultMatrix` | GET | Get RFID matrix data | ✅ |
| `/device/device/getMatrixConfig` | POST | Get matrix configuration | |
| `/device/device/getMatrixDictionary` | POST | Get matrix dictionary | |
| `/device/device/wear/wearListV2` | POST | List wearables | ✅ |
| `/device/device/wear/bindWearV2` | POST | Bind wearable | |
| `/device/device/wear/unbindWearV2` | POST | Unbind wearable | |
| `/device/device/wear/discoveryListV2` | POST | Discover wearables | |
| `/device/device/wear/getCollarDetail` | POST | Get collar details | |
| `/device/device/wear/getUserCollarList` | POST | List user collars | |
| `/device/device/wear/collarAddDevice` | POST | Add device to collar | |
| `/device/device/wear/delCollar` | POST | Delete collar | |
| `/device/device/wear/replaceCollar` | POST | Replace collar | |
| `/device/device/wear/qrCodeAddCollar` | POST | Add collar via QR code | |
| `/device/device/wear/getCollarAvaDeviceList` | POST | Available collar devices | |
| `/device/device/wear/bindWear` | POST | Bind wear (v1) | |

---

### Device Sharing

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/deviceShare/add` | POST | Share device | ✅ |
| `/device/deviceShare/remove` | POST | Remove share | ✅ |
| `/device/deviceShare/batchRemove` | POST | Batch remove shares | |
| `/device/deviceShare/cancel` | POST | Cancel pending share | |
| `/device/deviceShare/quit` | POST | Leave shared device | ✅ |
| `/device/deviceShare/retry` | POST | Retry failed share | |
| `/device/deviceShare/rec` | POST | Accept share invite | ✅ |
| `/device/deviceShare/verifyShare` | POST | Verify share code | ✅ |
| `/device/deviceShare/deviceShareList` | POST | Shared device list | |
| `/device/deviceShare/deviceSharedList` | POST | Devices shared with me | ✅ |
| `/device/deviceShare/deviceSharingList` | POST | Pending shares | ✅ |
| `/device/deviceShare/myShareList` | POST | My shares list | |
| `/device/deviceShare/mySharingDevices` | POST | Devices I'm sharing | ✅ |
| `/device/deviceShare/sharePopList` | POST | Share popup list | ✅ |
| `/device/deviceShare/deviceSelector` | POST | Device selector for sharing | |

---

### Device Audio

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/deviceAudio/all` | POST | List all audio files | ✅ |
| `/device/deviceAudio/add` | POST | Upload audio file | |
| `/device/deviceAudio/remove` | POST | Remove audio file | |
| `/device/deviceAudio/use` | POST | Set active audio | ✅ |

---

### Firmware/OTA

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/ota/getUpgrade` | POST | Check for firmware update | ✅ |
| `/device/ota/doUpgrade` | POST | Trigger firmware upgrade | ✅ |
| `/device/ota/getOtaItem` | POST | Get OTA item details | |
| `/member/app/ota` | POST | App update check | |

**getUpgrade response (when update available):**
```json
{
  "code": 0,
  "data": {
    "jobItemId": "abc123",
    "jobName": "Firmware Update",
    "targetVersion": "1.0.15",
    "upgradeDesc": "Bug fixes and improvements",
    "progress": 0
  }
}
```

**getUpgrade response (up-to-date):**
```json
{ "code": 0, "data": null }
```

---

### Camera/Video (TUTK)

The camera uses **TUTK/Kalay P2P SDK** — this is a peer-to-peer video protocol, not HTTP streaming. Not feasible for HA integration without native TUTK library.

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/member/third/tutk/info` | POST | Get TUTK credentials | |
| `/member/certificate/ca` | POST | Get CA certificate | ✅ |
| `/member/certificate/generate` | POST | Generate certificate | ✅ |
| `/member/certificate/confirm` | POST | Confirm certificate | ✅ |
| `/member/certificate/error` | POST | Report certificate error | |

**TUTK info response:**
```json
{
  "code": 0,
  "data": {
    "userToken": "GgNSaA6AAFcusPEvIGq2",
    "appTutkUrl": "https://us-vsaasapi-tutk.kalayservice.com/vsaas/api/v1/be/"
  }
}
```

**Camera connection uses:**
- `cameraId` from device list response
- `cameraAuthInfo` from device list response
- Native `android_tutk_camera_view` Flutter widget
- P2P connection via TUTK/IOTC SDK (libTUTKGlobalAPIsT.so, libIOTCAPIsT.so)

---

### Notifications & Messages

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/msg/page` | POST | Message list (paginated) | |
| `/device/msg/detail` | POST | Message detail | |
| `/device/msg/detailWithDel` | POST | Detail and delete | |
| `/device/msg/read` | POST | Mark message read | |
| `/device/msg/readAll` | POST | Mark all read | |
| `/device/msg/readBatch` | POST | Batch mark read | |
| `/device/msg/delBatch` | POST | Batch delete | |
| `/device/msg/unreadQuantity` | POST | Unread count | ✅ |
| `/device/msg/v2/dnd` | GET | Read the do-not-disturb window for push notifications. Returns `enable`, `startTime`, `endTime` (`"HH:MM"`), `repeatDays` (a JSON list in a string), `timezone`, `serverTime`. POST is rejected with code 1006 | |
| `/device/msg/v2/dnd/save` | ? | Set it. Body `enable`, `startTime`, `endTime` | |
| `/device/deviceTips/getTips` | POST | Get device tips | |
| `/device/deviceTips/disableTips` | POST | Disable a tip | |
| `/member/popup/create` | POST | Create popup | |
| `/member/findPet/detail` | POST | Lost pet detail | |
| `/member/findPet/publish` | POST | Publish lost pet | |
| `/member/findPet/upsertFindPet` | POST | Create/update lost pet | |

---

### Rooms

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/room/systemRooms` | POST | List system rooms | ✅ |
| `/device/room/addRoom` | POST | Add custom room | |
| `/device/room/upRoom` | POST | Update room | |
| `/device/room/delRoom` | POST | Delete room | |
| `/device/room/delRoomV2` | POST | Delete room (v2) | |

---

### App & System

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/member/app/config` | POST | App configuration | ✅ |
| `/member/app/commonConfig` | POST | Common config (authenticated) | |
| `/member/app/commonConfigWithoutLogin` | POST | Common config (unauthenticated) | |
| `/member/app/faq` | POST | FAQ list | |
| `/member/app/faqByType` | POST | FAQ by type | |
| `/member/app/delayUpgrade` | POST | Delay upgrade prompt | |
| `/member/channel/click` | POST | Analytics channel click | |
| `/member/feedback/save` | POST | Submit feedback | |
| `/member/feedback/tag` | POST | Feedback tags | |
| `/member/feedback/addLog` | POST | Add feedback log | |
| `/member/feedback/addDeviceFeedback` | POST | Device-specific feedback | |

---

## Live API Response Examples

### Device List (`/device/device/list`)

<details>
<summary>Click to expand</summary>

Each device in the list includes flat keys at the top level:

```json
{
  "deviceSn": "LB0102030312CEF4AE4D",
  "name": "Luma Smart Litter Box",
  "icon": "https://oss.us.petlibro.com/dlcloud/platform/product_icon/...",
  "productIdentifier": "PLLB001",
  "productName": "Luma Smart Litter Box",
  "mac": "88:49:2D:07:13:E2",
  "softwareVersion": "1.0.14",
  "timezone": "Europe/Berlin",
  "online": true,
  "surplusGrain": true,
  "powerType": 1,
  "powerMode": 1,
  "electricQuantity": 0,
  "batteryState": "low",
  "vacuumState": true,
  "pumpAirState": true,
  "vacuumMode": "NORMAL",
  "enableSound": true,
  "enableLight": true,
  "enableFeedingPlan": true,
  "enableAutoUpgrade": true,
  "wifiRssiLevel": 3,
  "wifiRssi": -68,
  "remainingReplacementDays": 90,
  "remainingCleaningDays": 90,
  "exceptionMessage": "",
  "weightPercent": 0,
  "weight": 0.0,
  "weightState": "NORMAL",
  "snowflake": true,
  "deviceShareState": 1,
  "barnDoorError": false,
  "doorErrorState": "NORMAL",
  "cameraSwitch": true,
  "rubbishFullState": false,
  "rubbishInplaceState": true,
  "filterState": "GOOD",
  "deviceStoppedWorking": false,
  "actDeodorizationMode": "MANUAL",
  "deodorizationStateOn": false,
  "doorState": "CLOSE",
  "cleanState": "GOOD",
  "matState": "GOOD",
  "remainingMatDays": 90
}
```

</details>

### realInfo (`/device/device/realInfo`)

<details>
<summary>Luma Smart Litter Box — Click to expand</summary>

```json
{
  "deviceSn": "LB0102030312CEF4AE4D",
  "mac": "88:49:2D:07:13:E2",
  "timezone": "Europe/Berlin",
  "hardwareVersion": "0.9",
  "softwareVersion": "1.0.14",
  "online": true,
  "lastOnlineTime": 1776248055291,
  "wifiSsid": "Midgard",
  "wifiRssi": -68,
  "wifiRssiLevel": 3,
  "powerMode": 1,
  "powerType": 1,
  "electricQuantity": 0,
  "batteryState": "low",
  "surplusGrain": true,
  "vacuumState": true,
  "pumpAirState": true,
  "volume": 80,
  "enableLight": true,
  "lightSwitch": true,
  "enableSound": true,
  "soundSwitch": true,
  "filterReplacementFrequency": 90,
  "remainingReplacementDays": 90,
  "machineCleaningFrequency": 90,
  "remainingCleaningDays": 90,
  "weightPercent": 0,
  "weightState": "NORMAL",
  "weight": 0.0,
  "calibration": true,
  "vacuumMode": "NORMAL",
  "enableCamera": true,
  "cameraSwitch": true,
  "resolution": "P1080",
  "cloudVideoRecordSwitch": true,
  "enableSleepMode": false,
  "barnDoorError": false,
  "runningState": "IDLE",
  "doorErrorState": "NORMAL",
  "whetherInSleepMode": false,
  "leftWarehouseSurplusGrain": true,
  "rightWarehouseSurplusGrain": true,
  "warehouseSurplusGrain": "GOOD",
  "garbageWarehouseState": "NORMAL",
  "garbageWarehouseLeaveState": "NORMAL",
  "throwMode": "NORMAL",
  "rubbishFullState": false,
  "rubbishInplaceState": true,
  "deviceStoppedWorking": false,
  "enableHumanDetection": false,
  "deodorizationModeSwitch": false,
  "deodorizationStateOn": false
}
```

</details>

### dataRealInfo (`/data/data/realInfo`)

<details>
<summary>Luma Smart Litter Box — Click to expand</summary>

Contains additional fields not in realInfo:

```json
{
  "filterState": "GOOD",
  "cleanState": "GOOD",
  "matState": "GOOD",
  "remainingMatDays": 90,
  "exceptionMessage": "",
  "actDeodorizationMode": "MANUAL",
  "deodorizationStateOn": false,
  "deodorizationTimerOffSwitch": false,
  "timedDeodorizationStartTime": 0,
  "doorState": "CLOSE",
  "batterySupply8Hours": false,
  "motionSensitivityLevel": 0
}
```

Note: This endpoint returns many fields that overlap with realInfo. The unique fields above are the ones not available from realInfo.

</details>

### getAttributeSetting (`/device/setting/getAttributeSetting`)

<details>
<summary>Luma Smart Litter Box — Click to expand</summary>

```json
{
  "lightSwitch": true,
  "soundSwitch": true,
  "volume": 80,
  "powerMode": 1,
  "enableAutoUpgrade": true,
  "cameraSwitch": true,
  "resolution": "P1080",
  "videoWatermarkSwitch": true,
  "nightVisionMode": "AUTO_BLACK_WHITE",
  "petDetectionSwitch": true,
  "enableReverseCamera": false,
  "enableHumanDetection": false,
  "enableSleepMode": false,
  "enableDeviceShare": true,
  "cleanModeEnable": true,
  "cleanMode": "AUTO",
  "autoDelaySec": 60,
  "enableAdsorption": false,
  "avoidRepeatClean": false,
  "deodorizationModeSwitch": true,
  "deodorizationMode": "SMART",
  "deodorizationWindSpeed": "LOW",
  "manualDeodorizationWindSpeed": "LOW",
  "manualDeodorizationSwitch": false,
  "disableHardwareButton": false,
  "deodorizationTimerOffSwitch": false,
  "deodorizationTimerOffInterval": 5,
  "afterDeodorizationSwitch": false,
  "durationAfterDeodorization": 2,
  "enableFillLight": true,
  "enableAudioRecording": false,
  "enableAutoCleanInSleepMode": true,
  "enableDeodorizationInSleepMode": true,
  "sleepModeType": 1,
  "enableAiAssistant": false,
  "motionSensitivityLevel": 0,
  "detThreshold": 0.6,
  "reidThreshold": 0.65
}
```

</details>

---

## App 1.9.40 Notes

From a static pass over app v1.9.40 (2026-10-12): `blutter` against `libapp.so`, plus a
string diff against v1.9.30. Unless a paragraph says it was read live, nothing here was
captured from the network or tried against the API: it shows what the app sends and how
it reads responses — not what a given device or firmware actually returns.

### What changed between 1.9.30 and 1.9.40

Little, and nothing that affects a device the integration supports:

- The pet-care dashboard moved to the `V2` calls listed under
  [Pet Care data](#pet-care-data-per-pet), with a new `FOOD_DISPENSED` metric.
- No new product identifiers, no new MQTT handlers, and no new keys in the device
  `realInfo` model.

The rest of this section is not new in 1.9.40. It is what the app has that this
reference and the integration did not yet cover.

### Litter box operation info (`/device/device/getSuspendInfo`)

The app's litter box screen calls this with `{"deviceSn": "<sn>"}` and reads:

| Field | Values seen in the app's code |
|-------|-------------------------------|
| `action` | `CLEAN`, `LEVELING`, `EMPTY` — the same names as the `execCmdService` actions |
| `execState` | `NORMAL` (nothing running), `EXEC`, `PAUSED`, `ENDING` |
| `progress` | Drives the progress bar; unit and range not confirmed |
| `exeCmdStartTime` | Start of the current action |
| `expectExeTime` | Expected duration |

The app shows "Cleaning", "Leveling", "Emptying", "Paused" or "Ending" from these.

Read live from an idle Luma (firmware 1.0.19, 2026-10-12):

```json
{
  "deviceSn": "<sn>",
  "action": "CLEAN",
  "exeCmdStartTime": 1791805702966,
  "expectExeTime": null,
  "execState": "NORMAL",
  "lastPauseTime": 1791805703409,
  "progress": 0
}
```

- While the box is idle (`execState: "NORMAL"`), `action` and `exeCmdStartTime` still
  describe the **last** action, so `action` alone does not mean something is running.
- `lastPauseTime` is returned but not read by the app.
- A Dockstream fountain answers the same call with every field `null`.
- No response has been captured while an action runs, so the scale of `progress`
  (0–1 or 0–100) is still unknown.

The integration's Luma **Operation** sensor is built on this call. It follows the app's
status line: `idle` for `NORMAL`; `cleaning` / `leveling` / `emptying` for `EXEC` with
that action (`running` for any other action); `paused`; `ending`. The raw fields are on
the sensor's attributes, `progress` included, unscaled.

### What `deviceStoppedWorking` means to the app

The app's Luma screen (`LB001/lb001_main.dart`) uses the flag for one thing: while it is
`true`, the Clean / Empty / Level buttons are drawn greyed out (`LbOperateStatus.gray`
instead of `wait`). No banner, dialog or error text is tied to it there, which matches
the app showing nothing during the blips reported in issue #1.

So the app treats it as "the box is not accepting a command right now", not as a fault.
That reading comes from the app's code, not from the device: what makes the firmware set
the flag is still unknown, and a payload captured during a blip is what would settle it.

Checked against a live Luma (firmware 1.0.19, integration diagnostics, 2026-10-12, box
idle and flag `false`):

- The flag is not specific to the litter box. `realInfo` carries `deviceStoppedWorking`
  for the Dockstream fountains (`PLWF105`, `PLWF106`, `PLWF116`) as well.
- The app's `realInfo` model also has `antiPinchState`, `errorState`, `execState`,
  `deviceState`, `zeroState` and `litterState`. The Luma sends **none** of them, so
  there is no companion field in `realInfo` that would explain a blip. (`errorState`
  does arrive for the fountains.)
- Next to the flag the Luma sends only `runningState`, `doorErrorState`, `barnDoorError`
  and, from `dataRealInfo`, `exceptionMessage`. That leaves `getSuspendInfo` above as
  the one untried source for what the box was doing at that moment.

### Litter box faults

`/device/device/releaseMotorStuck`, `/device/device/releaseAntiPinch` and the
`/device/lockedRotor/diagnostics` pair back the app's "stuck" flow. A diagnostics result
carries `state` (`PROCESSING`, `FINISH`, `ERROR`, `RECOVERY`), `percent`, `errorCode`
and `logs`. These act on hardware and have not been tried.

### Litter box settings from the app's pages

The keys are in the `getAttributeSetting` sample below; the current values were read live
on 2026-10-12. The **writes** follow the app's request keys and have not been exercised
against a device yet.

| Key | App label | Integration | Notes |
|-----|-----------|-------------|-------|
| `enableAdsorption` | Coverage assist | Switch *Coverage Assist* | Sent to `updateCleanModeSetting` together with `cleanMode`, `autoDelaySec` and `avoidRepeatClean`, as the app does (the app also sends `cleanModeEnable`) |
| `manualDeodorizationWindSpeed` | Fan speed (manual purify) | Select *Manual Air Purifier Fan Speed* | `LOW` / `HIGH`, to `updateDeodorizationSetting` |
| `deodorizationTimerOffSwitch` | Turn off after | Switch *Air Purifier Auto-Off* | To `updateDeodorizationSetting`, with the interval |
| `deodorizationTimerOffInterval` | Turn off after | Select *Air Purifier Auto-Off After* | Minutes; the app offers 5, 10, 15, 30, 60, 120 |
| `cleanMode` | Clean mode | Select *Clean Mode* (`AUTO` / `MANUAL`) | The app's page only ever sends `AUTO` or `PLAN` (scheduled) plus the separate `cleanModeEnable` flag. Whether the server accepts `MANUAL` is unconfirmed — not changed until a write has been observed |
| `deodorizationMode` | Operation mode | Read-only sensor | The app uses `SMART`, `PERIOD` and `MANUAL` |

### Push event keys

`eventKeys` values known to app 1.9.40 — see [MQTT_RESEARCH.md](MQTT_RESEARCH.md#payload).

---

## Integration Coverage

### Supported Product Identifiers

| Identifier | Product Name | Type |
|------------|-------------|------|
| `PLAF103` | Granary Smart Feeder | Feeder |
| `PLAF107` | Space Smart Feeder | Feeder |
| `PLAF108` | Air Smart Feeder | Feeder |
| `PLAF109` | Polar Wet Food Feeder | Feeder |
| `PLAF203` | Granary Smart Camera Feeder | Feeder |
| `PLAF301` | One RFID Smart Feeder | Feeder |
| `PLWF105` | Dockstream Smart Fountain | Fountain |
| `PLWF305` | Dockstream Smart RFID Fountain | Fountain |
| `PLWF106` | Dockstream 2 Smart Fountain | Fountain |
| `PLWF116` | Dockstream 2 Smart Cordless Fountain | Fountain |
| `PLLB001` | Luma Smart Litter Box | Litter Box |

The integration picks a device class by product *name*, not by identifier, so this table
is for reference. The identifiers are the ones in the README and all of them occur in
app 1.9.40; the earlier version of this table listed `PLAF007`, `PLAF015`, `PLWF005` and
`PLWF115`, none of which occur in the app. The name-to-identifier pairing is confirmed
from a live device list for `PLLB001`, `PLWF105`, `PLWF106` and `PLWF116`; for the
feeders and `PLWF305` it follows the README and has not been checked against hardware.

App 1.9.40 also knows `PLAF105`, `PLAF204`, `PLAF205`, `PLAF305`, `PLWF107` and
`PLPC001`. The integration has no device class for them, and which products they are has
not been established.

### Endpoints Used by Integration

Total: **112 endpoints** used out of **260+ discovered** in the app (counted from the code on 2026-10-12).

### Known API Quirks

1. **`baseInfo.name`** can return empty string `""` — filter empty strings to avoid overwriting valid names
2. **`workRecord/list`** requires `startTime`/`endTime` as epoch milliseconds, not date strings
3. **`data.data`** key in response is `null` (not `{}`) when no data exists — use `or {}` pattern
4. **Token expiry** returns code `1009` (`NOT_YET_LOGIN`) — must re-login and retry
5. **Forced logout** returns code `1025` (`FORCED_LOGOUT`) — session invalidated server-side
6. **`deodorizationModeSwitch`** has different values in `realInfo` (runtime state) vs `getAttributeSetting` (configured value)
7. **`maintenanceRecord`** requires `key` query parameter (e.g., `?key=filter`)
8. **`maintain`** endpoint is GET, not POST
9. **`deviceStoppedWorking`** (Luma `realInfo`) flips to `true` for seconds at a time while the box is idle — see [App 1.9.40 Notes](#app-1940-notes) and issue #1
