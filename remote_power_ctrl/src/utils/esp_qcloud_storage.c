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

#include "string.h"
#include "stdio.h"
#include "stdlib.h"

#include "nvs.h"
#include "nvs_flash.h"

#include "esp_qcloud_utils.h"
#include "esp_qcloud_storage.h"

static const char *TAG = "esp_qcloud_storage";

esp_err_t esp_qcloud_storage_init()
{
    static bool init_flag = false;

    if (!init_flag) {
        esp_err_t ret = nvs_flash_init();

        if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
            // NVS partition was truncated and needs to be erased
            // Retry nvs_flash_init
            ESP_ERROR_CHECK(nvs_flash_erase());
            ret = nvs_flash_init();
        }

        ESP_ERROR_CHECK(ret);

        init_flag = true;
    }

    return ESP_OK;
}

esp_err_t esp_qcloud_storage_erase(const char *key)
{
    ESP_QCLOUD_PARAM_CHECK(key);

    esp_err_t ret    = ESP_OK;
    nvs_handle handle = 0;

    /**< Open non-volatile storage with a given namespace from the default NVS partition */
    ret = nvs_open(CONFIG_QCLOUD_NVS_NAMESPACE, NVS_READWRITE, &handle);
    ESP_QCLOUD_ERROR_CHECK(ret != ESP_OK, ret, "Open non-volatile storage");

    /**
     * @brief If key is CONFIG_QCLOUD_NVS_NAMESPACE, erase all info in CONFIG_QCLOUD_NVS_NAMESPACE
     */
    if (!strcmp(key, CONFIG_QCLOUD_NVS_NAMESPACE)) {
        ret = nvs_erase_all(handle);
    } else {
        ret = nvs_erase_key(handle, key);
    }

    /**< Write any pending changes to non-volatile storage */
    nvs_commit(handle);

    /**< Close the storage handle and free any allocated resources */
    nvs_close(handle);

    ESP_QCLOUD_ERROR_CHECK(ret != ESP_OK && ret != ESP_ERR_NVS_NOT_FOUND,
                    ret, "Erase key-value pair, key: %s", key);

    return ESP_OK;
}

esp_err_t esp_qcloud_storage_set(const char *key, const void *value, size_t length)
{
    ESP_QCLOUD_PARAM_CHECK(key);
    ESP_QCLOUD_PARAM_CHECK(value);
    ESP_QCLOUD_PARAM_CHECK(length > 0);

    esp_err_t ret     = ESP_OK;
    nvs_handle handle = 0;

    /**< Open non-volatile storage with a given namespace from the default NVS partition */
    ret = nvs_open(CONFIG_QCLOUD_NVS_NAMESPACE, NVS_READWRITE, &handle);
    ESP_QCLOUD_ERROR_CHECK(ret != ESP_OK, ret, "Open non-volatile storage");

    /**< set variable length binary value for given key */
    ret = nvs_set_blob(handle, key, value, length);

    /**< Write any pending changes to non-volatile storage */
    nvs_commit(handle);

    /**< Close the storage handle and free any allocated resources */
    nvs_close(handle);

    ESP_QCLOUD_ERROR_CHECK(ret != ESP_OK, ret, "Set value for given key, key: %s", key);

    return ESP_OK;
}

esp_err_t esp_qcloud_storage_get(const char *key, void *value, size_t length)
{
    ESP_QCLOUD_PARAM_CHECK(key);
    ESP_QCLOUD_PARAM_CHECK(value);
    ESP_QCLOUD_PARAM_CHECK(length > 0);

    esp_err_t ret     = ESP_OK;
    nvs_handle handle = 0;

    /**< Open non-volatile storage with a given namespace from the default NVS partition */
    ret = nvs_open(CONFIG_QCLOUD_NVS_NAMESPACE, NVS_READWRITE, &handle);
    ESP_QCLOUD_ERROR_CHECK(ret != ESP_OK, ret, "Open non-volatile storage");

    /**< get variable length binary value for given key */
    ret = nvs_get_blob(handle, key, value, &length);

    /**< Close the storage handle and free any allocated resources */
    nvs_close(handle);

    if (ret == ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGD(TAG, "<ESP_ERR_NVS_NOT_FOUND> Get value for given key, key: %s", key);
        return ESP_ERR_NVS_NOT_FOUND;
    }

    ESP_QCLOUD_ERROR_CHECK(ret != ESP_OK, ret, "Get value for given key, key: %s", key);

    return ESP_OK;
}
