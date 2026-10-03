#!/bin/bash
# Installs what the DOE needs on Ubuntu 22.04 (jammy): OpenFOAM v2412, python3-numpy, rsync, flock.
# Skips OpenFOAM if v2412 is already installed. Run with sudo (or as root).
set -e
export DEBIAN_FRONTEND=noninteractive
HERE=$(cd "$(dirname "$0")/.." && pwd)
apt-get update -qq
apt-get install -y -qq python3 python3-numpy rsync util-linux curl ca-certificates >/dev/null
if [ -f /usr/lib/openfoam/openfoam2412/etc/bashrc ]; then
    echo "OpenFOAM v2412 already installed"
else
    # 1) official OpenCFD repository; 2) fall back to the bundled jammy .deb files
    if curl -s https://dl.openfoam.com/add-debian-repo.sh | bash && apt-get update -qq && apt-get install -y -qq openfoam2412-default; then
        echo "installed from dl.openfoam.com"
    else
        echo "repository install failed; using bundled packages in $HERE/debs (Ubuntu 22.04 only)"
        apt-get install -y -qq $HERE/debs/openfoam-selector_*.deb $HERE/debs/openfoam2412-common_*.deb \
            $HERE/debs/openfoam2412_*.deb $HERE/debs/openfoam2412-tools_*.deb
    fi
fi
source /usr/lib/openfoam/openfoam2412/etc/bashrc && command -v simpleFoam snappyHexMesh foamDictionary reconstructParMesh mpirun && python3 -c "import numpy" && echo INSTALL_OK
