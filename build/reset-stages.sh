#!/bin/sh
# Linux-C.O.S -- tell live-build to redo only what depends on the project's
# config after you changed package lists, hooks or includes, while KEEPING the
# 40+ GB chroot that is already installed in the cos-workspace volume.
#
#   ./reset-stages.sh && COS_PROFILE=full COS_BUILDER_PLATFORM=linux/amd64 ./build.sh
#
# What it removes: the stage markers for package installation, includes, hooks
# and the whole binary phase (plus its generated output).
# What it NEVER removes: .build/bootstrap and .build/config. Deleting those makes
# live-build re-run debootstrap from scratch and discard the installed chroot
# (a multi-hour mistake this project has made once already).
set -e
docker volume inspect cos-workspace >/dev/null 2>&1 || { echo "no cos-workspace volume -- nothing to reset"; exit 0; }
docker run --rm ${COS_BUILDER_PLATFORM:+--platform "$COS_BUILDER_PLATFORM"} -v cos-workspace:/build cos-builder sh -c '
  cd /build
  if [ -d .build ]; then
    cd .build
    rm -f chroot_package-lists.* chroot_install-packages.* chroot_includes_* chroot_hooks \
          chroot_preseed chroot_firmware binary_*
    cd ..
  fi
  # a failed or old binary phase must start clean: binary_rootfs renames parts of the chroot
  rm -rf binary binary.modified_timestamps live-image-* chroot.packages.* chroot.files
  echo "kept:    $(ls .build 2>/dev/null | tr "\n" " ")"
'
