# Deploying Courtroom AI — Backend to Cloud Run (CI/CD), Frontend to Streamlit Cloud

Two files you need to add to your repo (both attached alongside this guide):
  - `backend/Dockerfile`
  - `backend/.dockerignore`
  - `cloudbuild.yaml`   ← goes at the REPO ROOT, not inside backend/

Everything below assumes your repo is already on GitHub with `backend/` and
`frontend/` folders at the root, and you're pushing to a `main` branch.


## 0. One-time local setup

```bash
# Install gcloud CLI if you don't have it: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud projects create courtroom-ai-<yourname> --name="Courtroom AI"   # or use an existing project
gcloud config set project courtroom-ai-<yourname>

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```


## 0.5. Before your first build — check backend/requirements.txt

Your `llm.py` was modified to use the generic `openai` SDK (pointed at
Groq's OpenAI-compatible endpoint) instead of the `groq` package. Make
sure `backend/requirements.txt` has `openai>=1.0.0` in it (add it if
missing) — otherwise the Docker build will succeed but the container will
crash on startup with `ModuleNotFoundError: No module named 'openai'`.
The `groq` package can stay or go; it's just unused now if `llm.py` no
longer imports it.


## 1. Create an Artifact Registry repo (holds your Docker images)

```bash
gcloud artifacts repositories create courtroom-ai \
  --repository-format=docker \
  --location=us-central1 \
  --description="Courtroom AI backend images"
```
(Region can be anything — just keep it consistent with `_REGION` in
`cloudbuild.yaml`, currently `us-central1`.)


## 2. Store your API keys in Secret Manager (never commit these to git)

```bash
echo -n "gsk_your_actual_groq_key" | gcloud secrets create GROQ_API_KEY --data-file=-
echo -n "tvly_your_actual_tavily_key" | gcloud secrets create TAVILY_API_KEY --data-file=-
echo -n "pk-lf-your_actual_key" | gcloud secrets create LANGFUSE_PUBLIC_KEY --data-file=-
echo -n "sk-lf-your_actual_key" | gcloud secrets create LANGFUSE_SECRET_KEY --data-file=-
```

If you ever need to rotate a key later:
```bash
echo -n "new_value" | gcloud secrets versions add GROQ_API_KEY --data-file=-
```


## 3. Give Cloud Build permission to deploy to Cloud Run + read secrets

```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

# Cloud Build's default service account needs Cloud Run Admin + Service Account User
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Cloud Run's runtime service account needs to READ the secrets
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```


## 4. Connect your GitHub repo and create the trigger (push to main → deploy)

Easiest via console (one-time):
1. Go to **Cloud Build → Triggers** in the GCP Console.
2. Click **Connect Repository**, choose GitHub, authenticate, select your repo.
3. Click **Create Trigger**:
   - Event: **Push to a branch**
   - Branch: `^main$`
   - Configuration: **Cloud Build configuration file** → `cloudbuild.yaml` (repo root)
   - Save.

Or via CLI, once the repo is connected:
```bash
gcloud builds triggers create github \
  --repo-name="YOUR_REPO_NAME" \
  --repo-owner="YOUR_GITHUB_USERNAME" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml"
```

From now on, every `git push` to `main` automatically:
  builds `backend/Dockerfile` → pushes to Artifact Registry → deploys to Cloud Run.


## 5. First deploy (don't wait for a push — trigger it manually once to confirm it works)

```bash
gcloud builds submit --config=cloudbuild.yaml .
```

Watch the build in **Cloud Build → History**. Once it succeeds:
```bash
gcloud run services describe courtroom-backend --region=us-central1 --format='value(status.url)'
```
This prints your backend's public URL, e.g.
`https://courtroom-backend-xxxxx-uc.a.run.app` — copy it, you'll need it for
Streamlit Cloud next.

Sanity check:
```bash
curl https://courtroom-backend-xxxxx-uc.a.run.app/health
```


## 6. Frontend — Streamlit Community Cloud (separate from GCP, no Docker needed)

1. Push `frontend/` (already in your repo) to GitHub if not already there.
2. Go to https://share.streamlit.io → **New app**.
3. Point it at your repo, branch `main`, main file path `frontend/app.py`.
4. Under **Advanced settings → Secrets**, add:
   ```toml
   BACKEND_URL = "https://courtroom-backend-xxxxx-uc.a.run.app"
   ```
   (the Cloud Run URL from step 5 — your `frontend/app.py` already reads
   this via `os.getenv("BACKEND_URL", ...)`, so no code change needed.)
5. Deploy. Streamlit Cloud has its own separate GitHub integration — it
   auto-redeploys on every push to `main` too, independently of the GCP
   pipeline. No cloudbuild/Docker involvement for the frontend at all.


## 7. Lock down CORS (do this after confirming everything works)

Right now `backend/main.py` has:
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```
Once you have your real Streamlit Cloud URL, tighten this:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app-name.streamlit.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Commit + push — CI/CD redeploys the backend automatically.


## 8. Before going live — the Ollama fallback risk (see PROJECT_CONTEXT.txt §5, §7)

Your current `backend/llm.py` supports `LLM_PROVIDER=groq` or `ollama`.
Cloud Run has no Ollama server reachable at `localhost:11434`, so if
`LLM_PROVIDER` ever ends up set to `ollama` in production, every LLM call
will fail outright. The `cloudbuild.yaml` above explicitly sets
`--set-env-vars=...,LLM_PROVIDER=groq,...` to force this, but double-check
after your first deploy:
```bash
curl -X POST https://courtroom-backend-xxxxx-uc.a.run.app/simulate/full \
  -H "Content-Type: application/json" \
  -d '{"complaint": "test case"}'
```
If this fails or errors, check `LLM_PROVIDER` in the Cloud Run service's
env vars (Console → Cloud Run → your service → Edit & Deploy New Revision
→ Variables & Secrets).


## Ongoing workflow, after this is all set up

```bash
git add .
git commit -m "some backend change"
git push origin main
```
→ Cloud Build trigger fires → backend redeploys automatically on Cloud Run.
→ Streamlit Cloud separately redeploys the frontend automatically too.

No manual `gcloud run deploy` needed after the first-time setup above.