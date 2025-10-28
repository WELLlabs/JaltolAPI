# JaltolAPI - Backend Architecture Overview

## 🎯 **What is JaltolAPI?**

JaltolAPI is a **Django REST API backend** that serves as the brain of the Jaltol platform. Think of it as a powerful server that processes requests from the frontend (the user interface) and provides geospatial analysis, user management, and project management capabilities.

**In simple terms:** It's like a smart assistant that takes your requests (like "show me rainfall data for this village") and returns processed information (like charts and maps).

---

## 🏗️ **Core Architecture Components**

### **1. Django Framework (The Foundation)**
- **What it is:** A Python web framework that handles HTTP requests and responses
- **Simple explanation:** Like the foundation of a house - it provides the basic structure for building web applications
- **Why Django:** It's robust, secure, and has built-in features for user authentication, database management, and API creation

### **2. REST API (The Communication Layer)**
- **What it is:** A set of rules for how the frontend and backend communicate
- **Simple explanation:** Like a waiter in a restaurant - the frontend (customer) makes requests, and the API (waiter) brings back the requested data
- **How it works:** Uses HTTP methods (GET, POST, PUT, DELETE) to perform different operations

### **3. PostgreSQL Database (The Memory)**
- **What it is:** A relational database that stores all the application data
- **Simple explanation:** Like a digital filing cabinet that stores user information, project data, and geographic boundaries
- **Current setup:** Uses AWS RDS PostgreSQL instance for production data

---

## 🌍 **Geographic Data Management**

### **Hierarchical Geographic Structure**
The API manages India's administrative boundaries in a tree-like structure:

```
India
├── States (e.g., Maharashtra, Karnataka)
│   ├── Districts (e.g., Pune, Mumbai)
│   │   ├── Subdistricts (e.g., Talukas)
│   │   │   └── Villages (e.g., Individual villages)
```

**Models (Database Tables):**
- **State:** Stores state information
- **District:** Links to states, stores district data
- **SubDistrict:** Links to districts, stores subdistrict data  
- **Village:** Links to subdistricts, stores village data with Census IDs

**Simple explanation:** Like organizing files in folders - States are the main folders, Districts are subfolders, and Villages are individual files.

---

## 🛰️ **Google Earth Engine Integration**

### **What is Google Earth Engine?**
- **Technical:** Google's cloud-based platform for planetary-scale geospatial analysis
- **Simple explanation:** A massive computer in the cloud that can process satellite imagery and geographic data from around the world
- **Why use it:** It has petabytes of satellite data and powerful processing capabilities that would be impossible to run on a regular computer

### **Key Earth Engine Features in JaltolAPI:**

#### **1. Land Use Land Cover (LULC) Analysis**
- **What it does:** Analyzes what type of land cover exists in an area (forest, agriculture, urban, etc.)
- **Data sources:** IndiaSAT, FarmBoundary, Bhuvan datasets
- **Simple explanation:** Like looking at a satellite photo and identifying what's in each pixel - is it a forest, farmland, or city?

#### **2. Rainfall Analysis**
- **What it does:** Provides historical rainfall data for specific locations
- **Data source:** IMD (Indian Meteorological Department) precipitation data
- **Simple explanation:** Like a weather station that records how much it rained each year in a specific village

#### **3. Elevation and Terrain Analysis**
- **What it does:** Provides elevation data and slope calculations
- **Data source:** SRTM (Shuttle Radar Topography Mission) dataset
- **Simple explanation:** Like a topographic map that shows how high or low the land is and how steep the slopes are

#### **4. Village Comparison**
- **What it does:** Compares villages based on terrain characteristics
- **Simple explanation:** Like finding villages with similar landscape features for comparison studies

---

## 👥 **User Management & Authentication**

### **Authentication System**
- **JWT (JSON Web Tokens):** Secure way to identify users without storing passwords
- **Google OAuth:** Allows users to sign in with their Google accounts
- **Simple explanation:** Like a digital ID card that proves who you are when you use the system

### **User Roles & Plans**
- **Member Model:** Extended user profile with organization, role, and plan information
- **Plan System:** Different subscription levels with varying features
- **Simple explanation:** Like having different membership levels at a gym - basic, premium, etc.

### **Profile Management**
- **Profile Setup:** Users can set up their profiles with organization details
- **Profile Skipping:** Users can skip profile setup and complete it later
- **Simple explanation:** Like filling out a form about yourself when you join a service

---

## 📊 **Project Management**

### **Project System**
- **Project Model:** Stores user projects with metadata
- **Project CRUD:** Create, Read, Update, Delete operations
- **Simple explanation:** Like having a personal workspace where you can save and organize your analysis projects

---

## 🔧 **Technical Components**

### **Key Python Packages:**
- **Django:** Web framework
- **Django REST Framework:** API development
- **Google Earth Engine API:** Geospatial analysis
- **PostgreSQL (psycopg2):** Database connectivity
- **JWT:** Token-based authentication
- **CORS:** Cross-origin resource sharing for frontend communication

### **API Endpoints Structure:**
```
/api/
├── auth/           # User authentication
├── states/         # Geographic data
├── districts/
├── subdistricts/
├── villages/
├── projects/       # Project management
├── get_lulc_raster/    # Earth Engine analysis
├── get_rainfall_data/
├── get_srtm_raster/
└── custom_polygon_comparison/
```

---

## 🌐 **Environment Variables & Configuration**

### **Why Environment Variables Matter:**
Environment variables are like settings that tell the application how to behave in different environments (development, testing, production).

### **Key Environment Variables:**
- **SECRET_KEY:** Django's cryptographic key (like a master password)
- **DEBUG:** Whether to show detailed error messages (True for development, False for production)
- **DATABASE_*:** Database connection settings
- **GOOGLE_EARTH_ENGINE_API_KEY:** Access to Google Earth Engine
- **GOOGLE_OAUTH2_*:** Google Sign-In credentials

### **Simple explanation:** Like having different settings for your phone when you're at home vs. at work - same device, different configurations.

---

## 🔄 **Data Flow Example**

Here's how a typical request flows through the system:

1. **Frontend Request:** User clicks "Show rainfall data for Village X"
2. **API Receives:** Django receives the HTTP request
3. **Authentication:** System checks if user is logged in
4. **Geographic Lookup:** System finds the village in the database
5. **Earth Engine Processing:** System queries Google Earth Engine for rainfall data
6. **Data Processing:** System processes and formats the data
7. **Response:** System sends the data back to the frontend
8. **Frontend Display:** User sees rainfall charts and maps

**Simple explanation:** Like ordering food at a restaurant - you make a request, the kitchen (Earth Engine) prepares it, and the waiter (API) brings it to your table (frontend).

---

## 🚀 **Deployment & Scaling**

### **Current Setup:**
- **Backend:** Django on Google Cloud Platform
- **Database:** AWS RDS PostgreSQL
- **Frontend:** Vercel (separate deployment)
- **Earth Engine:** Google Cloud (serverless)

### **Why This Architecture:**
- **Scalable:** Can handle many users simultaneously
- **Reliable:** Multiple services ensure uptime
- **Cost-effective:** Pay only for what you use
- **Secure:** Each component has its own security measures

---

## 🎯 **Summary**

JaltolAPI is essentially a **geospatial data processing engine** that:

1. **Manages users** and their projects
2. **Processes geographic data** using Google Earth Engine
3. **Provides analysis tools** for land use, rainfall, and terrain
4. **Serves data** to the frontend in a structured format
5. **Handles authentication** and user management

**In one sentence:** It's a smart backend that takes geographic requests, processes them using satellite data, and returns meaningful insights about land and water resources in India.

The environment variables are crucial because they allow the same codebase to work in different environments (your local computer vs. the production server) with different settings for security, database connections, and external service access.



