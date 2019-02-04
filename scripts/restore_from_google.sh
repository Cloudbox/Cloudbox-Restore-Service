#!/usr/bin/env bash
#########################################################################
# Title:         Cloudbox Restore Service: Restore Backup From GDrive   #
# Author(s):     l3uddz, desimaniac                                     #
# URL:           https://github.com/cloudbox/cloudbox                   #
# Description:   Restore backup from Google Drive.                      #
# --                                                                    #
#         Part of the Cloudbox project: https://cloudbox.works          #
#########################################################################
#                   GNU General Public License v3.0                     #
#########################################################################

if ! /usr/bin/screen -list | /bin/grep -q "restore"; then
  
  /bin/rm -rfv /root/restore.log
  
  /usr/bin/screen -dmS restore \
    /usr/bin/rclone sync \
      --config=/root/.config/rclone/rclone.conf \
      --verbose=1 \
      --transfers=8 \
      --stats=60s \
      --checkers=16 \
      --drive-chunk-size=128M \
      --fast-list \
      --log-file=/root/restore.log \
      google: /opt/cloudbox_restore_service

fi