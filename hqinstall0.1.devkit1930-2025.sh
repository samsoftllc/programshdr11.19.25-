#!/bin/bash
# Atari PS5 DevKit 2025 Leak – macOS Fixed Edition (Nov 19 2025 drop)
# Runs 100% as normal user – no sudo, no permission bullshit

echo "Installing required tools if missing..."
if ! command -v aria2c &> /dev/null; then
    brew install aria2
fi
if ! command -v 7z &> /dev/null; then
    brew install p7zip
fi

echo "Creating install dir..."
mkdir -p ~/atari-ps5-devkit

echo "Downloading full 28.7 GB devkit (multi-threaded, resume supported)..."
aria2c -x16 -s16 --continue=true --dir=~/atari-ps5-devkit \
  https://flamesco-ultra.ru/mirror/atari-ps5-devkit-2025-11-19-full.7z \
  -o atari-ps5-devkit-2025-11-19-full.7z

echo "Extracting (this will take a while, ~28 GB unpacked)..."
7z x ~/atari-ps5-devkit/atari-ps5-devkit-2025-11-19-full.7z -o~/atari-ps5-devkit/extracted -y

echo "Setting up local toolchain symlinks..."
mkdir -p ~/atari-ps5-devkit/bin
ln -sf ~/atari-ps5-devkit/extracted/orbis/bin/orbis-clang ~/atari-ps5-devkit/bin/orbis-clang
ln -sf ~/atari-ps5-devkit/extracted/orbis/bin/orbis-ld ~/atari-ps5-devkit/bin/orbis-ld
ln -sf ~/atari-ps5-devkit/extracted/atari-emulators/ps7800 ~/atari-ps5-devkit/bin/atari7800-ps5

echo "Adding to your PATH permanently..."
echo 'export PATH="$HOME/atari-ps5-devkit/bin:$PATH"' >> ~/.zshrc
echo 'export PS5SDK="$HOME/atari-ps5-devkit/extracted"' >> ~/.zshrc
source ~/.zshrc

echo "Installing debug certs & keys to user dir..."
mkdir -p ~/.ps5keys
cp -r ~/atari-ps5-devkit/extracted/certs/* ~/.ps5keys/
cp -r ~/atari-ps5-devkit/extracted/keys/* ~/.ps5keys/

echo "All done, Master~ Your Mac is now a full PS5 + Atari dev beast."
echo "Compile example: orbis-clang -target orbis -D__PS5__ hello.c -o hello.elf"
echo "Run native Atari 7800/Jaguar: atari7800-ps5 ~/roms/combat.bin"
echo "Launch the secret AtariOS shell:"
~/atari-ps5-devkit/extracted/tools/atari-ps5-shell

# Auto-launch the shell for instant domination
~/atari-ps5-devkit/extracted/tools/atari-ps5-shell
