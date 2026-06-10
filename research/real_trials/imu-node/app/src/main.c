#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(imu_node, LOG_LEVEL_INF);

#if DT_HAS_COMPAT_STATUS_OKAY(st_lsm6dsl)
#define IMU_NODE DT_COMPAT_GET_ANY_STATUS_OKAY(st_lsm6dsl)
#elif DT_NODE_HAS_STATUS(DT_ALIAS(imu0), okay)
#define IMU_NODE DT_ALIAS(imu0)
#else
#error "No enabled IMU node found. Add an imu0 alias or st,lsm6dsl node in the board overlay."
#endif

int main(void)
{
    const struct device *imu = DEVICE_DT_GET(IMU_NODE);

    LOG_INF("IMU scaffold start");
    if (!device_is_ready(imu)) {
        LOG_ERR("IMU device is not ready: %s", imu->name);
        return 0;
    }

    LOG_INF("IMU device ready: %s", imu->name);

    while (1) {
        struct sensor_value accel[3];
        int rc = sensor_sample_fetch(imu);

        if (rc == 0) {
            rc = sensor_channel_get(imu, SENSOR_CHAN_ACCEL_XYZ, accel);
        }

        if (rc == 0) {
            LOG_INF("accel x=%d.%06d y=%d.%06d z=%d.%06d",
                    accel[0].val1, accel[0].val2,
                    accel[1].val1, accel[1].val2,
                    accel[2].val1, accel[2].val2);
        } else {
            LOG_ERR("sensor sample failed: %d", rc);
        }

        k_sleep(K_SECONDS(1));
    }
}
