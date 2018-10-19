#!/usr/bin/env bash
#################################################################################
# Title:         Cloudbox: Cloudbox Vault Restore Script                        #
# Author(s):     l3uddz                                                         #
# URL:           https://github.com/Cloudbox/Cloudbox                           #
# Description:   Restores encrypted config files from Cloudbox Vault Service.   #
# --                                                                            #
#             Part of the Cloudbox project: https://cloudbox.works              #
#################################################################################
#                     GNU General Public License v3.0                           #
#################################################################################
# Usage:                                                                        #
# ======                                                                        #
# curl -s https://cloudbox.works/vault.sh | bash -s 'USER' 'PASS' 'PATH'        #
# wget -qO- https://cloudbox.works/vault.sh | bash -s 'USER' 'PASS' 'PATH'      #
#################################################################################

# vars
files=( "ansible.cfg" "accounts.yml" "settings.yml" "adv_settings.yml" "backup_config.yml" "rclone.conf" )
vault="vault.cloudbox.works"
folder="/tmp/vault"
green="\e[1;32m"
red="\e[1;31m"
nc="\e[0m"
done="[ ${green}DONE${nc} ]"
fail="[ ${red}FAIL${nc} ]"

# inputs
USER=$1
PASS=$2
DIR=${3:-$HOME/cloudbox}

# validate inputs
if [ -z "$USER" ] || [ -z "$PASS" ]
then
      echo "You must provide the user & pass as arguments"
      exit 1
fi

# validate folders exist
TMP_FOLDER_RESULT=$(mkdir -p $folder)
if [ ! -z "$TMP_FOLDER_RESULT" ]
then
    echo "Failed to ensure $folder was created..."
    exit 1
fi

RESTORE_FOLDER_RESULT=$(mkdir -p $DIR)
if [ ! -z "$RESTORE_FOLDER_RESULT" ]
then
    echo "Failed to ensure $DIR was created..."
    exit 1
fi

# SHA1 username
USER_HASH=$(echo -n $USER | openssl dgst -sha1 | sed 's/^.*= //')
echo "User Hash: $USER_HASH"
echo ''

# Fetch files
echo "Fetching files from $vault..."
echo ''
for file in "${files[@]}"
do
        :
        # wget file
        printf '%-20.20s' "$file"
        wget -qO $folder/$file.enc http://$vault/load/$USER_HASH/$file
        file_header=$(head -c 10 $folder/$file.enc)
        # is the file encrypted?
        if [[ $file_header == Salted* ]]
        then
                echo -e $done
        else
                echo -e $fail
                exit 1
        fi
done

echo ''

# Decrypt files
echo 'Decrypting fetched files...'
echo ''
for file in "${files[@]}"
do
        :
        # wget file
        printf '%-20.20s' "$file"
        DECRYPT_RESULT=$(openssl enc -aes-256-cbc -d -salt -in $folder/$file.enc -out $folder/$file -k $PASS 2>&1)
        # was the file decryption successful?
        if [ -z "$DECRYPT_RESULT" ]
        then
                echo -e $done
        else
                echo -e $fail
                exit 1
        fi
done

echo ''

# Move decrypted files
echo 'Moving decrypted files...'
echo ''
for file in "${files[@]}"
do
        :
        # move file
        printf '%-20.20s' "$file"
        MOVE_RESULT=$(mv $folder/$file $DIR/$file 2>&1)
        # was the decrypted file moved successfully?
        if [ -z "$MOVE_RESULT" ]
        then
                echo -e $done
        else
                echo -e $fail
                exit 1
        fi
done

echo ''

# finish
exit 0