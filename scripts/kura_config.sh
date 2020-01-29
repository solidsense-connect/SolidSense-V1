#!/bin/bash
# 
#  generate Kura custom configuration
#  run as sudo
#
mount /dev/sda1 /mnt/usb1

if [[ ! -f /mnt/usb1/kura_config ]] ; then
    umount /mnt/usb1
    exit
fi

systemctl stop kura
#
cd /opt/SolidSense/kura/config
python gen_kura_properties.py

systemctl start kura
umount /mnt/usb1
