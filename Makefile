#CONFIG := "config/config_play.yaml" 
#EMAIL_ADDRESS := $(shell egrep -o "^service_account:.*" $CONFIG | cut -d\" -f2)
#KEY =  

run:
      CONFIG=${CONFIG:-'config/config_play.yaml'}
      EMAIL_ADDRESS=""
      KEY="$(egrep -o "^key:.*" $CONFIG | cut -d\" -f2)"

      env AIRPRESS_CONFIG="$CONFIG" \
	dev_appserver.py \
	--appidentity_email_address $EMAIL_ADDRESS \
	--appidentity_private_key_path config/$KEY \
	$@ .

