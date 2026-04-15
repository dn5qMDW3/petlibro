# PETLIBRO Cloud API Reference

> Extracted from PETLIBRO Android app v1.7.90 (Flutter/Dart) and verified against live API.
> Base URL: `https://api.us.petlibro.com` (US region)
> Last updated: 2026-04-15

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
    "token": "704cd53e8d744b1b94d822dd4b5a3122",
    "clientId": "APP_190201021",
    "memberId": 190201021,
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
| `/device/device/updateRoom` | POST | Assign device to room | |
| `/device/device/updateDeviceImage` | POST | Change device image | |
| `/device/device/wifiInfo` | POST | Get WiFi connection info | |
| `/device/device/wifiChangeService` | POST | Initiate WiFi change | |
| `/device/device/wifiReconnect` | POST | Reconnect WiFi | |
| `/device/device/getSuspendInfo` | POST | Get device suspension info | |
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
| `/device/setting/getNoticeSetting` | POST | Notification settings | |

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
| `/device/setting/updateFeedingPlanSwitch` | POST | Enable/disable feeding plans | ✅ |
| `/device/setting/updateRingerMode` | POST | Bell/ringer mode | |
| `/device/setting/updateRadarSetting` | POST | Radar sensing level | ✅ |
| `/device/setting/updateLowWaterSetting` | POST | Low water threshold | ✅ |
| `/device/setting/updateChildLockSwitch` | POST | Child lock toggle | ✅ |
| `/device/setting/updateNoticeSetting` | POST | General notification settings | |
| `/device/setting/updateFeedingNoticeSetting` | POST | Feeding notifications | |
| `/device/setting/updateOfflineNoticeSetting` | POST | Offline notifications | |
| `/device/setting/updateLowBatteryNoticeSetting` | POST | Low battery notifications | |
| `/device/setting/updatePowerChangeNoticeSetting` | POST | Power change notifications | |
| `/device/setting/updateVacuumSuccessNoticeSetting` | POST | Vacuum success notifications | |
| `/device/setting/updateVacuumFailedNoticeSetting` | POST | Vacuum fail notifications | |
| `/device/setting/updateSurplusGrainNoticeSetting` | POST | Food level notifications | |
| `/device/setting/updateGrainOutletBlockedNoticeSetting` | POST | Food outlet blocked notifications | |
| `/device/setting/updateMotionDetectionNoticeSetting` | POST | Motion detection notifications | |
| `/device/setting/updateSoundDetectionNoticeSetting` | POST | Sound detection notifications | |
| `/device/setting/updateDrinkTrendNoticeSetting` | POST | Drinking trend notifications | |
| `/device/setting/updateNoDrinkNoticeSetting` | POST | No-drink alert notifications | |
| `/device/setting/updateLocationReminderSetting` | POST | Location-based reminders | |
| `/device/setting/updateDesiccantNoticeSetting` | POST | Desiccant replacement notifications | |
| `/device/setting/dailyDrinkGoalSetting` | POST | Set daily drinking goal | |
| `/device/setting/enableDeviceShare` | POST | Enable device sharing | |
| `/device/setting/enableDeviceAiAssistance` | POST | Enable AI assistant | |
| `/device/setting/enableDrinkingWaterNotice` | POST | Drinking water notifications | |
| `/device/setting/enableFilterReplacementReminder` | POST | Filter replacement reminder | |
| `/device/setting/enableMachineCleaningReminder` | POST | Machine cleaning reminder | |
| `/device/setting/enableLowWaterNotice` | POST | Low water notification | |
| `/device/setting/enableReachDrinkingWaterAlertNotice` | POST | Drinking goal alert | |
| `/device/setting/enableTankOverturnedNotice` | POST | Tank overturned notification | |

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
| `/device/cleanPlan/getCleanPlan` | POST | Get scheduled clean plans | |
| `/device/cleanPlan/addCleanPlan` | POST | Add scheduled clean | |
| `/device/cleanPlan/updateCleanPlan` | POST | Update scheduled clean | |
| `/device/cleanPlan/delCleanPlan` | POST | Delete scheduled clean | |

---

### Maintenance & Resets

| Endpoint | Method | Purpose | Used by Integration |
|----------|--------|---------|:---:|
| `/device/device/filterReset` | POST | Reset filter replacement timer | ✅ |
| `/device/device/machineCleaningReset` | POST | Reset cleaning timer | ✅ |
| `/device/device/matReset` | POST | Reset mat replacement timer | ✅ |
| `/device/device/desiccantReset` | POST | Reset desiccant timer | ✅ |
| `/device/device/maintenanceFrequencySetting` | POST | Set maintenance frequency | ✅ |
| `/device/device/maintenanceRecord` | GET | Get maintenance history | |
| `/device/device/maintain` | GET | Get maintenance info | |

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
| `/member/pet/list` | POST | List all pets | |
| `/member/pet/petBaseInfoList` | POST | Basic pet info list | |
| `/member/pet/detailV2` | POST | Pet details (v2) | |
| `/member/pet/saveOrUpdate` | POST | Create/update pet | |
| `/member/pet/delete` | POST | Delete pet | |
| `/member/pet/getLabels` | POST | Get pet labels | |
| `/member/pet/getCommonLabels` | POST | Get common labels | |
| `/member/pet/waterIntakeSetting` | POST | Set pet water intake | |
| `/device/devicePetRelation/getBoundPets` | POST | Get pets bound to device | ✅ |
| `/device/devicePetRelation/bindPets` | POST | Bind pets to device | |
| `/device/devicePetRelation/removePets` | POST | Remove pets from device | |
| `/device/devicePetRelation/getBoundDevices` | POST | Get devices bound to pet | |
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

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/member/healthCare/dashboardList` | POST | Health dashboard list |
| `/member/healthCare/dashboardDetail` | POST | Health dashboard detail |
| `/member/healthCare/getDashboardLayout` | POST | Dashboard layout |
| `/member/healthCare/updateDashboardLayout` | POST | Update dashboard layout |
| `/member/healthCare/getFirstClassification` | POST | Health categories |
| `/member/healthCare/getPetGoal` | POST | Pet health goals |
| `/member/healthCare/goalSetting` | POST | Set health goals |
| `/member/healthCare/goalDistCal` | POST | Goal distance calculation |
| `/member/healthCare/goalRecommendInfo` | POST | Goal recommendations |
| `/member/healthCare/goalApplyToDevice` | POST | Apply goal to device |
| `/member/healthCare/planInfo` | POST | Health plan info |
| `/member/healthCare/addTraceV2` | POST | Add health trace |
| `/member/healthCare/updateTraceV2` | POST | Update health trace |
| `/member/healthCare/deleteTrace` | POST | Delete health trace |
| `/member/healthCare/traceHistory` | POST | Trace history |
| `/member/healthCare/traceQuantity` | POST | Trace quantities |
| `/member/healthCare/traceAndCalenderV2` | POST | Traces with calendar |
| `/member/healthCare/traceCalendarList` | POST | Trace calendar |
| `/member/healthCare/updateTraceCompletedState` | POST | Mark trace complete |
| `/member/healthCare/repeatTraceListV2` | POST | Repeating traces |
| `/member/healthCare/updateRepeatTraceV2` | POST | Update repeating trace |
| `/member/healthCare/enableRepeatTrace` | POST | Enable repeating trace |
| `/member/healthCare/deleteRepeatTrace` | POST | Delete repeating trace |
| `/member/healthCare/petBindDeviceList` | POST | Pet's bound device list |

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
| `/device/device/wear/wearListV2` | POST | List wearables | |
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

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/device/deviceShare/add` | POST | Share device |
| `/device/deviceShare/remove` | POST | Remove share |
| `/device/deviceShare/batchRemove` | POST | Batch remove shares |
| `/device/deviceShare/cancel` | POST | Cancel pending share |
| `/device/deviceShare/quit` | POST | Leave shared device |
| `/device/deviceShare/retry` | POST | Retry failed share |
| `/device/deviceShare/rec` | POST | Accept share invite |
| `/device/deviceShare/verifyShare` | POST | Verify share code |
| `/device/deviceShare/deviceShareList` | POST | Shared device list |
| `/device/deviceShare/deviceSharedList` | POST | Devices shared with me |
| `/device/deviceShare/deviceSharingList` | POST | Pending shares |
| `/device/deviceShare/myShareList` | POST | My shares list |
| `/device/deviceShare/mySharingDevices` | POST | Devices I'm sharing |
| `/device/deviceShare/sharePopList` | POST | Share popup list |
| `/device/deviceShare/deviceSelector` | POST | Device selector for sharing |

---

### Device Audio

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/device/deviceAudio/all` | POST | List all audio files |
| `/device/deviceAudio/add` | POST | Upload audio file |
| `/device/deviceAudio/remove` | POST | Remove audio file |
| `/device/deviceAudio/use` | POST | Set active audio |

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

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/member/third/tutk/info` | POST | Get TUTK credentials |
| `/member/certificate/ca` | POST | Get CA certificate |
| `/member/certificate/generate` | POST | Generate certificate |
| `/member/certificate/confirm` | POST | Confirm certificate |
| `/member/certificate/error` | POST | Report certificate error |

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

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/device/msg/page` | POST | Message list (paginated) |
| `/device/msg/detail` | POST | Message detail |
| `/device/msg/detailWithDel` | POST | Detail and delete |
| `/device/msg/read` | POST | Mark message read |
| `/device/msg/readAll` | POST | Mark all read |
| `/device/msg/readBatch` | POST | Batch mark read |
| `/device/msg/delBatch` | POST | Batch delete |
| `/device/msg/unreadQuantity` | POST | Unread count |
| `/device/deviceTips/getTips` | POST | Get device tips |
| `/device/deviceTips/disableTips` | POST | Disable a tip |
| `/member/popup/create` | POST | Create popup |
| `/member/findPet/detail` | POST | Lost pet detail |
| `/member/findPet/publish` | POST | Publish lost pet |
| `/member/findPet/upsertFindPet` | POST | Create/update lost pet |

---

### Rooms

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/device/room/systemRooms` | POST | List system rooms |
| `/device/room/addRoom` | POST | Add custom room |
| `/device/room/upRoom` | POST | Update room |
| `/device/room/delRoom` | POST | Delete room |
| `/device/room/delRoomV2` | POST | Delete room (v2) |

---

### App & System

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/member/app/config` | POST | App configuration |
| `/member/app/commonConfig` | POST | Common config (authenticated) |
| `/member/app/commonConfigWithoutLogin` | POST | Common config (unauthenticated) |
| `/member/app/faq` | POST | FAQ list |
| `/member/app/faqByType` | POST | FAQ by type |
| `/member/app/delayUpgrade` | POST | Delay upgrade prompt |
| `/member/channel/click` | POST | Analytics channel click |
| `/member/feedback/save` | POST | Submit feedback |
| `/member/feedback/tag` | POST | Feedback tags |
| `/member/feedback/addLog` | POST | Add feedback log |
| `/member/feedback/addDeviceFeedback` | POST | Device-specific feedback |

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

## Integration Coverage

### Supported Product Identifiers

| Identifier | Product Name | Type |
|------------|-------------|------|
| `PLAF007` | Air Smart Feeder | Feeder |
| `PLAF103` | Granary Smart Feeder | Feeder |
| `PLAF107` | Granary Smart Camera Feeder | Feeder |
| `PLAF015` | One RFID Smart Feeder | Feeder |
| `PLAF109` | Polar Wet Food Feeder | Feeder |
| `PLAF203` | Space Smart Feeder | Feeder |
| `PLWF105` | Dockstream Smart Fountain | Fountain |
| `PLWF005` | Dockstream Smart RFID Fountain | Fountain |
| `PLWF106` | Dockstream 2 Smart Fountain | Fountain |
| `PLWF115` | Dockstream 2 Smart Cordless Fountain | Fountain |
| `PLLB001` | Luma Smart Litter Box | Litter Box |

### Endpoints Used by Integration

Total: **61 endpoints** used out of **220+ discovered** in the app.

### Known API Quirks

1. **`baseInfo.name`** can return empty string `""` — filter empty strings to avoid overwriting valid names
2. **`workRecord/list`** requires `startTime`/`endTime` as epoch milliseconds, not date strings
3. **`data.data`** key in response is `null` (not `{}`) when no data exists — use `or {}` pattern
4. **Token expiry** returns code `1009` (`NOT_YET_LOGIN`) — must re-login and retry
5. **Forced logout** returns code `1025` (`FORCED_LOGOUT`) — session invalidated server-side
6. **`deodorizationModeSwitch`** has different values in `realInfo` (runtime state) vs `getAttributeSetting` (configured value)
7. **`maintenanceRecord`** requires `key` query parameter (e.g., `?key=filter`)
8. **`maintain`** endpoint is GET, not POST
