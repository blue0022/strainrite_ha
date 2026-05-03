# Strainrite Electric Fence — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![hassfest](https://github.com/bret536/strainrite_ha/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/bret536/strainrite_ha/actions/workflows/hassfest.yaml)
[![validate](https://github.com/bret536/strainrite_ha/actions/workflows/validate.yaml/badge.svg)](https://github.com/bret536/strainrite_ha/actions/workflows/validate.yaml)

Local integration for Strainrite WiFi/IP electric fence energizers (MB series). Provides arm/disarm control and full status monitoring via the device's built-in HTTP API — no cloud, no account required.

## Supported Devices

- MB3, MB8, MB12 series energizers with WiFi (Virtual Keypad / IP interface)

## Features

- **Switch** — Arm / disarm the fence
- **Sensors** — Fence voltage, energy output, supply voltage, CPU temperature, signal strength, runtime, alarm status
- **Buttons** — Clear alarm, Mute alarm
- **HomeKit** — Expose the arm/disarm switch to Apple Home via the built-in HomeKit Bridge integration
- **Local polling** — No cloud dependency; polls the device every 30 seconds

## Installation

### Via HACS (recommended)

1. In HACS, go to **Integrations** → three-dot menu → **Custom repositories**
2. Add `https://github.com/bret536/strainrite_ha` with category **Integration**
3. Install **Strainrite Electric Fence** and restart Home Assistant

### Manual

Copy `custom_components/strainrite/` into your HA config directory under `custom_components/`, then restart.

## Configuration

1. Go to **Settings → Integrations → Add Integration**
2. Search for **Strainrite Electric Fence**
3. Enter the IP address of your energizer (default `192.168.0.74`)
4. The integration will validate connectivity and create all entities

## Entities

| Entity | Description |
|--------|-------------|
| `switch.strainrite_fence` | Arm / disarm the energizer |
| `sensor.strainrite_fence_voltage` | Output voltage (kV) |
| `sensor.strainrite_energy_output` | Output energy (J) |
| `sensor.strainrite_supply_voltage` | DC supply input (V) |
| `sensor.strainrite_cpu_temperature` | Controller temperature (°C) |
| `sensor.strainrite_signal_strength` | WiFi signal (dBm) |
| `sensor.strainrite_runtime` | Uptime since last reset |
| `sensor.strainrite_alarm` | Active alarm description |
| `button.strainrite_clear_alarm` | Clear active alarm |
| `button.strainrite_mute_alarm` | Mute alarm buzzer |

## HomeKit

Once the integration is set up:

1. Go to **Settings → Integrations → Add Integration → HomeKit Bridge**
2. The fence switch will appear in Apple Home as a switch accessory
3. Control with Siri: *"Hey Siri, turn on/off the fence"*

## Notes

- The device's HTTP API requires no authentication on the local network
- The integration uses `local_polling` — ensure the energizer has a static/reserved IP
- Tested on Strainrite MB8 (firmware 1v27, WiFi module 2.22)
