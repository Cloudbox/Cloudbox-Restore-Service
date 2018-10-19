#!/usr/bin/env bash
#  0,4,8,12,16,20 * * * /opt/cloudbox_restore_service/scripts/backup_to_google.sh

if ! /usr/bin/screen -list | /bin/grep -q "backup"; then
        #/bin/rm -rfv /root/backup.log
        /usr/bin/screen -dmS backup bash -c 'cd /opt/cloudbox_restore_service; /usr/bin/zip -qr /root/latest_backup.zip * -x *.log* -x *.pyc* -x *__pycache__*; LAST_BACKUP_TIME="$(/usr/bin/rclone lsl google:/latest_backup.zip | sed -e '"'"'s/^[ \t]*//'"'"' | cut -d '"'"' '"'"' -f 2,3 | cut -d '"'"'.'"'"' -f 1 | sed s/'"'"' '"'"'/_/g | sed s/'"'"':'"'"'/./g)"; /usr/bin/rclone moveto google:latest_backup.zip "google:/archives/$LAST_BACKUP_TIME.zip" --config=/root/.config/rclone/rclone.conf --verbose=1 --transfers=8 --stats=60s --checkers=16 --drive-chunk-size=128M --fast-list --log-file=/root/backup.log; /usr/bin/rclone move /root/latest_backup.zip google: --config=/root/.config/rclone/rclone.conf --verbose=1 --transfers=8 --stats=60s --checkers=16 --drive-chunk-size=128M --fast-list --exclude="**.log" --exclude="**.pyc" --exclude="**__pycache__**" --exclude="**.git**" --log-file=/root/backup.log'
fi
