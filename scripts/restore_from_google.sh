#!/usr/bin/env bash

if ! /usr/bin/screen -list | /bin/grep -q "restore"; then
        /bin/rm -rfv /root/restore.log
        /usr/bin/screen -dmS restore /usr/bin/rclone sync google: /opt/cloudbox_restore_service --config=/root/.config/rclone/rclone.conf --verbose=1 --transfers=8 --stats=60s --checkers=16 --drive-chunk-size=128M --fast-list --log-file=/root/restore.log
fi