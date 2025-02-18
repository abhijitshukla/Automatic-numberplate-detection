# Automatic Number Plate Detection

## Overview
This project is an **Automatic Number Plate Detection System** that utilizes **YOLOv8** for object detection and **PaddleOCR** for optical character recognition (OCR). Detected license plate numbers are sent to a **FastAPI** backend, which stores them in a **MySQL database** with timestamps.

## Features
- **Real-time license plate detection** using YOLOv8.
- **OCR-based number plate recognition** with PaddleOCR.
- **FastAPI server for database storage** (MySQL).
- **Timestamps for every detected plate.**
- **Environment variables** for secure database configuration.

## Technologies Used
- **Python** (Core programming language)
- **OpenCV** (Image processing)
- **YOLOv8 (Ultralytics)** (License plate detection)
- **PaddleOCR** (Text recognition)
- **FastAPI** (Backend API for database storage)
- **MySQL** (Database for storing detected plates)
- **Uvicorn** (ASGI server for FastAPI)
- **Requests** (Sending data to the backend)
- **CVZone** (Visualization tools)
- **python-dotenv** (Environment variable management)

## Installation
### Prerequisites
Ensure you have the following installed on your system:
- **Python 3.x**
- **MySQL** (Ensure MySQL is running and accessible)

### Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone <repo_link>
   cd <repo_name>
   ```

2. **Install Required Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Create a `.env` file in the root directory and add the following:
   ```env
   DB_HOST=127.0.0.1
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=numberplate
   DB_PORT=3306
   ```
   > ⚠ **Important:** Replace `your_mysql_password` with your actual MySQL root password.

4. **Configure MySQL Database**
   - Ensure MySQL is running.
   - The database will be automatically created if it does not exist.
   - Modify `server.py` if you need to change database configurations.

## Running the Project
### Step 1: Start the FastAPI Server
Run the following command to start the FastAPI backend:
```bash
python server.py
```
This will start the server on `http://127.0.0.1:8000`.

### Step 2: Run the License Plate Detection
Once the FastAPI server is running, execute the following command to start the number plate detection:
```bash
python main.py
```

## API Endpoints
| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/store_plate/` | Stores detected plate number in MySQL with timestamp |
| `GET`  | `/plates/` | Retrieves all stored number plates |

## File Structure
```
├── main.py                 # Number plate detection & OCR
├── server.py               # FastAPI backend for MySQL storage
├── .env                    # Environment variables (database credentials)
├── requirements.txt        # Required dependencies
├── license_plate_detector.pt # YOLOv8 model for plate detection
├── coco1.txt               # Class names for YOLO model
├── .gitignore              # Ignore __pycache__ files
```

## Notes
- Modify `server.py` for custom database configurations.
- Ensure the `.env` file is properly configured before running the project.
- `main.py` reads video from `sample/sample.mp4`. Update it for a different input source.

## License
This project is open-source and available under the **MIT License**.

