#!/bin/bash

set -e  # Exit on any error

# Absolute path of this repo
PROJECT_PATH="$(cd "$(dirname "$0")" && pwd)"

# Check for .venv
if [ ! -d "$PROJECT_PATH/.venv" ]; then
    echo -e "[❌] '.venv' not found in $PROJECT_PATH"
    echo "👉 Please run:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Create system-wide launcher
echo "[📦] Installing 'pentagent' launcher to /usr/local/bin..."

sudo tee /usr/local/bin/pentagent > /dev/null <<EOF
#!/bin/bash
PROJECT_DIR="$PROJECT_PATH"
source "\$PROJECT_DIR/.venv/bin/activate"
cd "\$PROJECT_DIR"
python3 -m frontend.main_ui
EOF

sudo chmod +x /usr/local/bin/pentagent

echo -e "[✅] Installed successfully!"
echo -e "👉 Run it from anywhere using: \e[1mpentagent\e[0m"



