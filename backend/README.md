<div align="center">
  <h1>🚀 Chaatly Backend</h1>
  <p><strong>A fast and robust backend for the Chaatly application, built with FastAPI.</strong></p>
</div>

<br />

## ✨ Features

- **FastAPI Framework:** High-performance RESTful API using modern Python async capabilities.
- **Authentication:** Secure user registration, login, and JWT-based session management (access & refresh tokens).
- **Meetups Management:** Create and manage meetups endpoints.
- **PostgreSQL Database:** Robust relational database for reliable data storage.
- **Email Notifications:** Integrated with [Resend](https://resend.com/) for reliable email delivery.
- **CORS Enabled:** Seamless integration with frontend applications.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **FastAPI**
- **Uvicorn**
- **PostgreSQL**
- **SQLAlchemy** (or similar ORM depending on setup)
- **Pytest** for testing

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- PostgreSQL running locally or remotely

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/chaatly-backend.git
cd chaatly-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv chaatapp
source chaatapp/bin/activate  # On Windows: chaatapp\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the root directory based on the provided `.env.example` file:

```bash
cp .env.example .env
```

Make sure to update the `.env` variables with your specific database credentials and Resend API key.

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

The application will be available at: `http://localhost:8000`

Interactive API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🧪 Testing

To run tests using `pytest`, use the following command:

```bash
pytest tests/
```

---

## 📁 Project Structure

```
.
├── app/
│   ├── main.py          # FastAPI application instance & routing
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas for data validation
│   ├── database.py      # Database connection
│   ├── security.py      # Password hashing, JWT auth
│   └── routers/         # API routes (meetups, users, auth)
├── chaatapp/            # Virtual environment
├── scripts/             # Useful scripts
├── tests/               # Test cases
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables
```

---

## 🤝 Contributing

Contributions, issues and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/chaatly-backend/issues).
