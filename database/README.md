# Database Architecture & Management — MedVision AI

## 1. Overview
MedVision AI leverages a structured relational database to persist anonymous session logs, image technical metadata (format, dimensions, SHA-256 hash), and inference audit records.

In strict adherence to medical privacy and data security:
- **No Raw Image Blobs**: Medical images are processed entirely in memory during inference. Raw pixel data is never written to disk or stored in the database.
- **Zero Protected Health Information (PHI)**: Sessions are tracked via randomly generated UUID v4 identifiers, preventing correlation with patient identities.
- **Auditability via Hashing**: The `file_hash` column stores an in-memory SHA-256 cryptographic digest of the uploaded image to support deduplication and audit tracking without retaining sensitive medical imaging files.

---

## 2. Single-Instance vs. Multi-Instance Deployment Architecture

### Architecture Comparison
| Deployment Tier | Database Engine | Concurrency Model | Recommended Target |
| :--- | :--- | :--- | :--- |
| **Local Demonstration & Development** | SQLite 3.35+ | Single process / thread-safe with WAL mode | Local machine, researcher workstation |
| **Private Staging / Single-Node VM** | SQLite 3.35+ (with WAL) | Multi-worker on single host with `busy_timeout=30000` | Single dedicated GPU/CPU VM (e.g. AWS EC2, GCP Compute Engine) |
| **Public Production / Clustered** | PostgreSQL 15+ | Connection pooling (`QueuePool`), multi-container | Managed Cloud SQL, AWS RDS Aurora, Azure Database |

### Why SQLite is Strictly Single-Instance
SQLite writes require filesystem-level locks. While SQLite Write-Ahead Logging (WAL) mode enables concurrent readers alongside a serialized writer on a single machine, **SQLite cannot safely scale across multiple container instances or distributed load balancers** sharing network-attached storage (NFS/EFS), which risks database corruption. Multi-container or auto-scaled architectures must use PostgreSQL.

---

## 3. Directory Structure
```text
database/
├── schema.sql              # DDL script defining tables, constraints, and indexes
├── init_db.py              # Script to bootstrap local SQLite database
├── migrate_to_postgres.py  # Zero-data-loss migration utility from SQLite to PostgreSQL
└── README.md               # Operational documentation
```

---

## 4. SQLite Operational Maintenance, Backups & Recovery

### File Permissions Hardening
On POSIX environments, the database file permissions are automatically hardened to `0o600` (owner read/write only) at backend startup to prevent local unauthorized access:
```bash
chmod 600 medvision.db
```

### Consistent Online Hot Backup
Because Write-Ahead Logging (WAL) is active, standard file copying (`cp` or `copy`) while the server is running can produce corrupted snapshots. Always use the official SQLite online backup API:

**Linux / macOS (Bash):**
```bash
sqlite3 medvision.db ".backup 'backups/medvision_backup_$(date +%Y%m%d_%H%M%S).db'"
```

**Windows (PowerShell):**
```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
sqlite3 medvision.db ".backup 'backups/medvision_backup_$ts.db'"
```

### WAL Checkpointing & Maintenance
To truncate the WAL file and merge pending transactions back into the main database file:
```bash
sqlite3 medvision.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

### Database Integrity Verification
```bash
sqlite3 medvision.db "PRAGMA integrity_check;"
# Expected output: ok
```

---

## 5. PostgreSQL Migration Plan & Procedure

When upgrading to a multi-container or clustered cloud deployment:

### Step 1: Provision Target PostgreSQL Instance
Provision a managed PostgreSQL instance (v15+) with SSL enforced (`sslmode=require`).

### Step 2: Validate Source Database & Schema Dry-Run
Run pre-flight validation to verify source record counts and table schemas without modifying any database:
```bash
python database/migrate_to_postgres.py --sqlite-path medvision.db --dry-run
```

### Step 3: Execute Migration
Run the migration script to create the schema, transfer all historical `analysis_sessions` audit records in batches, and verify row-count parity:
```bash
python database/migrate_to_postgres.py \
  --sqlite-path medvision.db \
  --postgres-url "postgresql://medvision_user:SecurePassword@db.internal:5432/medvision?sslmode=require" \
  --batch-size 500
```

### Step 4: Update Backend Configuration
Set the production database environment variable:
```env
DATABASE_URL=postgresql://medvision_user:SecurePassword@db.internal:5432/medvision?sslmode=require
```

The FastAPI backend automatically detects the PostgreSQL dialect and configures production connection pooling (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`).
