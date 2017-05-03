project :=
version := auto

enable_services:
	gcloud service-management enable drive --project=$(project)
	gcloud service-management enable storage-api.googleapis.com --project=$(project)

run:
	CONFIG=${CONFIG:-'config/config_play.yaml'}
	EMAIL_ADDRESS=""
	KEY="$(egrep -o "^key:.*" $CONFIG | cut -d\" -f2)"

	env AIRPRESS_CONFIG="$CONFIG" \
	  dev_appserver.py \
	  --appidentity_email_address $EMAIL_ADDRESS \
	  --appidentity_private_key_path config/$KEY \
	  $@ .

deploy-flex:
	gcloud app deploy \
		--project=retail-hub \
		--version=flex \
		--no-promote \
		app.flex.yaml

deploy:
	gcloud app deploy -q \
		--project=$(project) \
		--version=$(version) \
		app.yaml
	gcloud app deploy -q \
		--project=$(project)\
		--version=$(version) \
		queue.yaml
	gcloud app deploy -q \
		--project=$(project) \
		--version=$(version) \
		index.yaml
