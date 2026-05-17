# Diag1

Diag1 to aplikacja webowa do porownywania wynikow badan laboratoryjnych z uzyciem modelu AI. Publiczne repo zawiera tylko kod aplikacji, infrastrukture oraz pliki potrzebne do lokalnego buildu i wdrozenia. Nie zawiera dokumentow projektowych, przykladowych badan, wynikow testow ani workflow GitHub Actions.

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic
- Frontend: Vue 3, Vite, Tailwind
- Infrastruktura: Docker, Cloud Run, Terraform, Artifact Registry
- AI: Vertex AI / Gemini

## Struktura repo

```text
.
├── backend/            # aplikacja FastAPI i migracje Alembic
├── frontend/           # aplikacja Vue 3
├── terraform/          # infrastruktura dla env dev i stage
├── scripts/            # skrypty pomocnicze do GCP / Terraform / DNS
├── docker-compose.yml  # lokalne uruchomienie calego stosu
├── Makefile            # podstawowe komendy developerskie
└── .env.example        # wzor zmiennych srodowiskowych
```

## Lokalny start

Wymagania:

- VS Code lub inny edytor
- Docker Desktop / Docker Engine
- `make`
- opcjonalnie `gcloud`, jesli lokalnie chcesz uzywac Vertex AI

Kroki:

```bash
git clone <repo-url> diag1
cd diag1
cp .env.example .env
```

Skonfiguruj `.env`:

- Dla Gemini Developer API ustaw `AI_PROVIDER=gemini` i `GEMINI_API_KEY`.
- Dla Vertex AI ustaw `AI_PROVIDER=vertex`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION` i zaloguj sie lokalnie przez `gcloud auth application-default login`, albo uzyj lokalnego pliku service account JSON.

Jesli korzystasz z lokalnego pliku service account JSON w Dockerze:

1. zapisz go lokalnie jako `backend/service-account.local.json`,
2. plik pozostaw poza Gitem,
3. ustaw w `.env`:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=/secrets/service-account.local.json
```

Uruchom aplikacje:

```bash
make up
make migrate
```

Adresy lokalne:

- frontend: `http://localhost:9080`
- backend health: `http://localhost:9000/api/healthz`
- postgres: `localhost:9543`

Podstawowe komendy:

- `make up`
- `make down`
- `make logs`
- `make build`
- `make migrate`

## Wdrozenie do GCP z lokalnej maszyny

Model wdrozenia jest celowo prosty:

- obrazy Docker budujesz lokalnie, np. z VS Code,
- wypychasz je do Artifact Registry,
- Terraform uruchamiasz lokalnie,
- repo nie zaklada GitHub Actions ani Cloud Build.

### 1. Wymagania

- `gcloud` zalogowany przez `gcloud auth login`
- ADC skonfigurowane przez `gcloud auth application-default login`
- Docker z obsluga `linux/amd64`
- Terraform `>= 1.5`
- istniejąca baza PostgreSQL dostepna z Cloud Run

Uwaga:

- Terraform w tym repo nie tworzy bazy danych.
- Do `database_url` podajesz gotowy adres swojej bazy: Cloud SQL, AlloyDB lub zewnetrzny PostgreSQL.
- Jesli wybierasz Cloud SQL, skonfiguruj lacznosc do bazy osobno i wpisz poprawny DSN w `terraform.tfvars`.

### 2. Bootstrap projektu GCP

Skrypt wlacza wymagane API i tworzy bucket na stan Terraform:

```bash
./scripts/gcp_bootstrap.sh <PROJECT_ID> <BILLING_ACCOUNT_ID> [REGION]
```

Skrypt nie buduje obrazow i nie publikuje nic przez GitHub.

### 3. Zbuduj obrazy lokalnie

Cloud Run uruchamia obrazy `linux/amd64`, wiec buduj je zawsze z tym targetem:

```bash
export PROJECT_ID=<your-gcp-project-id>
export REGION=europe-west4

export IMAGE_BACKEND=$REGION-docker.pkg.dev/$PROJECT_ID/diag1/backend:release-001
export IMAGE_FRONTEND=$REGION-docker.pkg.dev/$PROJECT_ID/diag1/frontend:release-001

gcloud config set project "$PROJECT_ID"
gcloud auth configure-docker "$REGION-docker.pkg.dev"

docker build --platform linux/amd64 -t "$IMAGE_BACKEND" ./backend
docker build --platform linux/amd64 \
  --build-arg VITE_API_URL=https://app.example.com \
  -t "$IMAGE_FRONTEND" \
  ./frontend
```

### 4. Wypchnij obrazy do Artifact Registry

```bash
docker push "$IMAGE_BACKEND"
docker push "$IMAGE_FRONTEND"
```

### 5. Ustaw Terraform

Przygotuj konfiguracje:

```bash
cp terraform/stage/terraform.tfvars.example terraform/stage/terraform.tfvars
```

Uzupełnij w `terraform/stage/terraform.tfvars` co najmniej:

- `project_id`
- `region`
- `domain`
- `database_url`
- `backend_image`
- `frontend_image`
- opcjonalnie `frontend_access_password`
- opcjonalnie `frontend_access_cookie_secret`

Jesli chcesz przechowywac stan Terraform w GCS, odkomentuj backend `gcs` w `terraform/stage/main.tf`.

### 6. Uruchom Terraform lokalnie

```bash
./scripts/terraform_gcp.sh --env stage init
./scripts/terraform_gcp.sh --env stage plan -var-file=terraform.tfvars
./scripts/terraform_gcp.sh --env stage apply -var-file=terraform.tfvars
```

Terraform wystawia:

- Artifact Registry
- Cloud Run backend
- Cloud Run frontend
- globalny Load Balancer
- zarzadzany certyfikat SSL

### 7. DNS i weryfikacja

Po `apply` pobierz adres LB:

```bash
cd terraform/stage
terraform output -raw lb_ip
```

Dodaj rekord `A` dla swojej domeny wskazujacy na ten adres.

Pomocniczo:

```bash
./scripts/show_dns_records.sh stage
./scripts/smoke_check_cloudrun.sh https://app.example.com
```

## Pliki lokalne, ktore nie powinny trafic do Git

Do repo nie powinny trafic miedzy innymi:

- `.env`
- `terraform/**/*.tfvars`
- `backend/seed/`
- `backend/tests/`
- `backend/app/testsupport/`
- `docker-compose.test.yml`
- lokalne klucze JSON, np. `backend/service-account.local.json`
- dokumenty, badania, notatki i eksporty robocze

## Bezpieczenstwo

- Nie commituj plikow z kluczami, haslami ani lokalnych eksportow danych.
- Dla publicznego wdrozenia ustaw wlasne wartosci `ADMIN_PASSWORD` i, jesli wlaczasz bramke haslową, rowniez `FRONTEND_ACCESS_COOKIE_SECRET`.
- `terraform.tfvars` i `.env` maja zostac lokalne.

## Licencja

Projekt jest objety licencja z pliku `LICENSE`.
