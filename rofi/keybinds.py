import os
import re
import subprocess
import sys

KEYBINDS_FILE = os.path.expanduser("$HOME/.config/hypr/keybinds.conf")
VAR_FILE = os.path.expanduser("$HOME/.config/hypr/variables.conf")
SEP = "\x1f"

MOD_REPLACEMENTS = {
	"$mod": "Win",
	"SHIFT": "Shift",
	"CTRL": "Ctrl",
	"ALT": "Alt",
}

KEY_REPLACEMENTS = {
	"Return": "Enter",
	"bracketright": "]",
	"bracketleft": "[",
	"comma": ",",
	"period": ".",
	"grave": "`",
	"XF86AudioRaiseVolume": "Vol+",
	"XF86AudioLowerVolume": "Vol-",
	"XF86AudioMute": "Mute",
	"XF86AudioMicMute": "MicMute",
	"XF86MonBrightnessUp": "Bright+",
	"XF86MonBrightnessDown": "Bright-",
	"mouse:272": "LMB",
}

EXEC_PATTERNS = [
	(r"terminal|\$terminal", "Terminal"),
	(r"killactive", "Close window"),
	(r"hyprshutdown|exit", "Exit Hyprland"),
	(r"\$files|nemo", "Files"),
	(r"\$menu.*drun", "Menu"),
	(r"\$menu.*run", "Command Menu"),
	(r"copyq", "Clipboard History"),
	(r"waybar", "Waybar"),
	(r"hyprlock", "Lock"),
	(r"powermenu", "Power Menu"),
	(r"hyprshot.*region", "Screenshot (Region)"),
	(r"hyprshot.*window", "Screenshot (Window)"),
	(r"hyprshot.*output", "Screenshot (Screen)"),
	(r"wpctl.*raise|volume.*5%\+", "Volume Up"),
	(r"wpctl.*lower|volume.*5%-", "Volume Down"),
	(r"wpctl.*mute.*SINK", "Mute"),
	(r"wpctl.*mute.*SOURCE", "Mic Mute"),
	(r"brightnessctl.*set.*\+", "Brightness Up"),
	(r"brightnessctl.*set.*-", "Brightness Down"),
]

BIND_RE = re.compile(r"^binde?\s*=")


def describe_exec(args: str) -> str:
	for pattern, desc in EXEC_PATTERNS:
		if re.search(pattern, args):
			return desc
	return args


def describe(dispatcher: str, args: str) -> str:
	if dispatcher == "exec":
		return describe_exec(args)
	if dispatcher == "workspace":
		return f"Go to workspace {args}"
	if dispatcher == "movetoworkspace":
		return f"Move window to workspace {args}"
	if dispatcher == "movefocus":
		return f"Focus {args}"
	if dispatcher == "togglefloating":
		return "Toggle floating"
	if dispatcher == "fullscreen":
		return "Toggle fullscreen"
	if dispatcher == "resizeactive":
		return "Resize window"
	if dispatcher == "movewindow":
		if "mon" in args:
			return "Move window to monitor"
		return f"Move window {args}"
	if dispatcher == "focusmonitor":
		return f"Focus monitor {args}"
	if dispatcher == "movecurrentworkspacetomonitor":
		return "Move workspace to monitor"
	if dispatcher == "togglegroup":
		return "Toggle window group"
	if dispatcher == "changegroupactive":
		if "f" in args:
			return "Next tab in group"
		if "b" in args:
			return "Previous tab in group"
		return "Change group tab"
	return f"{dispatcher} {args}"

def parse_keybinds():
	if not os.path.isfile(KEYBINDS_FILE):
		subprocess.run(
			["rofi", "-dmenu", "-p", "Error"],
			input="keybinds.conf not found",
			text=True,
		)
		sys.exit(1)

	entries = []

	with open(KEYBINDS_FILE) as f:
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			if not BIND_RE.match(line):
				continue

			content = line.split("=", 1)[1].strip()
			parts = content.split(",")
			if len(parts) < 3:
				continue

			mods = parts[0].strip()
			key = parts[1].strip()
			dispatcher = parts[2].strip()
			args = ",".join(parts[3:]).strip() if len(parts) > 3 else ""

			if "keybinds.sh" in args or "keybinds.py" in args:
				continue

			display_mods = mods
			for old, new in MOD_REPLACEMENTS.items():
				display_mods = display_mods.replace(old, new)

			if display_mods:
				keybind = f"{display_mods} + {key}"
			else:
				keybind = key

			for old, new in KEY_REPLACEMENTS.items():
				keybind = keybind.replace(old, new)
			description = describe(dispatcher, args)
			if dispatcher=="exec":
				dispatch_cmd = f"{args}"
			else:
				dispatch_cmd = f"hyprctl dispatch {dispatcher} {args}"
    
			vars = {}
			with open(VAR_FILE) as var_file:
				for line in var_file:
					line = line.strip()
					if line.startswith("$") and "=" in line:
						key, _, value = line.partition(" = ")
						vars[key.strip()] = value.strip()

			for key, value in vars.items():
				dispatch_cmd = dispatch_cmd.replace(key, value)


			display = f"{keybind:<30}  {description}"
			entries.append((display, dispatch_cmd))

	return entries


def main():
	entries = parse_keybinds()
	if not entries:
		return

	display_lines = "\n".join(e[0] for e in entries)

	result = subprocess.run(
		[
			"rofi",
			"-dmenu",
			"-i",
			"-p",
			"Keybinds",
			"-theme",
			os.path.expanduser("$HOME/.config/rofi/help.rasi"),
			"-no-custom",
			"-format",
			"i",
		],
		input=display_lines,
		text=True,
		capture_output=True,
	)

	if result.returncode != 0:
		return

	selected = result.stdout.strip()
	if not selected:
		return

	index = int(selected)
	subprocess.run(entries[index][1], shell=True)


if __name__ == "__main__":
	main()
