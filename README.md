# Tatou - PDF Watermarking Platform

A secure web platform for PDF watermarking with comprehensive security controls. This project demonstrates security best practices including XSS protection, SQL injection prevention, path traversal protection, and more.

⚠️ **Note:** This project is intended for pedagogical use. Do not deploy on an open network.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.8+ (for local testing)
- Git

### 1. Clone Repository
```bash
git clone https://github.com/nharrand/tatou.git
cd tatou
```

### 2. Configure Environment
```bash
# Copy environment template
cp sample.env .env

# Edit .env with your passwords
nano .env
```

### 3. Deploy with Docker
```bash
# Build and start all services
docker compose up --build -d

# Monitor logs
docker compose logs -f

# Verify server is running
curl http://127.0.0.1:5000/healthz
```

**Services:**
- **API Server:** http://127.0.0.1:5000
- **phpMyAdmin:** http://127.0.0.1:8080
- **Database:** MariaDB on port 3306

---

## 🧪 Testing

### Unit Tests

Run Python unit tests using pytest:

```bash
cd server

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies with dev tools
pip install -e ".[dev]"

# Run all unit tests
pytest

# Run specific test file
pytest ../tests/test_watermark_qr_unit.py

# Run with verbose output
pytest -v
```

**Test Coverage:**
- 17 unit test files in `tests/`
- Tests for watermarking, authentication, API endpoints, and security features

### API Tests (Regression Tests)

Verify security fixes with regression tests:

```bash
# Ensure server is running first
docker compose up -d

# Run all regression tests
cd fuzzing/regression_tests
./run_all_regression_tests.sh http://localhost:5000

# Run individual test
./rt_xss_create_user_login.sh http://localhost:5000
```

**Available Test Categories:**
- XSS Protection (4 tests)
- Path Traversal Protection (4 tests)
- SQL Injection Prevention (3 tests)
- XXE Protection (2 tests)
- Rate Limiting (2 tests)
- Information Disclosure (2 tests)

### Non-Regression Tests (Functionality)

Ensure core functionality still works:

```bash
cd fuzzing/non_regression_tests
./run_all_non_regression_tests.sh http://localhost:5000
```

### Quick Validation

Fast security check (recommended for CI/CD):

```bash
./QUICK_VALIDATION.sh http://localhost:5000
```

---

## 📊 Coverage Analysis

### Generate Coverage Report

```bash
cd server
source .venv/bin/activate

# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
firefox htmlcov/index.html
```

Coverage report will be generated in `htmlcov/` directory.

---

## 🔒 Security Features

This platform implements multiple security controls:

✅ **XSS Protection** - Input sanitization and output encoding  
✅ **SQL Injection Prevention** - Parameterized queries  
✅ **Path Traversal Protection** - Filename validation  
✅ **XXE Protection** - Safe XML parsing  
✅ **Rate Limiting** - Brute force prevention  
✅ **Security Headers** - CSP, X-Frame-Options, etc.  
✅ **Safe Error Handling** - No information disclosure  

**Vulnerability Status:** All known vulnerabilities fixed ✅

---

## 🛠️ Development

### Project Structure
```
tatou/
├── server/              # Flask API server
│   ├── src/            # Source code
│   │   ├── server.py           # Main API server
│   │   ├── security_utils.py   # Security functions
│   │   ├── watermark_*.py      # Watermarking modules
│   │   └── rmap/              # RMAP integration
│   ├── pyproject.toml  # Python dependencies
│   └── Dockerfile      # Server container
├── tests/              # Unit tests (pytest)
├── fuzzing/            # Security testing
│   ├── regression_tests/      # Security tests
│   └── non_regression_tests/  # Functionality tests
├── db/                 # Database initialization
├── docker-compose.yml  # Service orchestration
└── README.md          # This file
```

### Running Server Locally (without Docker)

```bash
cd server

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export DB_HOST=localhost
export DB_USER=tatou
export DB_PASSWORD=your_password

# Run server
cd src
python server.py
```

**Note: If rmap connection fails, run the following commands:**
```bash
export SERVICE_TOKEN=softsec2025
flask run --host=0.0.0.0 --port=5000
```

### Stop Services

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (⚠️ deletes data)
docker compose down -v
```

---

## 📚 Documentation

- **[API.md](server/API.md)** - API endpoint documentation
- **[FUZZING_REPORT.md](fuzzing/FUZZING_REPORT.md)** - Security testing methodology
- **[SECURITY_QUICK_REFERENCE.txt](SECURITY_QUICK_REFERENCE.txt)** - Security guidelines
- **[PROJECT_STATUS.txt](PROJECT_STATUS.txt)** - Development status

---

## 📝 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

## 🎓 Educational Purpose

This platform is designed for security education and demonstrates:
- Common web vulnerabilities (historical)
- Security remediation techniques
- Secure coding practices
- Security testing methodologies

**Do not use in production without thorough security review.**
