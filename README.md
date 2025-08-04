# JaltolAPI - Backend Application

A Django REST API backend for the Jaltol platform, providing geospatial analysis, Google Earth Engine integration, and project management capabilities.

## 🚀 Quick Start

### Prerequisites

- **Python** (v3.8 or higher)
- **pip** (Python package manager)
- **Git**
- **PostgreSQL** (optional, SQLite included for development)
- **Google Earth Engine** account and service credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/WELLLABS_GITHUB.git
   cd WELLLABS_GITHUB/JaltolAPI
   ```

2. **Create and activate virtual environment**
   
   **Windows (PowerShell):**
   ```powershell
   # Create virtual environment
   python -m venv jaltolvenv
   
   # Activate virtual environment
   .\jaltolvenv\Scripts\Activate.ps1
   
   # If you get execution policy error, run this first:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   
   **macOS/Linux:**
   ```bash
   # Create virtual environment
   python3 -m venv jaltolvenv
   
   # Activate virtual environment
   source jaltolvenv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   # Install core packages
   pip install -r requirements.txt
   ```

   **If you encounter installation errors, install packages individually:**
   ```bash
   # Core Django
   pip install Django==5.0.1
   pip install djangorestframework==3.15.2
   pip install django-cors-headers==4.3.1
   
   # Authentication & JWT
   pip install djangorestframework-simplejwt==5.3.0
   
   # Google Authentication & OAuth  
   pip install google-auth==2.27.0
   pip install google-auth-oauthlib==1.1.0
   pip install google-auth-httplib2==0.2.0
   
   # Google Earth Engine
   pip install earthengine-api==0.1.386
   
   # Environment & Configuration
   pip install python-dotenv==1.0.1
   
   # HTTP Requests
   pip install requests==2.31.0
   
   # Database (PostgreSQL - optional)
   pip install psycopg2==2.9.9
   pip install psycopg2-binary==2.9.9
   
   # Production Server
   pip install gunicorn==21.2.0
   ```

4. **Set up environment variables** (see [Environment Configuration](#environment-configuration))

5. **Set up Google Earth Engine credentials** (see [GEE Setup](#google-earth-engine-setup))

6. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start development server**
   ```bash
   python manage.py runserver
   ```

9. **Open in browser**
   - API Root: `http://127.0.0.1:8000/api/`
   - Admin Panel: `http://127.0.0.1:8000/admin/`

## 🔧 Environment Configuration

### Required Environment Files

Create the following file in the `JaltolAPI/` root directory:

#### `.env` (Required)
```env
# Django Configuration
SECRET_KEY=your-super-secret-django-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration (Optional - uses SQLite by default)
# DATABASE_URL=postgresql://username:password@localhost:5432/jaltol_db

# Google Earth Engine
GOOGLE_EARTH_ENGINE_API_KEY=your-gee-api-key
GOOGLE_APPLICATION_CREDENTIALS=./creds/ee-papnejaanmol-23b4363dc984.json

# Google OAuth2
GOOGLE_OAUTH2_CLIENT_ID=your-google-oauth-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-oauth-client-secret

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Production Settings (for deployment)
# DEBUG=False
# ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
# CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### Environment Variables Explained

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key for security | ✅ Yes |
| `DEBUG` | Enable Django debug mode | ✅ Yes |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | ✅ Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GEE service account JSON | ✅ Yes |
| `GOOGLE_OAUTH2_CLIENT_ID` | Google OAuth client ID | ✅ Yes |
| `GOOGLE_OAUTH2_CLIENT_SECRET` | Google OAuth client secret | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection string | ❌ Optional |
| `CORS_ALLOWED_ORIGINS` | Frontend URLs for CORS | ✅ Yes |

## 🗝️ Google Earth Engine Setup

### 1. Service Account Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create/Select a Project**
   - Create a new project or select existing one

3. **Enable Earth Engine API**
   - Go to "APIs & Services" > "Library"
   - Search for "Earth Engine API" and enable it

4. **Create Service Account**
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Name: `earth-engine-service-account`
   - Role: `Earth Engine Resource Admin`

5. **Generate Key**
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose JSON format
   - Download the JSON file

6. **Place Credentials**
   ```bash
   # Create creds directory
   mkdir creds
   
   # Move the downloaded JSON file
   mv /path/to/downloaded/service-account-key.json ./creds/ee-papnejaanmol-23b4363dc984.json
   ```

7. **Update .env file**
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=./creds/ee-papnejaanmol-23b4363dc984.json
   ```

### 2. Earth Engine Authentication

```bash
# Authenticate with Earth Engine (one-time setup)
earthengine authenticate

# Test the connection
python manage.py shell
>>> import ee
>>> ee.Initialize()
>>> print("Earth Engine connected successfully!")
```

## 📦 Available Commands

| Command | Description |
|---------|-------------|
| `python manage.py runserver` | Start development server |
| `python manage.py migrate` | Run database migrations |
| `python manage.py makemigrations` | Create new migrations |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py collectstatic` | Collect static files |
| `python manage.py shell` | Open Django shell |

## 🏗️ Project Structure

```
JaltolAPI/
├── gee_api/                    # Main API application
│   ├── views.py               # API endpoints
│   ├── models.py              # Database models
│   ├── serializers.py         # DRF serializers
│   ├── urls.py                # URL routing
│   ├── authentication_views.py # Auth endpoints
│   ├── google_auth.py         # Google OAuth integration
│   └── ee_processing.py       # Earth Engine processing
├── my_gee_backend/            # Django project settings
│   ├── settings.py            # Main settings
│   ├── urls.py                # Root URL configuration
│   └── wsgi.py                # WSGI configuration
├── creds/                     # Credentials directory
│   └── *.json                 # Service account keys
├── staticfiles/               # Static files
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management script
├── .env                       # Environment variables
└── db.sqlite3                 # SQLite database (dev)
```

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/google-login/` - Google OAuth login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token

### Geographic Data
- `GET /api/states/` - List all states
- `GET /api/districts/{state_id}/` - List districts by state
- `GET /api/subdistricts/{district_id}/` - List subdistricts
- `GET /api/villages/{subdistrict_id}/` - List villages
- `GET /api/get_boundary_data/` - Get boundary GeoJSON
- `GET /api/get_village_details/` - Get village details

### Earth Engine Analysis
- `GET /api/get_lulc_raster/` - Get LULC raster tiles
- `GET /api/get_area_change/` - Get area change analysis
- `GET /api/get_rainfall_data/` - Get rainfall data
- `GET /api/get_control_village/` - Get control village
- `POST /api/custom_polygon_comparison/` - Compare custom polygons

### Project Management
- `GET /api/projects/` - List user projects
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}/` - Get project details
- `PUT /api/projects/{id}/` - Update project
- `DELETE /api/projects/{id}/` - Delete project

## 🛠️ Development Workflow

### 1. Making Changes

```bash
# Activate virtual environment
.\jaltolvenv\Scripts\Activate.ps1  # Windows
# or
source jaltolvenv/bin/activate      # macOS/Linux

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Test your changes
python manage.py runserver

# Run migrations if models changed
python manage.py makemigrations
python manage.py migrate
```

### 2. Database Management

```bash
# Create new migration
python manage.py makemigrations gee_api

# Apply migrations
python manage.py migrate

# Reset database (development only)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### 3. Testing

```bash
# Run Django tests
python manage.py test

# Test specific app
python manage.py test gee_api

# Test API endpoints manually
curl http://127.0.0.1:8000/api/health/
```

### 4. Pushing Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add: new API endpoint for feature"

# Push to feature branch
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## 🚀 Deployment

### Development Deployment
```bash
# Start development server
python manage.py runserver

# Access at http://127.0.0.1:8000
```

### Production Deployment
```bash
# Install production server
pip install gunicorn

# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn my_gee_backend.wsgi:application --bind 0.0.0.0:8000

# Or use the provided start script
chmod +x start.sh
./start.sh
```

## 🔐 Security Notes

- **Never commit `.env` files** - They contain sensitive credentials
- **Use strong SECRET_KEY** - Generate using Django's get_random_secret_key()
- **Secure credentials directory** - Ensure `creds/` is in `.gitignore`
- **HTTPS only in production** - Update CORS and ALLOWED_HOSTS accordingly
- **Regular key rotation** - Rotate API keys and secrets periodically

## 🐛 Troubleshooting

### Common Issues

1. **Virtual environment activation fails**
   ```powershell
   # Run this first on Windows
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Earth Engine authentication error**
   ```bash
   # Re-authenticate
   earthengine authenticate
   
   # Check credentials file exists
   ls -la ./creds/
   ```

3. **Database migration errors**
   ```bash
   # Reset migrations (development only)
   rm gee_api/migrations/00*.py
   python manage.py makemigrations gee_api
   python manage.py migrate
   ```

4. **Import errors**
   ```bash
   # Ensure virtual environment is activated
   which python  # Should point to jaltolvenv
   
   # Reinstall requirements
   pip install -r requirements.txt
   ```

5. **CORS errors from frontend**
   ```env
   # Add frontend URL to .env
   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```

6. **Google OAuth errors**
   - Verify `GOOGLE_OAUTH2_CLIENT_ID` and `GOOGLE_OAUTH2_CLIENT_SECRET`
   - Check Google Cloud Console OAuth configuration
   - Ensure redirect URLs match

### Getting Help

- Check Django logs in terminal output
- Use Django admin panel at `/admin/`
- Test API endpoints with tools like Postman or curl
- Verify environment variables are loaded correctly

## 📚 Key Features

- **Django REST Framework** - Robust API development
- **Google Earth Engine** - Satellite imagery and geospatial analysis
- **Google OAuth** - Secure authentication
- **JWT Tokens** - Stateless authentication
- **PostgreSQL/SQLite** - Flexible database options
- **CORS Support** - Frontend integration
- **Admin Interface** - Built-in data management

## 🛠️ Tech Stack

- **Django 5.0.1** - Web framework
- **Django REST Framework 3.15.2** - API development
- **Google Earth Engine** - Geospatial analysis
- **PostgreSQL/SQLite** - Database
- **JWT** - Authentication tokens
- **Gunicorn** - Production WSGI server

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Activate virtual environment (`source jaltolvenv/bin/activate`)
4. Install dependencies (`pip install -r requirements.txt`)
5. Set up environment variables (`.env` file)
6. Run migrations (`python manage.py migrate`)
7. Make your changes
8. Test thoroughly (`python manage.py test`)
9. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
10. Push to the branch (`git push origin feature/AmazingFeature`)
11. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Happy coding! 🚀**