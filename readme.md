# Project To-Do List
- [ ] Store the user conversation history in a database (e.g., Firestore, PostgreSQL). Viewaable only be authenticated users.
- [x] Implement user authentication and authorization for accessing conversation history
- [x] Create a metrics dashboard to show usage statistics
- [x] Store the terraform state in a remote backend (e.g., GCS bucket, Terraform Cloud)
- [x] Deploy the function into GCP function using terraform or github actions
- [x] How do I ensure that only the telegram can call my GCP webhook endpoint?

# Storing the terraform state in a remote backend
To store the terraform state in a remote backend, you can use a Google Cloud Storage (GCS) bucket. Below are the steps to create a GCS bucket and configure Terraform to use it as a backend.
## Prerequisites (Create a Google Cloud Storage Bucket)
gcloud config set project $PROJECT_ID
gcloud storage buckets create gs://$BUCKET_NAME --project=vernacular-voice-bot --location=$REGION --uniform-bucket-level-access
gcloud storage buckets create gs://vernacular-voice-bot-tf-state --project=vernacular-voice-bot --location=asia-south1 --uniform-bucket-level-access

# Configure Telegram Webhook
Configure Telegram to call the webhook endpoint of the deployed function by invoking the following command on Powershell
Invoke-WebRequest -Uri "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=<URL>&secret_token=<WEBHOOK_SECRET>" -Method POST

Invoke-WebRequest -Uri "https://api.telegram.org/bot8361306450:AAH2kZszlG5OS6_m6UV9uWDAduYLsa1V6Uo/setWebhook?url=https://vernacular-chatbot-function-ykz3pfxpsq-el.a.run.app&secret_token=KbXMaH6bEEQPXOis3oUX" -Method POST