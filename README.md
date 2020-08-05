# rpi_pir_sensor
An attempt to control wifi blub with PIR sensor

## Setup
### Hardware
- Raspberry Pi
- PIR sensor (hc-sr501): [datasheet](https://components101.com/sites/default/files/component_datasheet/HC%20SR501%20PIR%20Sensor%20Datasheet.pdf)
- Tuya RGBW wifi blub: [Kogan model](https://www.kogan.com/au/buy/kogan-smarterhome-10w-ambient-rgbw-smart-bulb-e27-pack-of-4/)
technically it should works with any wifi dimmalbe lighting device
### Software
- Python 3.8
- Homebridge
  - [homebridge-tuya-web](https://github.com/milo526/homebridge-tuya-web)

### Getting `aid` and `iid` of your device
`http://hostname:51272/accessories`
check the response for `aid` and `iid`
