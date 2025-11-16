# home_assistant_pvoutput_upload
Script for uploading PV production data produced by lxp-bridge from Home Assistant to PVOutput.org

# Setup

You'll need to already have installed Home Assistant along with the following add-ons:

* Mosquitto Broker
* lxp-bridge (https://github.com/joshs85/lxp-bridge)
* HACS (https://github.com/hacs/addons/tree/main/get)
* pyscript (installed through HACS)
* File editor (for configuration file editing)

1. Create an account on PVOutput.org
    1. Enable API access and create an API Key on the settings page. *Keep this API Key for later*.
    2. Create a new System and get it's System ID.
        1. Go to Add Output, next to System Name hit ADD, fill out the information and Save.
        2. Go to the Settings page and look for your System ID under Registered Systems. *Keep this System ID for later*.
2. In your lxp-bridge configuration settings get the value from the datalog field. This is typically your inverters wifi module serial number. *Keep this value for later*.
3. Use File editor to save `max_pv_sensors.yaml` in to your `/homeassistant/` folder and add a template import for the file to `/homeassistant/configuration.yaml`. Add `template: !include max_pv_sensors.yaml` or if you already a template section in the file add `template max_pv_sensors: !include max_pv_sensors.yaml`
4. Use File editor to save `pvoutput_upload_eod_summary.py` to `/homeassistant/pyscript/`.
5. Set up an Automation to run the pvoutput_upload_eod_summary every day just before midnight.
    1. Settings > Automations > Create Automation > Create new automation
        1. Add Trigger > Time and location > Time
            1. Fixed time
            2. At time: 11:56:00 PM
        2. Add Action > Search for pyscript and pick the pvoutput_upload_eod_summary script.
            1. Set Action data to:

```
apikey: <replaceMe>
systemid: "<replaceMe>"
lxpBridgeDatalog: <replaceMe>
upload: true
```

You can also test the `pvoutput_upload_eod_summary.py` script directly to verify it is working through Developer tools > Actions tab, for the action search for pvoutput_upload_eod_summary, and use the following inputs:

```
action: pyscript.pvoutput_upload_eod_summary
data:
  apikey: asdf
  systemid: “qwerty”
  lxpBridgeDatalog: "bj12345678"
```

This should produce output similar to:

```
payload:
  d: "20251115"
  g: 4400
  e: 0
  c: 9900
  pp: 1884
  pt: "12:45"
```
