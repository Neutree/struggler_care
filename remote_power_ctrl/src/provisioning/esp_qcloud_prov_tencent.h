// Copyright 2020 Espressif Systems (Shanghai) PTE LTD
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#ifdef __cplusplus
extern "C" {
#endif /**< _cplusplus */

esp_err_t esp_qcloud_prov_data_handler(uint32_t session_id, const uint8_t *inbuf, ssize_t inlen,
                                       uint8_t **outbuf, ssize_t *outlen, void *priv_data);

/**
 * @brief Open UDP service to communicate with WeChat applet.
 * 
 * @return
 *     - ESP_OK: succeed
 *     - others: fail
 */
esp_err_t esp_qcloud_prov_udp_server_start(void);

/**
 * @brief Stop UDP service.
 * 
 * @return
 *     - ESP_OK: succeed
 *     - others: fail
 */
esp_err_t esp_qcloud_prov_udp_server_stop(void);

#ifdef __cplusplus
}
#endif /**< _cplusplus */
