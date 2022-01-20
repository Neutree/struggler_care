/* LED Light Example

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#include "esp_qcloud_log.h"
#include "esp_qcloud_console.h"
#include "esp_qcloud_storage.h"
#include "esp_qcloud_iothub.h"
#include "esp_qcloud_prov.h"

#include "light_driver.h"

#ifdef CONFIG_BT_ENABLE
#include "esp_bt.h"
#endif

static const char *TAG = "app_main";

#define POWER_CONTORL_GPIO 22
#define POWER_CONTORL_GPIO_SEL  (1ULL<<POWER_CONTORL_GPIO)
#define POWER_STATUS_GPIO  21
#define POWER_STATUS_GPIO_SEL  (1ULL<<POWER_STATUS_GPIO)

extern esp_err_t esp_qcloud_iothub_report_all_property(void);

#define ESP_INTR_FLAG_DEFAULT 0

typedef enum
{
    ACTION_NONE = 0,
    ACTION_POWER_ON,
    ACTION_POWER_OFF,
    ACTION_POWER_OFF_FORCE
}action_t;

static xQueueHandle gpio_evt_queue = NULL;
static volatile bool g_is_need_report_property = true;
static volatile bool g_is_force_power_off = false;
static volatile int  g_action = ACTION_NONE;

static void IRAM_ATTR gpio_isr_handler(void* arg)
{
    uint32_t gpio_num = (uint32_t) arg;
    xQueueSendFromISR(gpio_evt_queue, &gpio_num, NULL);
}

bool is_power_on()
{
    return gpio_get_level(POWER_STATUS_GPIO) == 1;
}

void power_on()
{
    if(is_power_on())
        return;
    //TODO: 限制间隔时间
    gpio_set_level(POWER_CONTORL_GPIO, 1);
    vTaskDelay(1500 / portTICK_PERIOD_MS);
    gpio_set_level(POWER_CONTORL_GPIO, 0);
}

void power_off()
{
    if(!is_power_on())
        return;
    //TODO: 限制间隔时间
    gpio_set_level(POWER_CONTORL_GPIO, 1);
    vTaskDelay(1500 / portTICK_PERIOD_MS);
    gpio_set_level(POWER_CONTORL_GPIO, 0);
}

void power_off_force()
{
    if(!is_power_on())
        return;
    //TODO: 限制间隔时间
    g_is_force_power_off = true;
    gpio_set_level(POWER_CONTORL_GPIO, 1);
    vTaskDelay(6000 / portTICK_PERIOD_MS);
    gpio_set_level(POWER_CONTORL_GPIO, 0);
    g_is_force_power_off = false;
}


/* Callback to handle commands received from the QCloud cloud */
static esp_err_t light_get_param(const char *id, esp_qcloud_param_val_t *val)
{
    if (!strcmp(id, "power")) {
        val->b = is_power_on();
        ESP_LOGI(TAG, "-----get power:%d", val->b);
    } else if(!strcmp(id, "power_off_force")) {
        ESP_LOGI(TAG, "-----get force power off:%d", val->b);
        val->b = g_is_force_power_off;
    }

    ESP_LOGI(TAG, "Report get, id: %s, val: %d", id, val->i);

    return ESP_OK;
}

/* Callback to handle commands received from the QCloud cloud */
static esp_err_t light_set_param(const char *id, const esp_qcloud_param_val_t *val)
{
    esp_err_t err = ESP_FAIL;
    ESP_LOGI(TAG, "Received set, id: %s, val: %d", id, val->i);
    if(g_action != ACTION_NONE)
    {
        ESP_LOGE(TAG, "busy..., try later");
        return err;
    }

    if (!strcmp(id, "power")) {
        ESP_LOGI(TAG, "-----set power:%d", val->b);
        if(val->b){
            g_action = ACTION_POWER_ON;
        }
        else{
            g_action = ACTION_POWER_OFF;
        }
        err = ESP_OK;
    } else if(!strcmp(id, "power_off_force")) {
        ESP_LOGI(TAG, "-----force off:%d", val->b);
        if(val->b){
            g_action = ACTION_POWER_OFF_FORCE;
        }
        err = ESP_OK;
    }
    g_is_need_report_property = true;
    return err;
}

static void gpio_task_example(void* arg)
{
    uint32_t io_num;
    esp_err_t err = ESP_FAIL;
    for(;;) {
        if(xQueueReceive(gpio_evt_queue, &io_num, 10 / portTICK_PERIOD_MS)) {
            printf("GPIO[%d] intr, val: %d\n", io_num, gpio_get_level(io_num));
            g_is_need_report_property = true;
        }
        if(g_action != ACTION_NONE)
        {
            switch (g_action)
            {
            case ACTION_POWER_ON:
                power_on();
                break;
            case ACTION_POWER_OFF:
                power_off();
                break;
            case ACTION_POWER_OFF_FORCE:
                power_off_force();
                break;
            default:
                break;
            }
            g_action = ACTION_NONE;
        }
        if(g_is_need_report_property)
        {
            ESP_LOGI(TAG, "===g_is_need_report_property now upload property");
            err = esp_qcloud_iothub_report_all_property();
            if(err != ESP_OK)
                ESP_LOGW(TAG, "esp_qcloud_iothub_report_property error:%d", err);
            g_is_need_report_property = false;
        }
    }
}

void remote_pc_contorl_init()
{
    ESP_LOGI(TAG, "-----remote pc control init");
    gpio_config_t io_conf;
    //disable interrupt
    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_OUTPUT;
    io_conf.pin_bit_mask = POWER_CONTORL_GPIO_SEL;
    io_conf.pull_down_en = 1;
    io_conf.pull_up_en = 0;
    //configure GPIO with the given settings
    gpio_config(&io_conf);
    gpio_set_level(POWER_CONTORL_GPIO, 0);

    io_conf.intr_type = GPIO_INTR_ANYEDGE;
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pin_bit_mask = POWER_STATUS_GPIO_SEL;
    io_conf.pull_down_en = 0;
    io_conf.pull_up_en = 0;
    gpio_config(&io_conf);
    gpio_set_intr_type(POWER_STATUS_GPIO, GPIO_INTR_ANYEDGE);

    //create a queue to handle gpio event from isr
    gpio_evt_queue = xQueueCreate(10, sizeof(uint32_t));
    //start gpio task
    xTaskCreate(gpio_task_example, "gpio_task_example", 2048*10, NULL, 10, NULL);

    gpio_install_isr_service(ESP_INTR_FLAG_DEFAULT);
    //hook isr handler for specific gpio pin
    gpio_isr_handler_add(POWER_STATUS_GPIO, gpio_isr_handler, (void*) POWER_STATUS_GPIO);
}




/* Event handler for catching QCloud events */
static void event_handler(void *arg, esp_event_base_t event_base,
                          int32_t event_id, void *event_data)
{
    switch (event_id) {
        case QCLOUD_EVENT_IOTHUB_INIT_DONE:
            esp_qcloud_iothub_report_device_info();
            ESP_LOGI(TAG, "QCloud Initialised");
            break;

        case QCLOUD_EVENT_IOTHUB_BOND_DEVICE:
            ESP_LOGI(TAG, "Device binding successful");
            break;

        case QCLOUD_EVENT_IOTHUB_UNBOND_DEVICE:
            ESP_LOGW(TAG, "Device unbound with iothub");
            esp_qcloud_wifi_reset();
            esp_restart();
            break;

        case QCLOUD_EVENT_IOTHUB_BIND_EXCEPTION:
            ESP_LOGW(TAG, "Device bind fail");
            esp_qcloud_wifi_reset();
            esp_restart();
            break;
            
        case QCLOUD_EVENT_IOTHUB_RECEIVE_STATUS:
            ESP_LOGI(TAG, "receive status message: %s",(char*)event_data);
            break;

        default:
            ESP_LOGW(TAG, "Unhandled QCloud Event: %d", event_id);
    }
}

static esp_err_t get_wifi_config(wifi_config_t *wifi_cfg, uint32_t wait_ms)
{
    ESP_QCLOUD_PARAM_CHECK(wifi_cfg);

    if (esp_qcloud_storage_get("wifi_config", wifi_cfg, sizeof(wifi_config_t)) == ESP_OK) {

#ifdef CONFIG_BT_ENABLE
    esp_bt_controller_mem_release(ESP_BT_MODE_BTDM);
#endif

        return ESP_OK;
    }

    /**< Reset wifi and restart wifi */
    esp_wifi_restore();
    esp_wifi_start();

    /**< The yellow light flashes to indicate that the device enters the state of configuring the network */
    light_driver_breath_start(128, 128, 0); /**< yellow blink */

    /**< Note: Smartconfig and softapconfig working at the same time will affect the configure network performance */

#ifdef CONFIG_LIGHT_PROVISIONING_SOFTAPCONFIG
    char softap_ssid[32 + 1] = CONFIG_LIGHT_PROVISIONING_SOFTAPCONFIG_SSID;
    // uint8_t mac[6] = {0};
    // ESP_ERROR_CHECK(esp_wifi_get_mac(WIFI_IF_STA, mac));
    // sprintf(softap_ssid, "tcloud_%s_%02x%02x", light_driver_get_type(), mac[4], mac[5]);

    esp_qcloud_prov_softapconfig_start(SOFTAPCONFIG_TYPE_ESPRESSIF_TENCENT,
                                       softap_ssid,
                                       CONFIG_LIGHT_PROVISIONING_SOFTAPCONFIG_PASSWORD);
    esp_qcloud_prov_print_wechat_qr(softap_ssid, "softap");
#endif

#ifdef CONFIG_LIGHT_PROVISIONING_SMARTCONFIG
    esp_qcloud_prov_smartconfig_start(SC_TYPE_ESPTOUCH_AIRKISS);
#endif

#ifdef CONFIG_LIGHT_PROVISIONING_BLECONFIG
    char local_name[32 + 1] = CONFIG_LIGHT_PROVISIONING_BLECONFIG_NAME;
    esp_qcloud_prov_bleconfig_start(BLECONFIG_TYPE_ESPRESSIF_TENCENT, local_name);
#endif

    ESP_ERROR_CHECK(esp_qcloud_prov_wait(wifi_cfg, wait_ms));

#ifdef CONFIG_LIGHT_PROVISIONING_SMARTCONFIG
    esp_qcloud_prov_smartconfig_stop();
#endif

#ifdef CONFIG_LIGHT_PROVISIONING_SOFTAPCONFIG
    esp_qcloud_prov_softapconfig_stop();
#endif

    /**< Store the configure of the device */
    esp_qcloud_storage_set("wifi_config", wifi_cfg, sizeof(wifi_config_t));

    /**< Configure the network successfully to stop the light flashing */
    light_driver_breath_stop(); /**< stop blink */

    return ESP_OK;
}




void app_main()
{
    /**
     * @brief Add debug function, you can use serial command and remote debugging.
     */
    esp_qcloud_log_config_t log_config = {
        .log_level_uart = ESP_LOG_INFO,
    };
    ESP_ERROR_CHECK(esp_qcloud_log_init(&log_config));
    /**
     * @brief Set log level
     * @note  This function can not raise log level above the level set using
     * CONFIG_LOG_DEFAULT_LEVEL setting in menuconfig.
     */
    esp_log_level_set("*", ESP_LOG_VERBOSE);

#ifdef CONFIG_LIGHT_DEBUG
    ESP_ERROR_CHECK(esp_qcloud_console_init());
    esp_qcloud_print_system_info(10000);
#endif /**< CONFIG_LIGHT_DEBUG */

    /**
     * @brief Initialize Application specific hardware drivers and set initial state.
     */
    // light_driver_config_t driver_cfg = COFNIG_LIGHT_TYPE_DEFAULT();
    // ESP_ERROR_CHECK(light_driver_init(&driver_cfg));

    /**< Continuous power off and restart more than five times to reset the device */
    if (esp_qcloud_reboot_unbroken_count() >= CONFIG_LIGHT_REBOOT_UNBROKEN_COUNT_RESET) {
        ESP_LOGW(TAG, "Erase information saved in flash");
        esp_qcloud_storage_erase(CONFIG_QCLOUD_NVS_NAMESPACE);
    } else if (esp_qcloud_reboot_is_exception(false)) {
        ESP_LOGE(TAG, "The device has been restarted abnormally");
#ifdef CONFIG_LIGHT_DEBUG
        light_driver_breath_start(255, 0, 0); /**< red blink */
#else
        // ESP_ERROR_CHECK(light_driver_set_switch(true));
#endif /**< CONFIG_LIGHT_DEBUG */
    } else {
        // ESP_ERROR_CHECK(light_driver_set_switch(true));
    }

    /*
     * @breif Create a device through the server and obtain configuration parameters
     *        server: https://console.cloud.tencent.com/iotexplorer
     */
    /**< Create and configure device authentication information */
    ESP_ERROR_CHECK(esp_qcloud_create_device());
    /**< Configure the version of the device, and use this information to determine whether to OTA */
    ESP_ERROR_CHECK(esp_qcloud_device_add_fw_version("0.0.1"));
    /**< Register the properties of the device */
    ESP_ERROR_CHECK(esp_qcloud_device_add_property("power", QCLOUD_VAL_TYPE_BOOLEAN));
    ESP_ERROR_CHECK(esp_qcloud_device_add_property("power_off_force", QCLOUD_VAL_TYPE_BOOLEAN));
    // ESP_ERROR_CHECK(esp_qcloud_device_add_property("saturation", QCLOUD_VAL_TYPE_INTEGER));
    // ESP_ERROR_CHECK(esp_qcloud_device_add_property("value", QCLOUD_VAL_TYPE_INTEGER));

    /**< The processing function of the communication between the device and the server */
    ESP_ERROR_CHECK(esp_qcloud_device_add_property_cb(light_get_param, light_set_param));
    
    /**
     * @brief Initialize Wi-Fi.
     */
    ESP_ERROR_CHECK(esp_qcloud_wifi_init());
    ESP_ERROR_CHECK(esp_event_handler_register(QCLOUD_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL));

    /**
     * @brief Get the router configuration
     */
    wifi_config_t wifi_cfg = {0};
    ESP_ERROR_CHECK(get_wifi_config(&wifi_cfg, portMAX_DELAY));

    /**
     * @brief Connect to router
     */
    ESP_ERROR_CHECK(esp_qcloud_wifi_start(&wifi_cfg));
    ESP_ERROR_CHECK(esp_qcloud_timesync_start());

    /**
     * @brief Connect to Tencent Cloud Iothub
     */
    ESP_ERROR_CHECK(esp_qcloud_iothub_init());
    ESP_ERROR_CHECK(esp_qcloud_iothub_start());
    ESP_ERROR_CHECK(esp_qcloud_iothub_ota_enable());

    remote_pc_contorl_init();
}
