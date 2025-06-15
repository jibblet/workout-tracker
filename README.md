#FULL credit to Author @enrique-paulino for original design and function. 

# 🏋️‍♂️ Workout Tracker

A simple and self-hostable workout tracking web app built with **Flask**, **SQLite**, and **Docker**.
---

## 📺 Demo


[![image](https://github.com/user-attachments/assets/d09abade-95e8-410d-b899-5bb033b6c019)](https://www.youtube.com/watch?v=xcMvPMsAjEs)


## 🚀 Features

- ✅ Log daily workouts by category and exercise type  
- 📊 Track performance and progress over time  
- 👥 Admin user management with authentication  
- 💾 Uses SQLite — zero setup, file-based database  
- 🐳 Containerised with Docker for effortless deployment  
- ⚙️ Environment-variable-driven configuration  
- 🛡️ Passwords hashed with `werkzeug.security`  

---

## 📦 Tech Stack

- **Backend**: Python 3.11, Flask, SQLAlchemy, Flask-Migrate  
- **Database**: SQLite (customisable)  
- **Server**: Waitress (production-ready WSGI server)  
- **Packaging**: Docker & Docker Compose  

---

## 🧪 Local Development

### 🔧 Requirements

- Python 3.11+
- `pip`
- Optional: virtualenv

```bash
git clone https://github.com/enrique-paulino/workout-tracker.git
cd workout-tracker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
### 🧠 Initialisation

```bash
python -m app.init_app
python run.py
```

Open `http://localhost:5000` in your browser.
Default admin credentials are:
- **Username**: admin
- **Password**: adminpass123

You can customise these via environment variables.

---

## 🐳 Docker Deployment

The image for this project can be found on [Docker](https://hub.docker.com/r/ennoluto/workout-tracker).

### ⚡ Quick Start
```bash
docker build -t workout-tracker .
docker run -d -p 5000:5000 \
  -e PORT=5000 \
  -e SQLITE_DB_PATH=sqlite:////app/app.db \
  -v $(pwd)/app.db:/app/app.db \
  workout-tracker
```

### 🧰 Docker Compose (recommended)
```yaml
version: '3.8'
services:
  workout-tracker:
    image: ennoluto/workout-tracker:latest
    container_name: workout-tracker
    ports:
      - "5000:5000"  # host:container (change host port if you want, e.g. "272:5000")
    environment:
      - PORT=5000
      - SQLITE_DB_PATH=sqlite:////app/data/app.db
    volumes:
      - ./data:/app/data
```
Start with:
```docker-compose up -d```

## ⚙️ Configuration

The application uses environment variables for configuration. Below are the supported options:

| Environment Variable | Description                          | Default              |
|----------------------|--------------------------------------|----------------------|
| `PORT`               | Port the app listens on              | `5000`               |
| `SQLITE_DB_PATH`     | SQLAlchemy DB URI                    | `sqlite:///app.db`   |
| `ADMIN_USERNAME`     | Admin account username               | `admin`              |
| `ADMIN_EMAIL`        | Admin email                          | `admin@example.com`  |
| `ADMIN_PASSWORD`     | Admin password (hashed internally)   | `adminpass123`       |

---

## 🛡️ License

This project is licensed under the [MIT License](LICENSE).

---

## 👨‍💻 Author

Made with 💪 by [@enrique-paulino](https://github.com/enrique-paulino)

> Contributions, issues and feedback welcome!
