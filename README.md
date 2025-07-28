# 🛡️ PentAgent - AI-Powered VAPT Agent

**PentAgent** is an AI-powered Vulnerability Assessment and Penetration Testing (VAPT) tool designed for cybersecurity professionals and ethical hackers. It features a clean modular GUI and intelligent agent-based automation that handles scanning, analysis, and reporting—saving you time and reducing manual work.
---

## ✨ Features

- 🤖 **Multi-AI Support**: Gemini, OpenAI, Anthropic, Ollama (local)
- 🧠 **Smart Agent Workflows**: Powered by LangGraph
- 🖥️ **Modular Web UI**: Built with NiceGUI
- 🔁 **Dual Modes**: Manual Approval or Fully Automatic
- 📊 **Real-time Logs & Result Analysis**
- 🕒 **Scan History Tracking**
- 🌗 **Light/Dark Theme Toggle**

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/chaitanyavishwakarma2009/PentAgent.git
cd PentAgent
```
### 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate

```
### 3. Install dependencies
```bash
pip install -r requirements.txt
```
Optional (faster): use uv if installed
```bash
uv pip install -r requirements.txt
```
### 4. Setup environment variables
```bash
cp .env.example .env
# Fill in your OpenAI, Gemini, Anthropic, or Ollama keys
```
### 5.🔧 Install Global Launcher
```bash
chmod +x install.sh
./install.sh

```
## 6. You're all set!
to run:
```bash
pentagent
```

# Description
PentAgent is an AI-powered Vulnerability Assessment and Penetration Testing (VAPT) tool designed for cybersecurity professionals and ethical hackers. It uses a modular GUI and intelligent agents to automate scanning, interpretation, and reporting — saving you time and effort.

### 🔍 Scan Types Supported:
- Reconnaissance Scan – Gathers open ports, services, banners, and basic network footprint.

- Vulnerability Scan – Uses tools like nikto, nmap, etc. to check for known vulnerabilities.

- Web Scan – Focused scanning of web applications for common issues like misconfigurations, exposed endpoints, etc.

- Full Scan – A combined workflow that performs all supported scans.


### ⚙️ Key Features:
- Entire workflow — from planning, deciding tools, handling basic errors, to analyzing results and suggesting the next step — is managed by AI agents.

- Designed to ease your job by eliminating the need to search through each scan output manually or rely on Google for interpretation.

- Works entirely within Kali Linux, focused on ethical analysis and intelligent automation.
