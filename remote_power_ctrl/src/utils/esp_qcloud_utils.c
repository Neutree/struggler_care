// Copyright 2020 Espressif Systems (Shanghai) PTE LTD
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

#include <stdint.h>
#include <sys/time.h>

#include "freertos/FreeRTOS.h"
#include "freertos/timers.h"

#include "esp_wifi.h"
#include <esp_timer.h>
#include <esp_system.h>
#include "esp_sntp.h"
#include "esp_log.h"

#include "esp_qcloud_utils.h"

static const char *TAG = "esp_qcloud_utils";

static void show_system_info_timercb(void *timer)
{
    uint8_t sta_mac[6]        = {0};
    uint8_t primary           = 0;
    wifi_second_chan_t second = 0;
    wifi_ap_record_t ap_info  = {0};

    esp_wifi_get_mac(ESP_IF_WIFI_STA, sta_mac);
    esp_wifi_get_channel(&primary, &second);
    esp_wifi_sta_get_ap_info(&ap_info);

    ESP_LOGI(TAG, "System information sta_mac: " MACSTR ", channel: [%d/%d], rssi: %d, free_heap: %u, minimum_heap: %u",
             MAC2STR(sta_mac), primary, second, ap_info.rssi, esp_get_free_heap_size(), esp_get_minimum_free_heap_size());

    if (!heap_caps_check_integrity_all(true)) {
        ESP_LOGE(TAG, "At least one heap is corrupt");
    }
}

void esp_qcloud_print_system_info(uint32_t interval_ms)
{
    TimerHandle_t timer = xTimerCreate("show_system_info", pdMS_TO_TICKS(interval_ms),
                                       true, NULL, show_system_info_timercb);
    xTimerStart(timer, 0);
}
