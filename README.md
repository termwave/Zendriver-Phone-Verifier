<h1 align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=30&pause=900&color=00FF00&center=true&vCenter=true&width=520&lines=%F0%9F%90%9B+Ultimate+Verifier;Built+by+Termwave;Hackish+UI+%7C+Serious+Controls" alt="Typing SVG" />
</h1>

```
 █    ██  ██▓  ▄▄▄█████▓ ██▓ ███▄ ▄███▓ ▄▄▄     ▄▄▄█████▓▓█████ 
 ██  ▓██▒▓██▒  ▓  ██▒ ▓▒▓██▒▓██▒▀█▀ ██▒▒████▄   ▓  ██▒ ▓▒▓█   ▀ 
▓██  ▒██░▒██░  ▒ ▓██░ ▒░▒██▒▓██    ▓██░▒██  ▀█▄ ▒ ▓██░ ▒░▒███   
▓▓█  ░██░▒██░  ░ ▓██▓ ░ ░██░▒██    ▒██ ░██▄▄▄▄██░ ▓██▓ ░ ▒▓█  ▄ 
▒▒█████▓ ░██████▒▒██▒ ░ ░██░▒██▒   ░██▒ ▓█   ▓██▒ ▒██▒ ░ ░▒████▒
░▒▓▒ ▒ ▒ ░ ▒░▓  ░▒ ░░   ░▓  ░ ▒░   ░  ░ ▒▒   ▓▒█░ ▒ ░░   ░░ ▒░ ░
░░▒░ ░ ░ ░ ░ ▒  ░  ░     ▒ ░░  ░      ░  ▒   ▒▒ ░   ░     ░ ░  ░
 ░░░ ░ ░   ░ ░   ░       ▒ ░░      ░     ░   ▒    ░         ░   
   ░         ░  ░        ░         ░         ░  ░           ░  ░
```

> 🧪 **Ultimate Verifier** — a desktop-driven workflow that assists with token-based logins, manual CAPTCHA solving, and SMS-based verification in a controlled, auditable way.  
> ⚠️ **For educational, research, and authorized testing only.** You are responsible for complying with platform ToS and local laws.

---

## ✨ Features

- 🟢 **Terminal Aesthetic** (animated timestamps, gradient banners, slick logs)
- 🔔 **Desktop Notifications** (optional) via `notify-py`
- 📦 **Process Control** with safe multiprocessing caps
- 📜 **Audit-Friendly Logs** and verified token output file
- 🧩 **Manual CAPTCHA Flow** — the browser stays on screen so *you* solve it
- 📲 **SMS Verification Hook** (5sim API; bring your own key)

---

## ⚙️ Requirements

- Python 3.11+
- Google Chrome (stable) installed
- Recommended OS: Windows 10/11
- Dependencies (installed below)

---

## 📥 Install

```bash
# 1) Start Code
python term.py

# 2) Install deps
pip install -r req.txt
# or, if you prefer manual:
pip install requests psutil colorama zendriver pystyle notify-py urllib3 httpx
```

> 💡 If `zendriver` requires Chrome, make sure Chrome is installed and on a compatible version.

---

## 🔧 Configure

Create `config.json` in the project root:

```json
{
    "api_key": "",
    "api_url": "https://5sim.net/v1",
    "country": "kenya",
    "operator": "virtual51",
    "product": "discord",
    "country_code": "254",
    "notify": true,
    "notification_icon": "data/pack.ico"
}
```

Also create `tokens.txt` with one account per line:

```
email@example.com:SuperSecretPass:discordTokenHere
```

> 🗝️ On first run you'll be asked for a license key. This binds to your HWID and updates IP history for auditability.

---

## 🚀 Run

```bash
python main.py
```

You’ll be prompted for:
- **Parallel threads** (keep reasonable to avoid rate limits)

Successful verifications append to:

```
verified.txt   # format: email:password:token
```

---

## 🧱 Safety & Ethics

- ❗ **No bypassing security** is provided here. CAPTCHA is solved by *you*.
- 🧭 **Use only on accounts you own or have written permission to test.**
- 📜 Respect platform Terms of Service and regional laws.
- 🛡️ This repo is for **education, research, and internal testing**.

---

## 🧰 Troubleshooting

- Browser won’t start? Confirm Chrome is installed and compatible with `zendriver`.
- OTP not received? Check your SMS provider quota, country/operator, or try again later.
- High rate limits? Reduce threads and add delays between attempts.
- No `config.json`? The app won’t start—create it as shown above.

---

## 👤 Credits

**Creator:** `Tunable | Termwave`  
**Contributors:** Wizard • Predzen  
**License:** MIT

> “Make it look like magic. Document it like science.”

---

<p align="center">
  <img alt="divider" src="https://img.shields.io/badge/Status-Active-00ff00?style=for-the-badge" />
  <img alt="style" src="https://img.shields.io/badge/Style-Hacker%20Green-00ff00?style=for-the-badge" />
  <img alt="safe" src="https://img.shields.io/badge/Use-Authorized%20Only-ff0000?style=for-the-badge" />
</p>
