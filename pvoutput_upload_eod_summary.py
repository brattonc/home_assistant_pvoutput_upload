# Copyright 2025 Curtis Bratton
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# This script uploads PV production data from Home Assistant to pvoutput.org. This script is intended for use with Home Assistant running pyscript, Mosquitto Broker, and lxp-bridge.
# * Python add-ons other than pyscript will not work.
# * The script references sensor names based on those produced by lxp-bridge v0.14.0 (https://github.com/joshs85/lxp-bridge). Other versions and forks of lxp-bridge may or may not produce compatible sensors.
# * Run this script by creating an Automation that runs every day just before midnight. Setting the Automation to run earlier will cause the power "consumed" value to be inaccurate.
#
# NOTE: If your inverter does not automatically update it's time based on daylight savings in the Spring and Fall data collected will be inaccurate after the time change. In the Fall this will result in uploading 0 for the "today" sensor values or missing an hour of data in the Spring until you change the time on your inverter.
# NOTE: This script requires two additional Sensors to be created. These Sensors use data from other sensors populated by lxp-bridge and can be found in the max_pv_sensors.yaml file. If you don't want to use these sensors pass in usePeakProduction=False.

import datetime
import requests

@service(supports_response="optional")
def pvoutput_upload_eod_summary(apikey, systemid, lxpBridgeDatalog, upload=False, usePeakProduction=True):
    """
    Collects PV production data from lxp-bridge sensors and uploads
    to pvoutput.org.

    Parameters:
    apikey (string): Your pvoutput.org API key.
    systemid (string): The sid or system ID of your PV System on pvoutput.org
    lxpBridgeDatalog (string): The value used in the lxp-bridge datalog
        configuration field. This is typically your inverters wifi module
        serial number.
    upload (boolean, optional): Control if data should be uploaded or not.
        Useful for testing without updating your outputs on pvoutput.org.
        Defaults to False.
    usePeakProduction (boolean, optional): Control if Peak Production data is
        collected and uploaded. Additional Sensors are required to make this
        work. See here: http://asdfg.qwert Defaults to True.

    Returns:
    dict: The payload data uploaded to pvoutput.org along with the response
        status code and text, or if upload is false only the payload that
        would have been uploaded.
    """
    
    # lxp-bridge converts the sensor names to all lower case.
    datalog = lxpBridgeDatalog.lower()
    url = "https://pvoutput.org/service/r2/addoutput.jsp"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Pvoutput-Apikey": apikey,
        "X-Pvoutput-SystemId": systemid,
    }
    api_data = {
        "date": datetime.datetime.now().strftime('%Y%m%d'),
        "generated": int(float(state.get(f"sensor.lxp_{datalog}_pv_generation_today")) * 1000),
        "exported": int(float(state.get(f"sensor.lxp_{datalog}_energy_to_grid_today")) * 1000),
        "from_grid": int(float(state.get(f"sensor.lxp_{datalog}_energy_from_grid_today")) * 1000),
        "battery_charge": int(float(state.get(f"sensor.lxp_{datalog}_battery_charge_today")) * 1000),
        "battery_discharge": int(float(state.get(f"sensor.lxp_{datalog}_battery_discharge_today")) * 1000),
    }
    
    if usePeakProduction:
        api_data["peak_production"] = int(state.get("sensor.daily_max_pv_power"))
        api_data["peak_production_time"] = state.get("sensor.daily_max_pv_power_time")
    
    api_data["consumed"] = api_data["generated"] - api_data["exported"] + api_data["from_grid"] + api_data["battery_discharge"]
    
    # We have to override the "exported" value otherwise pvoutput will throw an http 400
    # "exported" can be greater than "generated" if Forced Export is used to discharge batteries to grid.
    if api_data["exported"] > api_data["generated"]:
        api_data["exported"] = api_data["generated"]
    
    payload_data = {
        "d": api_data["date"],
        "g": api_data["generated"],
        "e": api_data["exported"],
        "c": api_data["consumed"],
    }
    
    if usePeakProduction:
        payload_data["pp"] = api_data["peak_production"]
        payload_data["pt"] = api_data["peak_production_time"]
    
    if upload:
        response = task.executor(requests.post, url, headers=headers, data=payload_data)
        if response.status_code != 200:
            log.warning("Failed to post data to PVOutput status={}, message={}".format(response.status_code, response.text))
        return {
            "payload": payload_data,
            "response_status": response.status_code,
            "response_payload": response.text
        }
    
    return {
        "payload": payload_data,
    }
