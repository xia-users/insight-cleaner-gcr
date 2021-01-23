SHELL:=/bin/bash

.PHONY: help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

config: ## Setting deploy configuration
	@TMP_PROJECT=$(shell gcloud config list --format 'value(core.project)'); \
	read -e -p "Enter Your Project Name: " -i $${TMP_PROJECT} PROJECT_ID; \
	gcloud config set project $${PROJECT_ID}; \
	read -e -p "Enter Desired Cloud Run Region: " -i 'europe-west1' CLOUD_RUN_REGION; \
	gcloud config set run/region $${CLOUD_RUN_REGION}; \
	read -e -p "Enter Desired Cloud Run Platform: " -i 'managed' CLOUD_RUN_PLATFORM; \
	gcloud config set run/platform $${CLOUD_RUN_PLATFORM};

init-users:
	SERVICE_ACC=; \
	gcloud iam service-accounts create $${SERVICE_ACC} \
		--display-name "Cloud Run Insight Cleaner"; \
	gcloud projects add-iam-policy-binding $${PROJECT_ID} \
		--member=serviceAccount:$${SERVICE_ACC}@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/pubsub.publisher; \
	gcloud projects add-iam-policy-binding $${PROJECT_ID} \
		--member=serviceAccount:$${SERVICE_ACC}@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/datastore.user; \
	gcloud projects add-iam-policy-binding $${PROJECT_ID} \
		--member=serviceAccount:$${SERVICE_ACC}@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/storage.objectAdmin; \
	gcloud projects add-iam-policy-binding $${PROJECT_ID} \
		--member=serviceAccount:$${SERVICE_ACC}@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/logging.logWriter;

build-cleaner:
	SERVICE_NAME=; \
	@PROJECT_ID=$(shell gcloud config list --format 'value(core.project)'); \
	cd cleaner; \
	gcloud builds submit --tag gcr.io/$${PROJECT_ID}/$${SERVICE_NAME};

deploy-cleaner:
	SERVICE_ACC=; \
	SERVICE_NAME=; \
	@PROJECT_ID=$(shell gcloud config list --format 'value(core.project)'); \
	CLOUD_RUN_REGION=$(shell gcloud config list --format 'value(run.region)'); \
	CLOUD_RUN_PLATFORM=$(shell gcloud config list --format 'value(run.platform)'); \
	gcloud run deploy insight-cleaner \
		--image gcr.io/$${PROJECT_ID}/$${SERVICE_NAME} \
    	--service-account $${SERVICE_ACC}@$${PROJECT_ID}.iam.gserviceaccount.com \
		--region $${CLOUD_RUN_REGION} \
		--platform $${CLOUD_RUN_PLATFORM} \
		--no-allow-unauthenticated; \
	gcloud run services add-iam-policy-binding $${SERVICE_NAME} \
		--member=serviceAccount:cloud-run-pubsub-invoker@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/run.invoker \
		--region $${CLOUD_RUN_REGION} \
		--platform $${CLOUD_RUN_PLATFORM};