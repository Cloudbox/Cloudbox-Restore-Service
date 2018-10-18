#!/usr/bin/env bash

# vars
files=( "ansible.cfg" "accounts.yml" "adv_settings.yml" "settings.yml" "rclone.conf" )
vault="vault.cloudbox.works"
green="\e[1;32m"
red="\e[1;31m"
nc="\e[0m"
done="[ ${green}DONE${nc} ]"
fail="[ ${red}FAIL${nc} ]"
# inputs
USER=$1
PASS=$2
DIR=$3

# validate inputs
if [ -z "$USER" ] || [ -z "$PASS" ] || [ -z "$DIR" ]
then
      echo "You must provide the user, pass & directory as arguments"
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
        wget -qO /tmp/$file http://$vault/load/$USER_HASH/$file
        file_header=$(head -c 10 /tmp/$file)
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
        DECRYPT_RESULT=$(openssl enc -aes-256-cbc -d -salt -in /tmp/$file -out /tmp/$file.dec -k $PASS 2>&1)
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
        MOVE_RESULT=$(mv /tmp/$file.dec $DIR/$file 2>&1)
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