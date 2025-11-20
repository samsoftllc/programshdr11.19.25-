#!/bin/bash
# [C] Samsoft LLC × Catsan LLC – FLAMESCO SDK HDR (PS2-FREE EDITION)
# Ultra-clean, M4 Pro optimized, no PS2 toolchain anywhere.

set -e

# --- Paths ---
export TOOLCHAIN_DIR="$HOME/eternal-toolchains"
export BIN_DIR="$TOOLCHAIN_DIR/bin"

mkdir -p "$TOOLCHAIN_DIR" "$BIN_DIR"

echo "=========================================================================="
echo " FLAMESCO SDK HDR – PS2-FREE FINAL BUILD"
echo " Destination: $TOOLCHAIN_DIR"
echo "=========================================================================="

# -------------------------------------------------------------
# Helper: tool check
# -------------------------------------------------------------
check_tool() {
    if eval "$1" &>/dev/null; then
        echo "✅ $2 OK"
    else
        echo "❌ $2 FAILED"
    fi
}

# -------------------------------------------------------------
# 1. Homebrew Dependencies
# -------------------------------------------------------------
echo "--- Installing Homebrew Dependencies ---"

brew install wget curl unzip zstd xz cmake ninja texinfo gawk gnu-sed coreutils \
    bison flex nasm yasm cc65 mame || true

# Link important brew tools into our private bin path
ln -sf "$(brew --prefix nasm)/bin/nasm" "$BIN_DIR/" 2>/dev/null || true
ln -sf "$(brew --prefix yasm)/bin/yasm" "$BIN_DIR/" 2>/dev/null || true
ln -sf "$(brew --prefix cc65)/bin"/* "$BIN_DIR/" 2>/dev/null || true
ln -sf "$(brew --prefix mame)/bin"/* "$BIN_DIR/" 2>/dev/null || true

echo "Homebrew deps installed."

# -------------------------------------------------------------
# 2. VitaSDK (PS Vita)
# -------------------------------------------------------------
echo "--- Installing VitaSDK ---"

TEMP="/tmp/vitasdk.tar.bz2"

# Correct download – follow redirects fully
curl -L --fail --silent --show-error \
    https://github.com/vitasdk/autobuilds/releases/latest/download/vitasdk-macos.tar.bz2 \
    -o "$TEMP"

# Extract only if file is valid
if file "$TEMP" | grep -q "bzip2 compressed"; then
    tar xf "$TEMP" -C "$TOOLCHAIN_DIR/"
    find "$TOOLCHAIN_DIR/vitasdk/bin" -type f -exec ln -sf {} "$BIN_DIR/" \; 2>/dev/null || true
    echo "VitaSDK installed."
else
    echo "❌ VitaSDK download failed (GitHub throttled or offline)."
fi

rm -f "$TEMP"

# -------------------------------------------------------------
# 3. OpenOrbis (PS4/PS5)
# -------------------------------------------------------------
echo "--- Installing OpenOrbis (PS4/PS5) ---"

OO="/tmp/oo.zip"
curl -L --fail --silent --show-error \
    https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain/releases/latest/download/OpenOrbis-PS4-Toolchain-master.zip \
    -o "$OO"

unzip -q "$OO" -d /tmp/ || true
rm "$OO"

if [ -d "/tmp/OpenOrbis-PS4-Toolchain-master" ]; then
    find "/tmp/OpenOrbis-PS4-Toolchain-master/bin/macos" -type f \
        -exec ln -sf {} "$BIN_DIR/" \; 2>/dev/null || true
    echo "OpenOrbis installed."
else
    echo "❌ OpenOrbis unavailable."
fi

rm -rf "/tmp/OpenOrbis-PS4-Toolchain-master"

# -------------------------------------------------------------
# 4. z88dk (Z80)
# -------------------------------------------------------------
echo "--- Installing z88dk (Z80) ---"

Z80="/tmp/z88dk.zip"

curl -L --fail --silent --show-error \
    http://nightly.z88dk.org/z88dk-macos-latest.zip \
    -o "$Z80"

unzip -q "$Z80" -d "$TOOLCHAIN_DIR/" || true
rm "$Z80"

if [ -d "$TOOLCHAIN_DIR/z88dk/bin" ]; then
    find "$TOOLCHAIN_DIR/z88dk/bin" -type f -exec ln -sf {} "$BIN_DIR/" \; 2>/dev/null || true
    echo "z88dk installed."
else
    echo "❌ z88dk download failed."
fi

# -------------------------------------------------------------
# 5. devkitPro (Switch/Wii/GameCube/3DS/GBA/DS)
# -------------------------------------------------------------
echo "--- DevkitPro Installer Downloaded (Manual Install Needed) ---"

DKP="$TOOLCHAIN_DIR/devkitpro-installer.pkg"

curl -L --fail --silent --show-error \
    https://github.com/devkitPro/installer/releases/latest/download/devkitpro-installer.pkg \
    -o "$DKP"

echo "Open the installer manually now:"
echo "  open $DKP"
echo "Install to: /opt/devkitpro"
echo "(Installer must be run by user — unsigned pkg.)"

# -------------------------------------------------------------
# 6. PATH Export
# -------------------------------------------------------------
if ! grep -q "eternal-toolchains/bin" ~/.zshrc; then
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> ~/.zshrc
fi

export PATH="$BIN_DIR:$PATH"

# -------------------------------------------------------------
# 7. Verification (PS2 Gone)
# -------------------------------------------------------------
echo "--- Verifying Installed Compilers (PS2 removed) ---"

check_tool "nasm -v" "nasm -v"
check_tool "yasm --version" "yasm --version"
check_tool "ca65 --version" "ca65 --version"
check_tool "z80asm help" "z80asm -h"
check_tool "OpenOrbis clang" "orbis-clang --version"
check_tool "arm-none-eabi-gcc (if devkitPro installed)" "arm-none-eabi-gcc --version"

echo "=========================================================================="
echo "🔥 FLAMESCO SDK HDR COMPLETE – PS2 REMOVED CLEANLY 🔥"
echo "=========================================================================="
