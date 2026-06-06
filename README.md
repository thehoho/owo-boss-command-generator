# OwO Boss Command Generator

Free Windows utility that converts OwO boss info and boss screenshots into NeonUtil boss commands.

## Features

- **Text Mode** – paste `owo boss i` output and auto-generate commands
- **Image Mode** – scan boss screenshots directly from Discord
- Weapon and passive icon dropdowns
- Automatically calculates QE
- Auto copies generated command to clipboard
- Mapping warnings for unknown weapons and passives
- Manual editing of detected values before generating

---

## How To Use

### Text Mode

#### Step 1

In Discord, run:

```txt
owo boss i
```

#### Step 2

For each boss message:

1. Right-click the boss message
2. Click **Copy Message**
3. Paste it into Boss 1, Boss 2, or Boss 3

⚠️ **Do NOT highlight the text and copy manually.**

The parser expects Discord's original message formatting. Highlight-copying may remove formatting and cause incorrect detection.

#### Step 3

(Optional) Enter custom HP values.

If left blank, the default HP values will be used.

#### Step 4

Click:

```txt
Generate & Copy Command
```

The generated command is automatically copied to your clipboard.

---

### Image Mode

#### Recommended Method

1. Open the boss image in Discord.
2. Right-click the image.
3. Click **Copy Image**.
4. Open OwO Boss Command Generator.
5. Press **Ctrl + V** inside Image Mode.

This is currently the most reliable method.

#### Alternative Methods

You can also:

- Use **Browse Image**
- Drag and drop a local image file from your computer

⚠️ Dragging directly from Discord usually does **not** work because Discord does not provide a local file path when dragging images.

#### After Importing

The app will automatically:

- Detect bosses
- Detect weapons
- Detect passives
- Detect HP values
- Generate a command

#### Review Results

Image Mode is still in beta.

Always verify:

- Boss levels
- HP values
- Weapon detection
- Passive detection

before using the generated command.

#### Generate Command

Click:

```txt
Generate & Copy Command
```

The command is automatically copied to your clipboard.

---

## Download

Download the latest portable release:

→ [Latest Release](https://github.com/thehoho/owo-boss-command-generator/releases/latest)

---

## Known Issues

- Image Mode is currently beta.
- OCR may occasionally misread similar digits.
- Always verify level and HP values before using the generated command.

---

## Credits

Made by Hassaan.

This project is not affiliated with, endorsed by, or officially connected to OwO Bot, NeonUtil, or Discord.
This project uses Tesseract OCR for image text recognition. Tesseract OCR and tessdata are licensed under Apache License 2.0
