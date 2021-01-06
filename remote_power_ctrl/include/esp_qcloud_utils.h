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

#pragma once

#include <stdint.h>

#include "freertos/FreeRTOS.h"

#include <esp_err.h>
#include "esp_log.h"

#ifdef __cplusplus
extern "C"
{
#endif

typedef struct esp_qcloud_time_config {
    /** If not specified, then 'CONFIG_ESP_QCLOUD_SNTP_SERVER_NAME' is used as the SNTP server. */
    char *sntp_server_name;
} esp_qcloud_time_config_t;

/**
 * Macro which can be used to check the error code,
 * and terminate the program in case the code is not ESP_OK.
 * Prints the error code, error location, and the failed statement to serial output.
 *
 * Disabled if assertions are disabled.
 */
#define ESP_QCLOUD_ERROR_CHECK(con, err, format, ...) do { \
        if (con) { \
            if(*format != '\0') \
                ESP_LOGW(TAG, "<%s> " format, esp_err_to_name(err), ##__VA_ARGS__); \
            return err; \
        } \
    } while(0)

/**
 * @brief Macro serves similar purpose as ``assert``, except that it checks `esp_err_t`
 *        value rather than a `bool` condition. If the argument of `ESP_QCLOUD_ERROR_ASSERT`
 *        is not equal `ESP_OK`, then an error message is printed on the console,
 *         and `abort()` is called.
 *
 * @note If `IDF monitor` is used, addresses in the backtrace will be converted
 *       to file names and line numbers.
 *
 * @param  err [description]
 * @return     [description]
 */
#define ESP_QCLOUD_ERROR_ASSERT(err) do { \
        esp_err_t __err_rc = (err); \
        if (__err_rc != ESP_OK) { \
            ESP_LOGW(TAG, "<%s> ESP_QCLOUD_ERROR_ASSERT failed, at 0x%08x, expression: %s", \
                     esp_err_to_name(__err_rc), (intptr_t)__builtin_return_address(0) - 3, __ASSERT_FUNC); \
            assert(0 && #err); \
        } \
    } while(0)

#define ESP_QCLOUD_ERROR_GOTO(con, lable, format, ...) do { \
        if (con) { \
            if(*format != '\0') \
                ESP_LOGW(TAG, format, ##__VA_ARGS__); \
            goto lable; \
        } \
    } while(0)

#define ESP_QCLOUD_ERROR_CONTINUE(con, format, ...) { \
        if (con) { \
            if(*format != '\0') \
                ESP_LOGW(TAG, format, ##__VA_ARGS__); \
            continue; \
        } \
    }

#define ESP_QCLOUD_ERROR_BREAK(con, format, ...) { \
        if (con) { \
            if(*format != '\0') \
                ESP_LOGW(TAG, format, ##__VA_ARGS__); \
            break; \
        } \
    }

#define ESP_QCLOUD_PARAM_CHECK(con) do { \
        if (!(con)) { \
            ESP_LOGE(TAG, "<ESP_QCLOUD_ERR_INVALID_ARG> !(%s)", #con); \
            return ESP_ERR_INVALID_ARG; \
        } \
    } while(0)

/** Reboot the chip after a delay
 *
 * This API just starts an esp_timer and executes a reboot from that.
 * Useful if you want to reboot after a delay, to allow other tasks to finish
 * their operations (Eg. MQTT publish to indicate OTA success)
 *
 * @param[in] ticks Time in ticks after which the chip should reboot
 *
 * @return ESP_OK on success
 * @return error on failure
 */
esp_err_t esp_qcloud_reboot(TickType_t wait_ticks);

/**
 * @brief Get the number of consecutive restarts
 *
 * @return
 *     - count
 */
int esp_qcloud_reboot_unbroken_count(void);

/**
 * @brief Get the number of restarts
 *
 * @return
 *     - count
 */
int esp_qcloud_reboot_total_count(void);

/**
 * @brief Determine if the restart is caused by an exception.
 *
 * @return
 *     - true
 *     - false
 */
bool esp_qcloud_reboot_is_exception(bool erase_coredump);

/** Initialize time synchronization
 *
 * This API initializes SNTP for time synchronization.
 *
 * @return ESP_OK on success
 * @return error on failure
 */
esp_err_t esp_qcloud_timesync_start(void);

/** Check if current time is updated
 *
 * This API checks if the current system time is updated against the reference time of 1-Jan-2019.
 *
 * @return true if time is updated
 * @return false if time is not updated
 */
bool esp_qcloud_timesync_check(void);

/** Wait for time synchronization
 *
 * This API waits for the system time to be updated against the reference time of 1-Jan-2019.
 * This is a blocking call.
 *
 * @param[in] uint32_t Number of ticks to wait for time synchronization.
 *
 * @return ESP_OK on success
 * @return error on failure
 */
esp_err_t esp_qcloud_timesync_wait(uint32_t wait_ms);

/** Interval printing system information
 * 
 * @param[in] uint32_t Interval of printing system log information
 * 
 */
void esp_qcloud_print_system_info(uint32_t interval_ms);

#ifdef __cplusplus
}
#endif
