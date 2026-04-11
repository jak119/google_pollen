# Google Pollen integration for Home Assistant

Provides pollen index and category sensors for one or more locations using the [Google Pollen API](https://developers.google.com/maps/documentation/pollen/overview).

## Sensors

Each configured location exposes five sensors:

| Sensor | Description |
|--------|-------------|
| Pollen index | Overall UPI value (0–5), the maximum across in-season pollen types |
| Pollen category | Text label for the overall level (e.g., "Low", "Medium", "High") |
| Tree pollen | UPI value for tree pollen |
| Grass pollen | UPI value for grass pollen |
| Weed pollen | UPI value for weed pollen |

Tree, grass, and weed sensors include long-term statistics support.

## Prerequisites

You need a Google Cloud project with the **Pollen API** enabled and a valid API key. Follow Google's [get an API key](https://developers.google.com/maps/documentation/pollen/get-api-key) guide to create one.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant.
2. Go to **Integrations** and click the menu (⋮) → **Custom repositories**.
3. Add this repository URL and select **Integration** as the category.
4. Search for **Google Pollen** and click **Download**.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/google_pollen` folder into your `<config>/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & services** → **Add integration**.
2. Search for **Google Pollen**.
3. Enter your API key and pick your first location.
4. Additional locations can be added later via the integration's **Add location** option.
