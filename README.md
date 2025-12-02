# Equipment Condition Tracker

## Mackenzie Kleczynski etm8nu

A Flask-based web application for tracking the condition of borrowed equipment through photo documentation and MongoDB data management.

---

## 1) Executive Summary

**Problem:** The Contemplative Commons at UVA is launching a new equipment checkout initiative to support mind-body practices and community engagement. Students, faculty, and community members can borrow items like yoga mats for practice spaces or home use, binoculars for bird watching by the pond, and extension cords or chargers for studying in the building. Previously, equipment like yoga mats couldn't leave designated rooms, limiting access to contemplative practices. With the new checkout system in place, we needed a way for staff to document equipment condition when items are returned to ensure accountability, tracking wear and tear over time, and protecting against unreported damages.

**Solution:** I built a web app where staff members log in with a unique 4-digit PIN, upload photos of returned equipment, and mark whether items condition are "Clear" or "Damaged." All the information like employee names, timestamps, photos, and condition status gets saved to MongoDB so managers can track patterns and trends over time. The photos live on the server, and the metadata lives in the database.

---

## 2) System Overview

### Course Concept(s)

This project uses concepts from **DS 2022 - Systems I: Intro to Computing**:

- **Flask Web Framework (RESTful API):** Multiple routes (GET/POST), session management for user authentication, form data processing, file uploads, and template rendering with Jinja2
- **MongoDB (NoSQL Database):** Two collections (`employees` and `uploads`), CRUD operations, query operators for filtering, and cloud-hosted via MongoDB Atlas
- **Docker Containerization:** Reproducible build environment with Python 3.11, Flask, PyMongo, and all dependencies packaged in a single container
- **Environment Variables & Secrets Management:** MongoDB URI and Flask secret key stored in `.env` file (excluded from Git), loaded at runtime
- **File Storage & Organization:** Photos organized hierarchically by equipment type with secure filename handling to prevent directory traversal attacks

### Architecture Diagram

![System Architecture Diagram](assets/architecture-diagram.png)

**System Flow:**

The diagram shows three layers working together. When a staff member logs in, they enter a PIN that Flask checks against the MongoDB `employees` collection. After login, they can upload a photo and mark whether the equipment is in good condition or damaged. Flask saves the actual photo file to the local `/photos` directory and stores all the metadata (who uploaded it, when, what condition it was in) in MongoDB. When staff view the gallery, Flask pulls the metadata from MongoDB and serves the photo files from the filesystem.

### Data/Models/Services

**Data Sources:**

1. **Example Employee Credentials** (3 test accounts)
   - Mackenzie (PIN: 1234)
   - Lucy (PIN: 5678)
   - Staff Member (PIN: 9999)
   - Stored in MongoDB `employees` collection with `_id`, `name`, and `pin` fields

2. **Upload Metadata**
   - Grows with each upload
   - Stored in MongoDB `uploads` collection
   - Fields: `item`, `condition` ("Clear" or "Damaged"), `employee_name`, `employee_id`, `filename`, `filepath`, `uploaded_at`

3. **Photo Files**
   - User-uploaded images (JPEG, PNG, GIF)
   - Stored locally in `photos/{item-name}/{timestamp}-{filename}` format
   - Typically 100KB - 5MB per photo

**External Services:**

- **MongoDB Atlas** (Free M0 Tier) - Cloud-hosted NoSQL database
- **Docker Desktop** - Container runtime for reproducible deployment

**Code Attribution:**

This project was developed with assistance from Claude (Anthropic AI) for Flask routes, MongoDB integration, HTML/CSS templates, Docker configuration, and debugging. All code was reviewed and customized for this specific use case. The problem identification, requirements, and feature design are my original work.

---

## 3) How to Run (Local)

### Prerequisites

- Docker Desktop installed and running
- MongoDB Atlas account with connection string (free tier available)

### Docker Setup

**Build the image:**
```bash
docker build -t equipment-tracker:latest .
```

**Run the container:**
```bash
docker run --rm -p 4321:5000 \
  -e MONGODB_URI="mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/equipment_tracker?retryWrites=true&w=majority" \
  -e SECRET_KEY="your-random-secret-key-here" \
  equipment-tracker:latest flask --app app run --host=0.0.0.0 --port=5000
```

**Health check:**
```bash
curl http://localhost:4321/health
```

Expected response: `{"status":"ok","message":"Equipment Tracker is running"}`

### Manual Setup (without Docker)

1. **Clone the repository:**
```bash
git clone https://github.com/kenzkleczynski/equipment-tracker.git
cd equipment-tracker
```

2. **Create `.env` file:**
```bash
cp .env.example .env
```

Edit `.env` with your MongoDB credentials:
```
MONGODB_URI=mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/equipment_tracker
SECRET_KEY=change-this-to-random-string
```

3. **Install dependencies:**
```bash
pip3 install Flask pymongo python-dotenv
```

4. **Seed employee test data (optional):**
```bash
python3 setup_employees.py
```

This creates three test employees. You can then log in with PIN 1234 (Mackenzie), 5678 (Lucy), or 9999 (Staff Member).

5. **Run locally:**
```bash
python3 app.py
```

6. **Access the app:**
```
http://localhost:4321
```

---

## 4) Design Decisions

### Why This Stack?

I chose Flask, MongoDB, and Docker because the project needed three things: user authentication, the ability to query and filter data, and a way to run the same code on any computer without installation headaches. Flask handles the web server and sessions, MongoDB lets me organize equipment uploads and filter by condition or date, and Docker packages everything so anyone can run it without installing Python or downloading libraries.

### Alternatives I Considered

- **Static HTML + file storage:** Wouldn't work because there's no way to query data or prevent unauthorized access
- **SQL database:** MongoDB was better here because the metadata schema might evolve (adding notes, damage descriptions, etc.) and NoSQL handles that more flexibly

### Tradeoffs

**Performance:** MongoDB queries run and photo uploads finish in under 1 second, which is fast enough for staff using it during their shifts. I didn't add caching because the data set is small.

**Cost:** MongoDB Atlas M0 (free tier) gives enough storage for a few hundred photos. If I scaled up, I would most likely need to pay.

**Complexity:** Docker makes deployment easy but requires one extra command to run. The alternative would be manually installing Python, Flask, and PyMongo on each computer, which is error-prone.

**Maintainability:** The code is organized into routes in `app.py`, templates in a `templates/` folder, and photos in a `photos/` directory. No testing suite, so there's risk of bugs.

### Security & Privacy

**Secrets:** MongoDB URI and Flask SECRET_KEY are in `.env`, which is gitignored so they never hit GitHub. When running Docker, these get passed in via `-e` flags.

**File validation:** Only JPEG, PNG, and GIF are allowed. Filenames get sanitized with Werkzeug's `secure_filename()` to prevent directory traversal attacks (like someone uploading `../../etc/passwd`).

**Authentication:** The 4-digit PIN system is simple and works for an internal tool. In production, I'd add bcrypt hashing and rate limiting after failed attempts.

**Data:** I don't collect any sensitive personal info beyond employee names. PINs are stored in plaintext which is fine for this low-security internal tool.

### Ops & Scaling

**Current scope:** This was built for a small team at the Contemplative Commons. It stores uploads in MongoDB and photos on the local filesystem. For a larger deployment, I'd migrate photos to Azure Blob Storage.

**Known limitations:** Photos are stored locally, so if the server crashes, they're lost. There's no automated backup.

---

## 5) Results & Evaluation

### Screenshots

**Login Page**

![Login Page](assets/Login.png)

Staff enters their 4-digit PIN here. The form validates against MongoDB.

**Invalid PIN**

![Invalid PIN](assets/Invalid_Pin.png)

When an incorrect PIN is entered, the app shows an error message and redirects back to login.

**Home Page**

![Home Page](assets/Home.png)

After successful login, staff see the home page with two options: upload a photo or view the gallery.

**Upload Page**

![Upload Page](assets/Upload.png)

Staff select the equipment type from a dropdown, choose whether it's in good condition or damaged, and upload a photo.

**Gallery - Select Item**

![Gallery Select](assets/Gallery_Select.png)

Before viewing photos, staff choose which item type they want to see (yoga mat, binoculars, foam roller, etc.).

**Gallery - Yoga Mats**

![Gallery Yoga Mats](assets/Gallery_YogaMat.png)

The gallery displays all uploaded photos for the selected item in a 3-column grid. Each photo shows the employee who uploaded it, the timestamp, and a badge indicating whether it's in "Clear" or "Damaged" condition.

**Gallery - Binoculars**

![Gallery Binoculars](assets/Gallery_Binoculars.png)

Another example of the gallery view with multiple equipment types showing different condition statuses.

**Database - Employees Collection**

![Employees Collection](assets/DB_employees.png)

This shows the MongoDB `employees` collection with the three test accounts (Mackenzie, Lucy, Staff Member) and their PINs.

**Database - Uploads Collection**

![Uploads Collection](assets/DB_uploads.png)

This shows the MongoDB `uploads` collection with metadata for each uploaded photo: item type, condition status, employee name, filename, filepath, and timestamp.

### Testing & Validation

**I manually tested everything that matters:**

1. **Login flow:** Valid PIN (1234) -> successful login . Invalid PIN (0000) -> error message . Accessing protected routes without login -> redirected to login 

2. **Photo upload:** Upload JPEG with "Clear" condition -> photo appears in gallery . Upload PNG with "Damaged" condition -> red badge displays . Try uploading PDF -> rejected with error 

3. **Gallery:** Empty gallery shows "No photos yet" . Gallery with 4+ photos displays in 3-column grid . Photos sorted newest-first 

4. **MongoDB queries:** 
   - Query: `db.uploads.find({condition: "Damaged"})` -> returns only damaged items 
   - Query: `db.uploads.aggregate([{$group: {_id: "$employee_name", count: {$sum: 1}}}])` -> shows upload counts per employee 

**Sample MongoDB data:**

```json
{
  "_id": "692b11cb920a20211b61bd9e",
  "item": "Yoga Mat",
  "condition": "Clear",
  "employee_name": "Mackenzie",
  "employee_id": "692b0ed40e6208b0e458d10b",
  "filename": "20251201-153123-IMG_1911.jpeg",
  "filepath": "photos/yoga-mat/20251201-153123-IMG_1911.jpeg",
  "uploaded_at": "2025-12-01T15:31:23.801Z"
}
```

---

## 6) What's Next

### Features I'd Add

- **Notes field:** Let staff add text descriptions of damage beyond just "Clear" or "Damaged"
- **Email alerts:** Auto-notify managers when an item is marked damaged
- **Before/after photos:** Show how an item's condition changes over time
- **Barcode scanning:** Scan equipment barcodes to auto-populate the item field
- **CSV export:** Download upload data for analysis in Excel or Tableau

### Infrastructure Improvements

- **Cloud deployment:** Deploy to Azure App Service so managers can access it from anywhere
- **Automated backups:** Daily backups to Azure Blob Storage
- **Database migrations:** Add a framework (like MongoDB Migrate) for versioning schema changes
- **Role-based access:** Separate permissions for staff (upload only) vs. managers (query and delete access)

### Code Quality

- **Unit tests:** Add pytest tests for Flask routes and MongoDB queries
- **CI/CD:** Set up GitHub Actions to run tests on every commit
- **Error handling:** Add middleware to catch and log all exceptions
- **Photo storage:** Migrate from local filesystem to Azure Blob Storage for multi-server support

### Analytics Dashboard

- **Visualizations:** Charts showing uploads per day, damage rate by item, most active staff members
- **Trends:** Equipment lifecycle timelines showing condition changes
- **Reports:** Weekly automated reports to managers summarizing equipment status

---

## 7) Links

- **GitHub Repo:** https://github.com/kenzkleczynski/equipment-tracker
- **Public Cloud App:** Not deployed (local development only)

---

## License

MIT License - See `LICENSE` file for details.

**Built for DS 2022 - Systems I: Intro to Computing, University of Virginia**