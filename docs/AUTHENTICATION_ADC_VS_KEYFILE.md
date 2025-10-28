## Application Default Credentials (ADC) vs Service Account Key Files

### Overview
There are two common ways your app authenticates to Google APIs like Earth Engine:
- Service account key file via `GOOGLE_APPLICATION_CREDENTIALS`
- Keyless Application Default Credentials (ADC)

### Approach 1 — Service account key file (GOOGLE_APPLICATION_CREDENTIALS)
- You create a long‑lived JSON key for a service account.
- You place the file on the machine/container and point `GOOGLE_APPLICATION_CREDENTIALS` to it.
- Code loads the file and authenticates.
- Pros: works anywhere (on‑prem, laptops).
- Cons: static secret can leak, must rotate/distribute carefully, devops overhead, not tied to the Cloud Run service account identity.

### Approach 2 — Application Default Credentials (ADC)
- Code asks Google’s auth library for “default credentials” (no file).
- On Cloud Run, Google injects short‑lived credentials for the service account attached to the service.
- No key files to manage; tokens are auto‑rotated; identity is exactly the Cloud Run service account.
- For local dev, ADC uses your `gcloud auth application-default login` user or a local key if you set one.

### Why Google recommends ADC
- Stronger security: no static keys to steal; short‑lived tokens auto‑rotate.
- Simpler operations: nothing to copy/mount/rotate; IAM changes take effect immediately.
- Least privilege and auditability: permissions flow from the runtime service account you configured.

### Earth Engine specifics
- Earth Engine uses Google auth plus its own asset ACLs.
- With ADC, the identity is your Cloud Run service account (e.g., `jaltol-api-sa@…`).
- You must:
  - Enable the Earth Engine API for your project.
  - Grant Earth Engine IAM role(s) to the service account (e.g., `roles/earthengine.admin` as you chose).
  - Share private EE assets with the service account (Reader/Writer as needed).
  - Optionally set the EE project when initializing EE.

### Code pattern (ADC)
Use ADC instead of a key file when initializing Earth Engine:

```python
import os
import ee
import google.auth

def initialize_earth_engine():
    creds, _ = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/earthengine',
        'https://www.googleapis.com/auth/cloud-platform',
    ])
    ee.Initialize(credentials=creds, project=os.getenv('EE_PROJECT', 'gcp-welllabs'))
    return creds
```

### When to use which
- Use ADC (recommended): workloads running on Google Cloud (Cloud Run, GCE, GKE) or where you can rely on a runtime service account.
- Use key files: only when running outside Google Cloud and ADC isn’t available.

### Migration checklist (Jaltol)
- Cloud Run service account has Earth Engine role(s) in IAM.
- Earth Engine API enabled for the project; project linked in the EE Code Editor.
- Private EE assets shared with the Cloud Run service account.
- Remove `GOOGLE_APPLICATION_CREDENTIALS` from Cloud Run env vars.
- Update EE initialization to ADC (no key file).
- Optionally set `EE_PROJECT=gcp-welllabs` in the Cloud Run service.

### References
- [Earth Engine: Service accounts and authentication](https://developers.google.com/earth-engine/guides/service_account)
- [Google Cloud: Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc)
- [Cloud Run: Using service accounts](https://cloud.google.com/run/docs/securing/service-identity)


