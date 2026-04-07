#!/bin/bash
set -e

APPNAME="W-Engine Pro"
APPVERSION="1.0.0"
OUTPUT_DIR="$(pwd)/dist"
APPDIR="$(pwd)/packaging/AppDir"
PYINSTALLER_OUT="$(pwd)/dist/pyinstaller"

clean() {
    echo "=== Cleaning previous build ==="
    rm -rf "$OUTPUT_DIR"/*
    rm -rf "$APPDIR/usr/"*
    rm -rf "$APPDIR/.DirIcon"
    echo "Clean complete."
}

if [ "$1" = "clean" ]; then
    clean
    exit 0
fi

if [ "$1" = "rebuild" ]; then
    clean
fi

echo "=== $APPNAME Packaging Script ==="
echo "Version: $APPVERSION"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/wengine"

echo "=== Step 1: Build Python with PyInstaller ==="

pyinstaller packaging/wengine.spec --distpath "$PYINSTALLER_OUT" --workpath "$OUTPUT_DIR/build" -y

echo "=== Step 2: Copy Python binaries to AppDir ==="
cp -r "$PYINSTALLER_OUT/"* "$APPDIR/usr/"

echo "=== Step 3: Copy source code to AppDir ==="
cp -r core data engines render threads ui styles main.py "$APPDIR/usr/share/wengine/"

echo "=== Step 4: Bundle mpv, mpvpaper, yt-dlp ==="

copy_binary_with_deps() {
    local bin="$1"
    local dest="$2"
    local bin_path=$(which "$bin" 2>/dev/null)
    
    if [ -z "$bin_path" ]; then
        echo "Warning: $bin not found in system"
        return 1
    fi
    
    echo "Bundling $bin..."
    cp "$bin_path" "$dest/"
    
    # Copy shared libraries
    for lib in $(ldd "$bin_path" | grep "=>" | awk '{print $3}' | sort -u); do
        if [ -f "$lib" ]; then
            cp -n "$lib" "$APPDIR/usr/lib/" 2>/dev/null || true
        fi
    done
    
    # Copy also the main libs from ldd output (not just => deps)
    for lib in $(ldd "$bin_path" | awk '{print $1}' | sort -u); do
        if [[ "$lib" != "linux-vdso.so"* ]] && [[ "$lib" != "linux-gate.so"* ]]; then
            if [ -f "/lib/$lib" ]; then
                cp -n "/lib/$lib" "$APPDIR/usr/lib/" 2>/dev/null || true
            fi
            if [ -f "/lib64/$lib" ]; then
                cp -n "/lib64/$lib" "$APPDIR/usr/lib/" 2>/dev/null || true
            fi
        fi
    done
}

copy_binary_with_deps mpv "$APPDIR/usr/bin"
copy_binary_with_deps mpvpaper "$APPDIR/usr/bin"
copy_binary_with_deps yt-dlp "$APPDIR/usr/bin"

echo "=== Step 5: Create Python symlinks ==="
# Ensure python3 points to the bundled python
PYTHON_BASE=$(ls -d "$APPDIR"/usr/lib/python3.* 2>/dev/null | head -1)
if [ -n "$PYTHON_BASE" ]; then
    ln -sf "$PYTHON_BASE" "$APPDIR/usr/lib/python3"
fi

echo "=== Step 6: Copy desktop files and icons ==="
cp packaging/wengine.desktop "$APPDIR/usr/share/applications/"
cp -n data/W-Enginepro.svg "$APPDIR/usr/share/icons/hicolor/scalable/apps/" 2>/dev/null || true

echo "=== Step 7: Create AppRun ==="
cat > "$APPDIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"

export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/usr/lib/x86_64-linux-gnu:$HERE/usr/wengine/_internal:$LD_LIBRARY_PATH"

for dir in "$HERE/usr/lib"/python3.*; do
    if [ -d "$dir" ]; then
        export PYTHONHOME="$HERE/usr"
        export PYTHONPATH="$HERE/usr/share/wengine:$dir/site-packages"
        break
    fi
done

for dir in "$HERE/usr/wengine/_internal"; do
    if [ -d "$dir" ]; then
        export PYTHONPATH="$dir:$PYTHONPATH"
        break
    fi
done

for dir in "$HERE/usr/lib"/PySide6/Qt; do
    if [ -d "$dir" ]; then
        export QT_PLUGIN_PATH="$dir/plugins:$QT_PLUGIN_PATH"
        export QT_QPA_PLATFORM_PLUGIN_PATH="$dir/plugins/platforms:$QT_QPA_PLATFORM_PLUGIN_PATH"
        export QML2_IMPORT_PATH="$dir/qml:$QML2_IMPORT_PATH"
        break
    fi
done

export PATH="$HERE/usr/bin:$PATH"

if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    export QT_QPA_PLATFORM="wayland;xcb"
else
    export QT_QPA_PLATFORM="xcb"
fi

exec "$HERE/usr/wengine/wengine.bin" "$@"
APPRUN_EOF

chmod +x "$APPDIR/AppRun"

echo "=== Step 8: Create launcher symlink ==="
cp "$PYINSTALLER_OUT/wengine/wengine" "$APPDIR/usr/wengine/wengine.bin"
ln -sf "../AppRun" "$APPDIR/usr/bin/wengine"

LINUXDEPLOY="$(pwd)/packaging/linuxdeploy"
APPIMAGETOOL="$(pwd)/packaging/appimagetool"

echo "=== Step 9: Build AppImage ==="
if [ -x "$APPIMAGETOOL" ]; then
    cd "$OUTPUT_DIR"
    "$APPIMAGETOOL" "$APPDIR" "W-Engine-Pro-$APPVERSION-x86_64.AppImage"
    echo "AppImage created: $OUTPUT_DIR/W-Engine-Pro-$APPVERSION-x86_64.AppImage"
elif [ -x "$LINUXDEPLOY" ]; then
    cd "$OUTPUT_DIR"
    set +e
    "$LINUXDEPLOY" --appdir="$APPDIR" --output=appimage \
        -i "$APPDIR/usr/share/icons/hicolor/scalable/apps/wengine.svg" \
        -d "$APPDIR/usr/share/applications/wengine.desktop" 2>&1
    set -e
    if [ -f "$OUTPUT_DIR/W-Engine-Pro-$APPVERSION-x86_64.AppImage" ]; then
        echo "AppImage created: $OUTPUT_DIR/W-Engine-Pro-$APPVERSION-x86_64.AppImage"
    else
        echo "AppImage not created. Checking for alternative..."
        ls -la "$OUTPUT_DIR"/*.AppImage 2>/dev/null || echo "No AppImage found"
    fi
else
    echo "Warning: No packaging tool found. AppImage not created."
fi

echo "=== Packaging Complete ==="
echo "AppDir: $APPDIR"
echo "Output: $OUTPUT_DIR"