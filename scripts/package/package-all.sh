#!/bin/bash

set -e

echoerr() { echo "$@" 1>&2; }

function get_platform() {
    # Will return "linux" for GNU/Linux
    #   I'd just like to interject for a moment...
    #   https://wiki.installgentoo.com/index.php/Interjection
    # Will return "macos" for macOS/OS X
    # Will return "windows" for Windows/MinGW/msys

    _platform=$(uname | tr '[:upper:]' '[:lower:]')
    if [[ $_platform == "darwin" ]]; then
        _platform="macos";
    elif [[ $_platform == "msys"* ]]; then
        _platform="windows";
    elif [[ $_platform == "mingw"* ]]; then
        _platform="windows";
    elif [[ $_platform == "linux" ]]; then
        # Nothing to do
        true;
    else
        echoerr "ERROR: $_platform is not a valid platform";
        exit 1;
    fi

    echo $_platform;
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function get_version() {
    "$SCRIPT_DIR/getversion.sh";
}

function get_version_no_prefix() {
    "$SCRIPT_DIR/getversion.sh" --strip-v;
}

function get_arch() {
    _arch="$(uname -m)"
    echo $_arch;
}

platform=$(get_platform)
version=$(get_version)
version_no_prefix=$(get_version_no_prefix)
arch=$(get_arch)
# Research tags are suffixed (e.g. v0.14.0b3-research), but the edition
# belongs in its own filename token, not in the version part:
#   activitywatch[-tauri][-research]-<version>-<os>-<arch>[-setup].<ext>
version="${version%-research}"
version_no_prefix="${version_no_prefix%-research}"
build_suffix=""
if [[ $TAURI_BUILD == "true" ]]; then
    build_suffix="-tauri"
fi
if [[ $AW_RESEARCH_EDITION == "true" ]]; then
    build_suffix="${build_suffix}-research"
fi

echo "========================================"
echo "Build Version Information"
echo "========================================"
echo "Platform:       $platform"
echo "Arch:           $arch"
echo "Version (with v):  $version"
echo "Version (no v):     $version_no_prefix"
echo "Tauri build:    ${TAURI_BUILD:-false}"
echo "========================================"
echo

# For Tauri Linux builds, include helper scripts and README
if [[ $platform == "linux" && $TAURI_BUILD == "true" ]]; then
    cp scripts/package/README.txt scripts/package/move-to-aw-modules.sh dist/activitywatch/
fi

function build_zip() {
    echo "Zipping executables..."
    pushd dist;
    filename="cepem-watch${build_suffix}-${version}-${platform}-${arch}.zip"
    echo "Name of package will be: $filename"

    if [[ $platform == "windows"* ]]; then
        7z a $filename activitywatch;
    else
        zip -r $filename activitywatch;
    fi
    popd;
    echo "Zip built!"
}

function build_setup() {
    filename="cepem-watch${build_suffix}-${version}-${platform}-${arch}-setup.exe"
    echo "Name of package will be: $filename"

    # Locate the Inno Setup compiler. Inno may be installed system-wide or
    # per-user (winget), so probe several locations and finally PATH.
    iscc=""
    for cand in \
        "/c/Program Files (x86)/Inno Setup 6" \
        "/c/Program Files/Inno Setup 6" \
        "$LOCALAPPDATA/Programs/Inno Setup 6" \
        "$HOME/AppData/Local/Programs/Inno Setup 6"; do
        if [ -f "$cand/ISCC.exe" ]; then iscc="$cand/ISCC.exe"; break; fi
        if [ -f "$cand/iscc.exe" ]; then iscc="$cand/iscc.exe"; break; fi
    done
    if [ -z "$iscc" ] && command -v iscc >/dev/null 2>&1; then
        iscc="$(command -v iscc)"
    fi
    if [ -z "$iscc" ]; then
        echo "ERROR: Couldn't find Inno Setup (ISCC.exe) which is needed to build the installer. Install it (e.g. 'winget install JRSoftware.InnoSetup'). Exiting."
        exit 1
    fi

    if [[ $TAURI_BUILD == "true" ]]; then
        env AW_VERSION=$version_no_prefix "$iscc" scripts/package/aw-tauri.iss
    else
        env AW_VERSION=$version_no_prefix "$iscc" scripts/package/activitywatch-setup.iss
    fi
    mv dist/cepem-watch-setup.exe dist/$filename
    echo "Setup built!"
}

build_zip
if [[ $platform == "windows"* ]]; then
    build_setup
fi

echo
echo "-------------------------------------"
echo "Contents of ./dist"
ls -l dist
echo "-------------------------------------"

