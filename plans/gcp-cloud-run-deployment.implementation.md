<!-- ffdc7b26-9072-4a35-b7aa-a984ac0fced7 925c6765-74ab-4bec-b099-407249f09b0d -->
# Deploy Jaltol API to GCP Cloud Run
See docs/GCP_CONFIG_CHOICE.md for reason for choosing Cloud Run instead of GCP Compute Engine/AWS EC2

## Phase 1: GCP Project Setup
- Used existing GCP project with billing enabled - `gcp-welllabs`
- gcloud CLI was already installed locally(v430), updated it to v544
- `gcloud auth list` showed that personal gmail was the default email for the CLI
- Changed application default credentials (ADC) to welllabs jaltol email ID. 
  ```bash
  gcloud auth login --update-adc  OR
  gcloud config set account company-email@gmail.com
  ```
- used `gcloud config set project gcp-welllabs` to set default project
- Aligned application default credentials to the correct project for billing/quotas.
  ```bash
  gcloud auth application-default set-quota-project gcp-welllabs OR
  gcloud auth application-default login
  ```
- `gcloud config list` showed default project and email.
- Enabled required APIs: Cloud Run, Cloud SQL, Cloud Build, Secret Manager, Cloud Storage with `gcloud services enable run.googleapis.com sqladmin.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com storage.googleapis.com artifactregistry.googleapis.com iamcredentials.googleapis.com` 

## Phase 2: Database Migration AWS > GCP

### 2.1 Cloud SQL PostgreSQL Setup
- Created Cloud SQL PostgreSQL instance (db-f1-micro for dev, db-n1-standard-1 for prod)
- Configured instance settings: region (asia-south1 recommended), automated backups, maintenance window
  ```bash
  gcloud sql instances create jaltol-postgres --database-version=POSTGRES_14 --tier=db-f1-micro --region=asia-south1 --storage-type=SSD --storage-size=20GB --backup-start-time=03:00 --maintenance-window-day=FRI --maintenance-window-hour=16`
  ```
- Checked status with `gcloud sql instances list`.
- Enabled Compute Engine API which was required for some Cloud SQL features.
- Created database
  ```bash
  gcloud sql databases create jaltol_db --instance=jaltol-postgres
  ```
- Created database users with strong password: 
  ```bash
  gcloud sql users create admindatabase --instance=jaltol-postgres --password=YOUR_STRONG_PASSWORD # same as AWS RDS db
  gcloud sql users create jaltol_admin --instance=jaltol-postgres --password=YOUR_STRONG_PASSWORD
  ```
- Configured connection security (Cloud SQL Proxy for Cloud Run)
  ```bash
  gcloud projects describe gcp-welllabs --format="value(projectNumber)"
  ```
- Granted the default Compute service account for Cloud Run the Cloud SQL Client role 
  ```bash
  gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" --role="roles/cloudsql.client"`
  ```

### 2.2 Database Export from AWS RDS | import to GCP
- Exported Jaltol API database from AWS RDS: 
  - via pgAdmin by 'Creating a backup`,  format set to Plain (SQL) and filename "jaltol_backup.sql"
- Create Cloud Storage bucket for import: 
  ```bash
  gsutil mb -l asia-south1 gs://jaltol-api-data-migration-bucket
  ```
- Uploaded dump to GCS: 
  ```bash
  gsutil cp jaltol_backup.sql gs://jaltol-api-data-migration-bucket/
  ```
- Got Cloud SQL service account email with 
  ```bash
  gcloud sql instances describe jaltol-postgres --format="value(serviceAccountEmailAddress)"
  ```
- Gave Cloud SQL service account access to bucket to move backup to Postgres
  ```bash
  gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" --role="roles/storage.objectViewer"
  ```
- Import to Cloud SQL as admin user specified by the database being imported: 
  ```bash
  gcloud sql import sql jaltol-postgres gs://jaltol-api-data-migration-bucket/jaltol_backup.sql --database=jaltol_db --user=admindatabase
  ```
- Verify data integrity with sample queries
- Optional (didn't do this): Connect from local machine using Cloud SQL Proxy to test connectivity
   - Windows: Download from https://cloud.google.com/sql/docs/mysql/sql-proxy
   - Start a local proxy on 5432 - `cloud-sql-proxy.exe gcp-welllabs:asia-south1:jaltol-postgres`
   - in pgAdmin connect with Host:127.0.0.1 or localhost, database, username and password

## Phase 3: Application Configuration

### 3.1 Update Django Settings

**File**: `JaltolAPI/my_gee_backend/settings.py`

- Added Cloud SQL connection configuration using Unix socket
- Configured Django to use GCS for static files when RUN_ENV='cloudrun' (using `django-storages`)
- Updated `ALLOWED_HOSTS` with Cloud Run URL
- Set `DEBUG=False` for production
- Configure proper CORS origins

**File**: `JaltolAPI/requirements.txt`
- Added `django-storages[google]` and installed.


### 3.2 Environment Variables & Secrets

- Created `.env.production` template (not committed, only for local use)
- Set up Secret Manager for sensitive credentials:
  - `DJANGO_SECRET_KEY` (signs sessions)
  - `DATABASE_PASSWORD`
  - `GOOGLE_OAUTH2_CLIENT_SECRET` (for google sign-in)
- **Important**: When adding secrets via command line, ensure no trailing newline characters, else use a file
  - Windows: `echo|set /p="password">dbpass.txt` (no newline) or `echo password>dbpass.txt` (adds newline - **avoid**)
  - Then add secret: `gcloud secrets versions add database-password --data-file=dbpass.txt`
- Noted version number using `gcloud secrets versions list database-password`
- The following non-sensitive settings are set as environment variables in the Cloud Run service configuration:
  - `DATABASE_NAME`
  - `DATABASE_USER`
  - `DATABASE_HOST`
  - `DATABASE_PORT`
  - `GOOGLE_OAUTH2_CLIENT_ID`
  - `GOOGLE_APPLICATION_CREDENTIALS` ()
  - `GS_BUCKET_NAME`
  - `RUN_ENV`
  - `DEBUG`
  - `ALLOWED_HOSTS`
  - Any additional configuration variables that do not contain secrets or private keys
- Sensitive values pulled from Secret Manager at runtime.
- GOOGLE_APPLICATION_CREDENTIALS points to the service account key used for GEE, later phased out and replaced by keyless approach.

### 3.3 Django static files configuration
Django serves as a backend API here, but still needs "static files"—unchanging assets like images, JavaScript, or CSS—for its admin interface and browsable API pages. Even if the frontend is separate, these static files are required by Django for admin and UI functionality.
- Created GCS bucket: `jaltol-static-files` with `gsutil mb -l asia-south1 gs://jaltol-static-files`
- Configured bucket permissions (public read for static files) with `gsutil mb -l asia-south1 gs://jaltol-static-files`
- Run `collectstatic` to upload existing static files from Django and installed packages into GCS (in .env , RUN_ENV=cloudrun). If that doesn't work then do `gsutil -m rsync -r staticfiles/ gs://jaltol-static-files/`

## Phase 4: Containerization & Cloud Run

### High-Level Concepts: Docker, Containerization, and Cloud Run

- **What is Docker?**  
  Docker is a tool that lets you package an application and everything it needs (code, libraries, system tools) into a single unit called a **container image**. This ensures the app runs the same way anywhere—on your laptop, in the cloud, or on someone else’s computer.

- **What is Containerization?**  
  Containerization is the process of putting your app and its dependencies into a **container**. Think of a container as a lightweight, isolated box. Unlike a virtual machine, it shares the computer’s OS but still keeps your app separate from others. This makes deployments reliable and repeatable.

- **What is Cloud Run?**  
  Cloud Run is a fully managed service by Google Cloud that runs your containers. You simply give Cloud Run your container image, and it handles launching it, scaling it up or down automatically (even to zero), managing resources, handling health checks, and providing a public URL.  
  - **Key terms:**  
    - *Container Image*: The "blueprint" for running your app, built with Docker.
    - *Instance*: A running copy of your container.
    - *Scaling*: Cloud Run automatically increases or decreases the number of instances based on traffic.
    - *Environment Variables*: Settings (like passwords, API keys) that are given to your app when it runs.
    - *Artifact Registry*: Google's storage for your container images, like a warehouse for your app packages.

In summary:  
You use **Docker** to containerize your Django app (make a container image). You upload that image to **Artifact Registry**. Then, **Cloud Run** runs your image on-demand, manages scaling and networking, and provides a public endpoint for your API—no servers to manage yourself.


### 4.1 Build - Update Dockerfile for Production

**File**: `JaltolAPI/Dockerfile`

Changes made in this commit:
- Changed base image to `python:3.11-slim` (fixes earthengine-api compatibility with 3.9.0 bug)
- Install system dependencies: `gcc`, `postgresql-client`
- Copy requirements first (better Docker layer caching)
- Run `collectstatic` during build
- Create non-root user for security
- Configure Gunicorn with 2 workers, 2 threads, 300s timeout
- Use PORT environment variable (Cloud Run standard)

Note: No Cloud SQL Proxy needed - Cloud Run handles connection via Unix socket

**Status:** Completed. Local build successful (~350s). Next step: Push to Artifact Registry.

### 4.2 Push - Image to Artifact Registry

**Conceptual Explanation:**
You built a Docker image on your local machine. But Cloud Run needs to access it from GCP. Artifact Registry is like a "warehouse" in the cloud where you store your Docker images. This is the standard way to store Docker images in GCP (Container Registry is being phased out).

**What each step does:**
1. **Create repository**: Like creating an empty folder in Google's warehouse where your images will live. The format is `docker` because Docker images have a specific layout.
2. **Configure Docker auth**: Tells your local Docker client how to prove it's allowed to push/pull images to GCP. It updates your Docker config file automatically.
3. **Tag image**: Docker images are identified by tags. This gives your local image a "cloud address" - like adding a shipping label with the warehouse address (`asia-south1-docker.pkg.dev/gcp-welllabs/jaltol-api/jaltol-api:latest`).
4. **Push image**: Uploads the image from your machine to Google's warehouse. This is the slow step (depends on image size and internet speed).

**Why asia-south1?** Same region as your Cloud SQL and where Cloud Run will run → lower latency.

**Commands:**
- Create Artifact Registry repository: `gcloud artifacts repositories create jaltol-api --repository-format=docker --location=asia-south1`
- Configure Docker authentication: `gcloud auth configure-docker asia-south1-docker.pkg.dev`
- Tag image for registry: `docker tag jaltol-api:local asia-south1-docker.pkg.dev/gcp-welllabs/jaltol-api/jaltol-api:latest`
- Push image: `docker push asia-south1-docker.pkg.dev/gcp-welllabs/jaltol-api/jaltol-api:latest`

### 4.3 Create Cloud Run Configuration

**Conceptual Explanation:**
This YAML file is like a "recipe" that tells Cloud Run exactly how to run your container. Think of it as the job description for your API. It specifies:
- **Which Docker image to use** (from Artifact Registry)
- **How much resources to give it** (CPU, memory)
- **How many instances can run** (auto-scaling: 0-50)
- **Environment variables** (configuration your app needs)
- **Which secrets to load** (passwords, API keys)
- **How to connect to Cloud SQL** (via Unix socket)
- **Health check settings** (how to tell if the app is healthy)

**Key settings explained:**
- **minScale: 0**: Shuts down completely when no traffic (costs $0)
- **maxScale: 50**: Can handle up to 50 simultaneous instances if traffic spikes
- **concurrency: 80**: Each instance handles 80 requests at once
- **timeout: 300s**: Request fails if it takes longer than 5 minutes
- **startupProbe**: Checks `/api/health/` to confirm app started successfully
- **livenessProbe**: Keeps checking if app is still running

**Security:** Secrets (passwords, API keys) are pulled from Secret Manager at runtime, not hardcoded.

**New file**: `JaltolAPI/cloudrun.yaml` - Created with all necessary configuration

- Created the app service account with `gcloud iam service-accounts create jaltol-api-sa --display-name="Jaltol API Service Account"`
- Granted it access to Cloud SQL with `gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:jaltol-api-sa@gcp-welllabs.iam.gserviceaccount.com" --role="roles/cloudsql.client"`

### 4.4 Test - Local Docker Build (Optional)
Local runs won’t reach Cloud SQL (needs Cloud SQL Proxy), so database calls will fail. This mainly validates the container starts.

**Commands:**

```bash
# Build Docker image
docker build -t jaltol-api:local .

# Run container locally (test without Cloud SQL connection)
docker run -p 8080:8080 --env-file .env.production jaltol-api:local

# Test health endpoint
curl http://localhost:8080/api/health/

# View logs
docker logs <container_id>
```

### 4.5 Deploy - to Cloud Run
- Granted service account access to secrets with 
  ```bash
  gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:jaltol-api-sa@gcp-welllabs.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
  ```
- Used this command to list secrets `gcloud secrets list` and this one to get versions to be added to deploy command `gcloud secrets versions list database-password`
- Deployed with 
  ```bash
  gcloud run deploy jaltol-api --image asia-south1-docker.pkg.dev/gcp-welllabs/jaltol-api/jaltol-api:latest --region asia-south1 --platform managed --allow-unauthenticated --add-cloudsql-instances gcp-welllabs:asia-south1:jaltol-postgres --set-env-vars "DEBUG=False,RUN_ENV=cloudrun,DATABASE_NAME=jaltol_db,DATABASE_USER=admindatabase,CLOUD_SQL_CONNECTION_NAME=gcp-welllabs:asia-south1:jaltol-postgres,GOOGLE_APPLICATION_CREDENTIALS=/app/creds/gcp-welllabs-6e4173f30e21.json,GS_BUCKET_NAME=jaltol-static-files,GOOGLE_OAUTH2_CLIENT_ID=[YOUR-GOOGLE-OAUTH2-CLIENT-ID]" --set-secrets "DATABASE_PASSWORD=database-password:2,GOOGLE_OAUTH2_CLIENT_SECRET=google-oauth-secret:1,DJANGO_SECRET_KEY=django-secret-key:1" --memory 512Mi --cpu 1 --timeout 300 --concurrency 80 --max-instances 20 --min-instances 0 --service-account jaltol-api-sa@gcp-welllabs.iam.gserviceaccount.com
  ```
- Test with curl: `/api/health/`, `/api/get_boundary_data` and `/api/get_lulc_raster` worked perfectly. `/api/states` returned 500 error
- Debugging steps:
  1. Set `DEBUG=True` to get detailed error logs: `gcloud run services update jaltol-api --region asia-south1 --update-env-vars DEBUG=True`
  2. Error revealed: `password authentication failed for user "admindatabase"`
  3. Verified password in Secret Manager: `gcloud secrets versions access latest --secret="database-password"`
  4. Password had trailing newline character from `echo` command (Windows cmd issue)
  5. Fixed by creating password without newline using `echo|set /p="[MY-PASSWORD]">dbpass.txt` (Windows) or `Set-Content -NoNewline -Path dbpass.txt -Value '[MY-PASSWORD]'` (PowerShell)
  6. Added new secret version: `gcloud secrets versions add database-password --data-file=dbpass.txt`
  7. Redeployed with updated secret version number: `database-password:2` instead of `database-password:1`
  8. All endpoints including `/api/states` now work correctly. This also fixed the `/api/auth` issues.
  9. These commands were helpful for examining logs and debugging
    - `gcloud run services update jaltol-api --region asia-south1 --update-env-vars DEBUG=True`
    - `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=jaltol-api AND severity>=WARNING" --limit 50 > warnings.txt`
    - `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=[revision-name]" --limit 50 --format=json > errors.txt`


## Phase 5: CI/CD Pipeline Setup

### 5.1 Cloud Build Configuration

**Update file**: `JaltolAPI/cloudbuild.yaml`

**Conceptual Explanation:**
Cloud Build is like having an automated factory worker that watches your GitHub repo. When you push code, it:
1. Downloads your code from GitHub
2. Builds a Docker image using your Dockerfile
3. Pushes the image to Artifact Registry
4. Deploys the new version to Cloud Run
5. Runs any post-deployment tasks (migrations, static files)

**What the YAML file does:**
- **substitutions**: Variables that can be changed without editing code (like region, service name)
- **steps**: List of commands to run in order
- **timeout**: Kill the build if it takes longer than 10 minutes
- **images**: Automatically tag image with 'latest' and the git commit SHA

**Detailed Configuration:**

1. **Build Docker Image**
   - Step uses `gcr.io/cloud-builders/docker` (pre-installed Docker in Cloud Build)
   - Command: `docker build -t asia-south1-docker.pkg.dev/$PROJECT_ID/jaltol-api:$COMMIT_SHA .`
   - Tags with both commit SHA (for tracking) and `latest` (for convenience)
   - `$COMMIT_SHA` is automatically set by Cloud Build from git

2. **Push to Artifact Registry**
   - Uploads both `latest` tag (for easy reference) and commit SHA tag (for deployment tracking)
   - Uses `gcr.io/cloud-builders/docker` to push
   - Images: `asia-south1-docker.pkg.dev/gcp-welllabs/jaltol-api:$COMMIT_SHA` and `:latest`

3. **Deploy to Cloud Run**
   - Updates the service with the new image AND re-applies all configuration
   - Includes: env vars, secrets, Cloud SQL connection, scaling, service account
   - Uses the full deployment command (same as Phase 3.5) to ensure consistency
   - This is safer than relying on Cloud Run to persist settings across deployments

**Commands to prepare:**
```bash
gcloud projects describe gcp-welllabs --format="value(projectNumber)"
```

Allow Cloud Build to deploy to Cloud Run, to access secrets and push/pull Docker images from Artifact Registry
```bash
gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:YOUR_PROJECT_NUMBER@cloudbuild.gserviceaccount.com" --role="roles/run.admin"

gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:YOUR_PROJECT_NUMBER@cloudbuild.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:YOUR_PROJECT_NUMBER@cloudbuild.gserviceaccount.com" --role="roles/artifactregistry.writer"
```

**Deployment Behavior:**
- Cloud Run uses blue-green deployments by default
- New revision is created with the new image
- Old revision stays running until traffic is fully migrated
- Zero downtime - requests are only routed to the new revision after it's healthy
- Old revision is automatically cleaned up after a few days

**Important:** The Cloud Build config uses the **full deployment command** that includes all settings (env vars, secrets, scaling, etc.). This ensures that:
- Every deployment has the exact same configuration as your initial deployment
- No risk of configuration drift or missing settings
- Changes to secrets or env vars are explicitly reflected in the cloudbuild.yaml file

**Note:** Database migrations and static files collection happen at deployment time (handled by the `collectstatic` step in Dockerfile), so they're already automated. No need for separate migration steps in the build config.

### 5.2 GitHub Integration

**Conceptual Explanation:**
A build trigger watches your GitHub repo and automatically runs Cloud Build when you push code. It's like having a CI/CD pipeline that wakes up whenever you commit.

**Two Connection Methods:**

**Method: Cloud Build GitHub App (Recommended - Simpler)**
- Cloud Build installs an app on your GitHub organization/repository
- No personal OAuth tokens required
- More secure (scoped to specific repos)

**Steps to Set Up (via Console - Recommended):**

1. **Connect Repository** ✅ (Already completed)
   - Connected via Cloud Build GitHub App (1st gen)
   - Repository: `WELLlabs/JaltolAPI`

2. **Create Dedicated Service Account for Cloud Build**
   This creates a dedicated service account (cloud-build-deployer) for Cloud Build to use during deployments. It's given permissions needed to deploy to Cloud Run, access secrets, and push Docker images. Cloud Build itself is allowed to "impersonate" this account securely. This setup is needed because the default Cloud Build account can't deploy with custom permissions or set the runtime service account for Cloud Run, so a dedicated account with least-privilege access is safer and required for proper automation.

   - Created: `cloud-build-deployer@gcp-welllabs.iam.gserviceaccount.com`
   - Granted roles:
     ```bash
     gcloud iam service-accounts create cloud-build-deployer --display-name="Cloud Build Deployer"
     gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:cloud-build-deployer@gcp-welllabs.iam.gserviceaccount.com" --role="roles/run.admin"
     gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:cloud-build-deployer@gcp-welllabs.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
     gcloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:cloud-build-deployer@gcp-welllabs.iam.gserviceaccount.com" --role="roles/artifactregistry.writer"
     ```
   - Allow Cloud Build to impersonate it:
     ```bash
     gcloud iam service-accounts add-iam-policy-binding cloud-build-deployer@gcp-welllabs.iam.gserviceaccount.com --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" --role="roles/iam.serviceAccountTokenCreator"
     ```
   - Allow deployments that set the Cloud Run runtime Service Account
     ```bash
     gcloud iam service-accounts add-iam-policy-binding jaltol-api-sa@gcp-welllabs.iam.gserviceaccount.com --member="serviceAccount:cloud-build-deployer@gcp-welllabs.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
     ```
     
3. **Create Build Trigger via Console**
   - Go to: https://console.cloud.google.com/cloud-build/triggers
   - Click "Create Trigger"
   - **Name**: `jaltol-api-deploy`
   - **Event**: Push to a branch
   - **Source**: Select `WELLlabs/JaltolAPI`
   - **Branch**: `^main$` (regex pattern for main branch only)
   - **Configuration**: Cloud Build configuration file
   - **Location**: `cloudbuild.yaml` (in repo root, not in JaltolAPI/ subfolder)
   - **Service account**: `cloud-build-deployer@gcp-welllabs.iam.gserviceaccount.com` (select from dropdown)
   - Click "Create"

**Why Console over CLI?**
- 1st gen GitHub App connections have CLI compatibility issues with `gcloud builds triggers create`
- Console provides validation and guided setup
- Service account dropdown shows available options

**Important Notes:**
- `cloudbuild.yaml` is at repo root (not in a subfolder like `JaltolAPI/cloudbuild.yaml`)
- The trigger only fires on pushes to `main` branch
- Every push to `main` will trigger a full build and deployment
- Service account selection is required for 1st gen repositories (default Cloud Build SA not shown in dropdown)

**Test the Trigger:**
1. Make a small change (e.g., update a comment in any file)
2. Commit and push to `main` branch
3. Check Cloud Build history: https://console.cloud.google.com/cloud-build/builds
4. Watch the build progress in real-time
   ```bash
   cloud projects add-iam-policy-binding gcp-welllabs --member="serviceAccount:cloud-build-deployer@gcp-welllabs.iam.gserviceaccount.com" --role="roles/logging.logWriter"
   ```
5. Verify deployment by checking Cloud Run revisions

### 5.3 Earth Engine Authentication migrated to Application Default Credentials
Earth Engine authentication in all code and Cloud Run config was updated to use the Cloud Run service account (ADC), removing all key file references.

#### 5.3.1 Initial Error - Service Account Key File Missing

**Context**: The initial deployment used service account key files (`GOOGLE_APPLICATION_CREDENTIALS` pointing to a JSON file), which are not included in the Docker image. The app couldn't find the key file at `/app/creds/gcp-welllabs-6e4173f30e21.json`.

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '/app/creds/gcp-welllabs-6e4173f30e21.json'`

**Root Cause**: Service account key files were deprecated in favor of Application Default Credentials (ADC) for security and operational simplicity.

#### 5.3.2 Migration to Application Default Credentials

**Why ADC?**
- More secure: No long-lived key files that can leak
- Simpler operations: Auto-rotated credentials, no manual key management
- Better for Cloud Run: Uses the runtime service account's identity

**Steps:**

1. **Grant Earth Engine IAM Role**
   ```bash
   gcloud projects add-iam-policy-binding gcp-welllabs \
     --member="serviceAccount:jaltol-api-sa@gcp-welllabs.iam.gserviceaccount.com" \
     --role="roles/earthengine.admin"
   ```

2. **Grant Service Usage Consumer Role**
   ```bash
   gcloud projects add-iam-policy-binding gcp-welllabs \
     --member="serviceAccount:jaltol-api-sa@gcp-welllabs.iam.gserviceaccount.com" \
     --role="roles/serviceusage.serviceUsageConsumer"
   ```

3. **Update Code to Use ADC**
   - Modified all Earth Engine initialization functions in:
     - `gee_api/constants.py`
     - `gee_api/ee_processing.py`
     - `gee_api/views.py`
     - `gee_api/utils.py`

4. **Remove Key File Environment Variable from Cloud Run**
   ```bash
   gcloud run services update jaltol-api --region asia-south1 \
     --remove-env-vars=GOOGLE_APPLICATION_CREDENTIALS
   ```

5. **Add EE_PROJECT Environment Variable**
   ```bash
   gcloud run services update jaltol-api --region asia-south1 \
     --update-env-vars EE_PROJECT=gcp-welllabs
   ```

6. **Update cloudbuild.yaml to Remove Key Path**
   - Removed `GOOGLE_APPLICATION_CREDENTIALS=/app/creds/gcp-welllabs-6e4173f30e21.json` from `--set-env-vars`
   - Added `EE_PROJECT=gcp-welllabs` to env vars

#### 5.3.3 Earth Engine Asset Permissions

- Shared Earth Engine assets with service account `jaltol-api-sa@gcp-welllabs.iam.gserviceaccount.com` as Reader
- Ensured Earth Engine API is enabled for project
- Verified project is linked in Earth Engine Code Editor

#### 5.3.4 Verification Steps

1. Enabled DEBUG mode to see detailed errors:
   ```bash
   gcloud run services update jaltol-api --region asia-south1 --update-env-vars DEBUG=True
   ```

2. Checked logs after each deployment:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=jaltol-api AND severity>=ERROR" --limit 20
   ```

3. Tested endpoints:
   - `/api/health/` - ✅ Working
   - `/api/states/` - ✅ Working
   - `/api/get_boundary_data/` - ✅ Working
   - `/api/get_lulc_raster/` - ✅ Working

#### 5.3.5 Documentation Created

- `docs/AUTHENTICATION_ADC_VS_KEYFILE.md` - Conceptual explanation of the difference between key files and ADC

**Results**: All Earth Engine functionality now works with keyless authentication. No service account key files needed in the Docker image. IAM roles provide all necessary permissions.

### 5.4 Troubleshooting Common Issues

1. **Password Authentication Failed**
   - **Symptom**: `FATAL: password authentication failed for user "admindatabase"`
   - **Cause**: Trailing newline in secret value (especially when using `echo` on Windows)
   - **Solution**: Create password file without newline, then add as secret version

2. **Secret Version Mismatch**
   - **Symptom**: Cloud Run uses wrong secret version
   - **Solution**: Update deployment command with correct version number (e.g., `database-password:2`)

3. **Unix Socket Connection Issues**
   - **Symptom**: Cannot connect to Cloud SQL from Cloud Run
   - **Verify**: `--add-cloudsql-instances` flag includes correct connection name format
   - **Check**: Service account has `roles/cloudsql.client` role

4. **Missing Environment Variables**
   - **Symptom**: App fails to start or behaves unexpectedly
   - **Debug**: Use `DEBUG=True` to see detailed error logs
   - **Command**: `gcloud run services update jaltol-api --region asia-south1 --update-env-vars DEBUG=True`

## Phase 6: Testing & Validation

### 6.1 Smoke Tests
- Test authentication endpoints (register, login, Google OAuth)
- Test geographic data endpoints (states, districts, villages)
- Test Earth Engine endpoints (LULC, rainfall, SRTM)
- Test project management CRUD operations
- Verify static files load correctly

### 6.2 Performance Testing
- Test cold start latency (should be 3-5 seconds)
- Test warm response times (should be <500ms)
- Simulate traffic spike (50-100 concurrent users)
- Verify auto-scaling behavior
- Monitor Cloud Run metrics

### 6.3 Frontend Integration
- Update frontend environment variables with new API URL
- Test end-to-end user flows
- Verify CORS configuration
- Check authentication flow

## Phase 7: Production Hardening

### 7.1 Security Configuration
- Enable Cloud Armor (DDoS protection) if needed
- Configure IAM roles (principle of least privilege)
- Set up VPC Service Controls (optional, for enhanced security)
- Review and restrict service account permissions
- Enable audit logging

### 7.2 Monitoring & Alerting
- Set up Cloud Monitoring dashboards
- Configure alerts: error rate >5%, latency >2s, instance count
- Enable Cloud Logging for application logs
- Set up log-based metrics for custom monitoring
- Configure uptime checks

### 7.3 Cost Optimization
- Set budget alerts ($10, $25, $50 thresholds)
- Review and optimize container resource allocation
- Consider committed use discounts for Cloud SQL if usage is consistent
- Monitor egress costs (should be <$5/month initially)

## Phase 8: DNS & Custom Domain Configuration (optional)
- Map custom domain to Cloud Run service
- Configure SSL certificate (automatic via Cloud Run)
- Update DNS records (CNAME or A record)
- Update `ALLOWED_HOSTS` and CORS settings

## Key Files Modified/Created

**Existing files updated:**

- `JaltolAPI/Dockerfile` - Production-ready container
- `JaltolAPI/cloudbuild.yaml` - CI/CD pipeline
- `JaltolAPI/my_gee_backend/settings.py` - Cloud SQL + GCS config
- `JaltolAPI/requirements.txt` - Add django-storages

**New files created:**

- `JaltolAPI/cloudrun.yaml` - Cloud Run service config
- `JaltolAPI/.env.production` - Production env template
- `JaltolAPI/deploy.sh` - Manual deployment script
- `JaltolAPI/.gcloudignore` - Files to exclude from builds

## Estimated Costs (First Month)
- Cloud Run: ~$0.60/month (10K requests)
- Cloud SQL (db-f1-micro): ~$7/month
- Cloud Storage: ~$0.50/month
- Cloud Build: Free tier (120 build-minutes/day)
- **Total: ~$8-10/month**

## To-dos

- [x] Set up GCP project, enable APIs, configure gcloud CLI
- [x] Create Cloud SQL PostgreSQL instance and migrate data from AWS RDS
- [x] Set up GCS bucket for static files and configure django-storages
- [x] Update Django settings for Cloud SQL, GCS, and production environment
- [x] Configure Secret Manager for sensitive credentials
- [x] Update Dockerfile for production with Cloud SQL Proxy and Gunicorn
- [x] Create Cloud Run service configuration (cloudrun.yaml)
- [x] Update cloudbuild.yaml for CI/CD pipeline
- [x] Connect GitHub repository and set up Cloud Build triggers
- [x] Test deployment and verify all endpoints work
- [ ] Set up monitoring, alerting, and cost budgets
- [ ] Configure custom domain and SSL certificate