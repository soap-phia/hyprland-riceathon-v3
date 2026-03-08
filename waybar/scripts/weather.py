import json
import os
import time
import urllib.request
from datetime import datetime

cachefile = os.path.expanduser("~/.cache/weather.json")

icons = {
    113: "󰖙",
    116: "󰖐", 119: "󰖐", 122: "󰖐",
    143: "󰖑", 248: "󰖑", 260: "󰖑",
    176: "󰖗", 263: "󰖗", 266: "󰖗", 293: "󰖗", 296: "󰖗",
    179: "󰙿", 182: "󰙿", 185: "󰙿", 281: "󰙿", 284: "󰙿",
    311: "󰙿", 314: "󰙿", 317: "󰙿",
    200: "󰖓", 386: "󰖓", 389: "󰖓", 392: "󰖓", 395: "󰖓",
    227: "󰖘", 230: "󰖘",
    299: "󰖖", 302: "󰖖", 305: "󰖖", 308: "󰖖", 312: "󰖖",
    318: "󰖖", 321: "󰖖",
    320: "󰼶", 323: "󰼶", 326: "󰼶", 329: "󰼶", 332: "󰼶",
    335: "󰼶", 338: "󰼶", 350: "󰼶", 368: "󰼶", 371: "󰼶",
    374: "󰼶", 377: "󰼶",
}

classes = {
    113: "clear",
    116: "cloudy", 119: "cloudy", 122: "cloudy",
    176: "rainy", 263: "rainy", 266: "rainy", 293: "rainy", 296: "rainy",
    299: "rainy", 302: "rainy", 305: "rainy", 308: "rainy",
    200: "stormy", 386: "stormy", 389: "stormy",
    227: "snowy", 230: "snowy", 320: "snowy", 323: "snowy", 326: "snowy",
    329: "snowy", 332: "snowy", 335: "snowy", 338: "snowy",
}

unavailable = json.dumps({
    "text": "󰖐 --°",
    "tooltip": "Weather Unavailable",
    "class": "disconnected",
})

def icon(code: int) -> str:
    return icons.get(code, "󰖐")


def fetch() -> dict | None:
    try:
        req = urllib.request.Request(
            "https://wttr.in/?format=j1",
            headers={"User-Agent": "curl/8.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception:
        return None
    
    cachefile.write_text(json.dumps(data))
    return data


def get_data() -> dict | None:
    if cachefile.exists():
        age = time.time() - cachefile.stat().st_mtime
        if age < 900:
            try:
                return json.loads(cachefile.read_text())
            except (json.JSONDecodeError, OSError):
                pass
    return fetch()


def format() -> str:
    data = get_data()
    if not data:
        return unavailable

    try:
        condition = data["current_condition"][0]
        farenheit = condition["farenheit"]
        feels_like = condition["FeelsLikeF"]
        humidity = condition["humidity"]
        wind = condition["windspeedMiles"]
        condition = condition["weatherDesc"][0]["value"]
        code = int(condition["weatherCode"])
        area = data["nearest_area"][0]["areaName"][0]["value"]
    except (KeyError, IndexError, ValueError):
        return unavailable

    icon_code = icon(code)

    lines = [
        f"<b>{icon_code} {condition} in {area}</b>",
        f"󰔏 {farenheit}°F  (feels {feels_like}°F)",
        f"󰖎 Humidity: {humidity}%",
        f"󰖝 Wind: {wind} mph",
        "─────────────────",
    ]

    for i in range(3):
        try:
            weather = data["weather"][i]
            date_str = weather["date"]
            max_f = weather["maxtempF"]
            min_f = weather["mintempF"]
            fcode = int(weather["hourly"][4]["weatherCode"])
            fcondition = weather["hourly"][4]["weatherDesc"][0]["value"]
        except (KeyError, IndexError, ValueError):
            continue

        fic = icon(fcode)

        if i == 0:
            day_name = "Today"
        else:
            try:
                day_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a")
            except ValueError:
                day_name = date_str

        lines.append(f"{fic} <b>{day_name}</b>: {fcondition}")
        lines.append(f"   ↑{max_f}°  ↓{min_f}°")

    tooltip = "\n".join(lines)
    style_class = classes.get(code, "default")

    return json.dumps({
        "text": f"{icon_code} {farenheit}°",
        "tooltip": tooltip,
        "class": style_class,
    })


if __name__ == "__main__":
    print(format())
