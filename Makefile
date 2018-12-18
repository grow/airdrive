project :=
organization :=
version := auto

setup:
	# gcloud projects create $(project)
	# gcloud app create --project=$(project)
	$(MAKE) enable-services
	$(MAKE) deploy
	$(MAKE) deploy-yaml
	$(MAKE) deploy-queue

enable-services:
	gcloud services enable drive --project=$(project)
	gcloud services enable storage-api.googleapis.com --project=$(project)

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

deploy-yaml:
	gcloud app deploy -q \
		--project=$(project)\
		queue.yaml
	gcloud app deploy -q \
		--project=$(project) \
		index.yaml

deploy:
	gcloud app deploy -q \
		--project=$(project) \
		--version=$(version) \
		--promote \
		app.yaml

stage:
	gcloud app deploy -q \
		--project=$(project) \
		--version=$(version) \
		--no-promote \
		app.yaml

deploy-retail:
	gcloud app deploy -q \
		--project=$(project) \
		--version=$(version) \
		--promote \
		retail.yaml

stage-retail:
	gcloud app deploy -q \
		--project=$(project) \
		--version=$(version) \
		--no-promote \
		retail.yaml

deploy-queue:
	gcloud app deploy \
	  -q \
	  --project=$(project) \
	  queue.yaml
