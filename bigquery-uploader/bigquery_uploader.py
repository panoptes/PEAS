#!/usr/bin/python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import collections

unit_serial = "PAN001"
filename = "/Users/mimming/code/environmental-analysis-system/cached_data/20160515_weather.json"

schema_mapping = {
    "_id_$oid": "oid",
    "time_$date": "timestamp",
    "date_$date": "timestamp",
    "data_Ambient Temperature": "ambient_temperature",
    "data_ambient_temp_C": "ambient_temperature",
    "data_weather_sensor_name": "weather_sensor_name",
    "data_weather_sensor_serial_number": "weather_sensor_serial_number",
    "data_errors_error_1": "error_1",
    "data_errors_error_2": "error_2",
    "data_errors_error_3": "error_3",
    "data_errors_error_4": "error_4",
    "data_Errors_!E1": "error_1",
    "data_Errors_!E2": "error_2",
    "data_Errors_!E3": "error_3",
    "data_Errors_!E4": "error_4",
    "data_weather_sensor_firmware_version": "weather_sensor_firmware_version",
    "data_gust_condition": "gust_safe",
    "data_Internal Voltage": "internal_voltage",
    "data_internal_voltage_V": "internal_voltage",
    "data_LDR Resistance": "ldr_resistance",
    "data_ldr_resistance_Ohm": "ldr_resistance",
    "data_PWM": "pwm_value",
    "data_pwm_value": "pwm_value",
    "data_rain_condition": "rain_safe",
    "data_rain_frequency": "rain_frequency",
    "data_safe": "safe",
    "data_rain_sensor_temp_C": "rain_sensor_temperature",
    "data_Rain Sensor Temperature": "rain_sensor_temperature",
    "data_sky_condition": "sky_safe",
    "data_Sky Safe": "sky_safe",
    "data_Sky Temperature": "sky_temperature",
    "data_sky_temp_C": "sky_temperature",
    "data_Switch": "switch",
    "data_Switch Status": "switch_status",
    "data_wind_condition": "wind_safe",
    "data_Wind Speed": "wind_speed",
    "data_wind_speed_KPH": "wind_speed",
}

default_values = {
    "unit_serial_number": "PAN001"
}


# print("processing unit " + unit_serial + " file " + filename)

def remap(d):
    remapped_data = d.copy()

    for key in d:
        if key in schema_mapping:
            del remapped_data[key]
            remapped_data[schema_mapping[key]] = d[key]

    return remapped_data


def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def fix_timestamps(d):

    if 'timestamp' in d:
        d['timestamp'] /= float(1000)

    return d

def add_defaults(d):
    for key in default_values:
        if key not in d:
            d[key] = default_values[key]
    return d

with open(filename, 'rb') as f:
    file_content = f.read()

    # assuming it's a list, just load it up
    file_data = json.loads(file_content.decode('utf-8'))

    for record in file_data:
        flat_record = flatten(record)
        remapped_record = remap(flat_record)
        defaults_added = add_defaults(remapped_record)
        timestamps_fixed = fix_timestamps(defaults_added)

        print(json.dumps(timestamps_fixed))



