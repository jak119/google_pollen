# Google Pollen integration for Home Assistant

Provides per-pollen-type index and category sensors for one or more locations using the [Google Pollen API](https://developers.google.com/maps/documentation/pollen/overview).

## Sensors

Each configured location exposes the following sensors:

### Per pollen type (tree, grass, weed)

| Sensor | Default | Description |
|--------|---------|-------------|
| {Type} pollen index | Enabled | UPI value (0–5) for that pollen type |
| {Type} pollen category | Enabled | Text label for that type's level |
| {Type} pollen index description | Disabled | Textual explanation of the current index level |
| {Type} pollen color | Disabled | Hex color code representing the index level (e.g., `#ff0000`) |
| {Type} pollen health recommendations | Disabled | Health guidance for the current pollen level |

The pollen index sensors include long-term statistics support. Disabled-by-default sensors can be enabled individually under **Settings → Devices & services**.

## Prerequisites

You need a Google Cloud project with the **Pollen API** enabled and a valid API key. Follow Google's [get an API key](https://developers.google.com/maps/documentation/pollen/get-api-key) guide to create one.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jak119&repository=google_pollen&category=integration)

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

## Disclaimer

This integration was largely developed with the help of Claude. I spent time on this for my own use however decided to also make it available in case it'd help others.
