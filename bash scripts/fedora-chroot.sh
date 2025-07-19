#!/bin/sh

# Create necessary directories
mkdir -p /mnt/fedora /mnt/fedora/boot /mnt/fedora/boot/efi /mnt/fedora/dev /mnt/fedora/proc /mnt/fedora/sys /mnt/fedora/run

# Mount the consolidated partition (assuming it's Btrfs)
mount /dev/nvme0n1p8 /mnt/fedora/ -t btrfs

# Mount the EFI partition
mount /dev/nvme0n1p7 /mnt/fedora/boot/efi/

# Bind mount necessary filesystems
mount --bind /dev/ /mnt/fedora/dev
mount -t proc /proc /mnt/fedora/proc/
mount -t sysfs /sys /mnt/fedora/sys/
mount -t tmpfs tmpfs /mnt/fedora/run/

# Chroot into the Fedora environment
chroot /mnt/fedora /bin/bash

