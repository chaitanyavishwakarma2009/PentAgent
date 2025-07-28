# 🛡️ PentAgent - AI-Powered VAPT Agent

**PentAgent** is an interactive, AI-powered agent framework for **Vulnerability Assessment and Penetration Testing (VAPT)**.  
Built using **LangGraph** and **NiceGUI**, it orchestrates intelligent agents and a sleek web UI to help automate reconnaissance, analysis, and exploitation — all with real-time feedback.

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
