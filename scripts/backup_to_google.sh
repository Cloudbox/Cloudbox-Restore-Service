#!/usr/bin/env bash

if ! /usr/bin/screen -list | /bin/grep -q "backup"; then
        #/bin/rm -rfv /root/backup.log
        /usr/bin/screen -dmS backup /usr/bin/rclone copy /opt/cloudbox_restore_service google: --config=/root/.config/rclone/rclone.conf --verbose=1 --transfers=8 --stats=60s --checkers=16 --drive-chunk-size=128M --fast-list --exclude='**.log' --log-file=/root/backup.log
fi