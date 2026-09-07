# Docker-Compose-Free Local PostgreSQL Setup Guide

Per the **LegalLens** constitution ([AGENTS.md](file:///c:/Users/Athul/OneDrive/Desktop/LegalLens/AGENTS.md)), we do not introduce Docker or container orchestration. This guide provides lightweight, native PostgreSQL setup instructions for local development across platforms.

---

## 1. Installation

### Windows
1. **Official EDB Installer**:
   - Download the PostgreSQL Windows installer from [EnterpriseDB](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
   - Run the installer, select PostgreSQL 15 or 16.
   - During installation, set a password for the `postgres` superuser (e.g., `postgres` for local development) and keep the default port `5432`.
2. **Via Winget** (PowerShell):
   ```powershell
   winget install PostgreSQL.PostgreSQL --accept-package-agreements --accept-source-agreements
   ```
3. **Via Scoop** (if installed):
   ```powershell
   scoop install postgresql
   ```

### macOS (Homebrew)
```bash
brew install postgresql@15
brew services start postgresql@15
```

### Linux (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

## 2. Database & User Creation

Open a terminal or PowerShell prompt and connect to PostgreSQL using `psql`:

```bash
psql -U postgres
```
*(Enter the superuser password when prompted).*

Execute the following SQL commands to create the dedicated database and grant permissions:

```sql
-- 1. Create LegalLens database
CREATE DATABASE legallens;

-- 2. (Optional) Create dedicated user if not using default postgres
CREATE USER legallens_user WITH ENCRYPTED PASSWORD 'legallens_secure_pass';
GRANT ALL PRIVILEGES ON DATABASE legallens TO legallens_user;

-- 3. Verify connection
\c legallens
\q
```

---

## 3. Environment Configuration

Update your root `.env` file with the connection string:

```env
# For default postgres superuser
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legallens

# Or for custom user
# DATABASE_URL=postgresql://legallens_user:legallens_secure_pass@localhost:5432/legallens
```

---

## 4. Connection Verification Script

You can verify that your PostgreSQL database is accepting connections by running:

```bash
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/legallens'); print('✅ PostgreSQL connection successful!'); conn.close()"
```

> **Offline / Fallback Mode**:
> If running in an environment without a running PostgreSQL server, LegalLens can gracefully fallback to a local SQLite database (`sqlite:///./backend/legallens_dev.db`) during development and unit testing by setting:
> ```env
> DATABASE_URL=sqlite:///./backend/legallens_dev.db
> ```
