// Copyright 2017 Espressif Systems (Shanghai) PTE LTD
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

#ifndef __led_pwm_H__
#define __led_pwm_H__

#ifdef __cplusplus
extern "C" {
#endif

#include "driver/ledc.h"

#define HW_TIMER_GROUP (0)                                 /**< Hardware timer group */
#define HW_TIMER_ID (0)                                    /**< Hardware timer number */
#define HW_TIMER_DIVIDER (16)                              /**< Hardware timer clock divider */
#define HW_TIMER_SCALE (TIMER_BASE_CLK / HW_TIMER_DIVIDER) /**< Convert counter value to seconds */
#define GAMMA_CORRECTION 0.8                               /**< Gamma curve parameter */
#define GAMMA_TABLE_SIZE 256                               /**< Gamma table size, used for led fade*/
#define DUTY_SET_CYCLE (20)                                /**< Set duty cycle */

/**
  * @brief Initialize and set the ledc timer for the iot led
  *
  * @param timer_num The timer index of ledc timer group used for iot led
  *     This parameter can be one of LEDC_TIMER_x where x can be (0 .. 3) 
  *
  * @param speed_mode speed mode of ledc timer
  *     This parameter can be one of LEDC_x_SPEED_MODE where x can be (LOW, HIGH)
  *
  * @param freq_hz frequency of ledc timer
  *     This parameter must be less than 5000
  *
  * @return
  *	    - ESP_OK if sucess
  *     - ESP_QCLOUD_ERR_INVALID_ARG Parameter error
  *     - ESP_FAIL Can not find a proper pre-divider number base on the given frequency 
  *         and the current duty_resolution.
*/
esp_err_t led_pwm_init(ledc_timer_t timer_num, ledc_mode_t speed_mode, uint32_t freq_hz);

/**
  * @brief DeInitializes the iot led and free resource
  * 
  * @return
  *	    - ESP_OK if sucess
*/
esp_err_t led_pwm_deinit();

/**
  * @brief Set the ledc channel used by iot led and associate the gpio port used 
  *     for output
  * 
  * @param channel The ledc channel
  *     This parameter can be LEDC_CHANNEL_x where x can be (0 .. 15)
  * @param gpio_num the ledc output gpio_num
  *     This parameter can be GPIO_NUM_x where x can be (0, 33)
  * 
  * @note If the operation of esp32 depends on SPI FLASH or PSRAM, then these related 
  *     pins should not be set to output.
  *         
  * @return
  *	    - ESP_OK if sucess
  *     - ESP_QCLOUD_ERR_INVALID_ARG Parameter error
  *	    - ESP_ERR_INVALID_STATE if lot_led_init() is not called yet
*/
esp_err_t led_pwm_regist_channel(ledc_channel_t channel, gpio_num_t gpio_num);

/**
  * @brief Returns the channel value 
  * @note before calling this function, you need to call led_pwm_regist_channel() to
  *     set the channel
  * 
  * @param channel The ledc channel
  *     This parameter can be LEDC_CHANNEL_x where x can be (0 .. 15)
  * @param dst The address where the channel value is stored
  * @return
  *     - ESP_OK if sucess
  *	    - ESP_QCLOUD_ERR_INVALID_ARG if dst is NULL
  *	    - ESP_ERR_INVALID_STATE if lot_led_init() is not called yet
*/
esp_err_t led_pwm_get_channel(ledc_channel_t channel, uint8_t* dst);

/**
  * @brief Set the fade state for the specified channel
  * @note before calling this function, you need to call led_pwm_regist_channel() to
  *     set the channel
  * 
  * @param channel The ledc channel
  *     This parameter can be LEDC_CHANNEL_x where x can be (0 .. 15)
  * @param value The target output brightness of iot led
  *     This parameter can be (0 .. 255)
  * @param fade_ms The time from the current value to the target value
  * @return
  *	    - ESP_OK if sucess
  *	    - ESP_ERR_INVALID_STATE if lot_led_init() is not called yet
*/
esp_err_t led_pwm_set_channel(ledc_channel_t channel, uint8_t value, uint32_t fade_ms);

/**
  * @brief Set the blink state or loop fade for the specified channel
  * @note before calling this function, you need to call led_pwm_regist_channel() to
  *     set the channel
  *         
  * @param channel The ledc channel
  *     This parameter can be LEDC_CHANNEL_x where x can be (0 .. 15)
  * @param value The output brightness of iot led
  *     This parameter can be (0 .. 255)
  * @param period_ms Blink cycle
  * @param fade_flag select loop fade or blink
  *     1 for loop fade
  *     0 for blink
  * @return
  *	    - ESP_OK if sucess
  *	    - ESP_ERR_INVALID_STATE if lot_led_init() is not called yet
*/
esp_err_t led_pwm_start_blink(ledc_channel_t channel, uint8_t value, uint32_t period_ms, bool fade_flag);

/**
  * @brief Stop the blink state or loop fade for the specified channel
  * 
  * @param channel The ledc channel
  *     This parameter can be LEDC_CHANNEL_x where x can be (0 .. 15)
  * @return
  *	    - ESP_OK if sucess
  *	    - ESP_ERR_INVALID_STATE if lot_led_init() is not called yet
*/
esp_err_t led_pwm_stop_blink(ledc_channel_t channel);

/**
  * @brief Set the specified gamma_table to control the fade effect, usually 
  *     no need to set
  * 
  * @param gamma_table[GAMMA_TABLE_SIZE] Expected gamma table value
  *
  * @note  Gamma_table is the dimming curve used by the led_pwm driver. 
  *     The element type is uint16_t. Each element is treated as a binary 
  *     fixed-point number. The decimal point is before the eighth bit 
  *     and after the ninth bit, so the range of expressions can be 
  *     0x00.00 ~ 0xff.ff. 
  * @note default gamma_table is created in led_pwm_init()
  *
  * @return
  *	    - ESP_OK if sucess
  *	    - ESP_ERR_INVALID_STATE if lot_led_init() is not called yet
*/
esp_err_t led_pwm_set_gamma_table(const uint16_t gamma_table[GAMMA_TABLE_SIZE]);

#ifdef __cplusplus
}
#endif

#endif /**< __led_pwm_H__ */
