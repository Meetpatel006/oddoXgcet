# Dayflow HRMS

Dayflow is a comprehensive Human Resource Management System designed to streamline employee management, attendance tracking, and leave management.

## Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: SQLite (via [SQLAlchemy](https://www.sqlalchemy.org/))
- **Language**: Python 3.9+

### Frontend
- **Framework**: [Next.js 16](https://nextjs.org/) (App Directory)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **UI Components**: [Radix UI](https://www.radix-ui.com/), [Lucide React](https://lucide.dev/)

## Project Structure

- `backend/`: Contains the FastAPI application code, database models, and API endpoints.
- `frontend/`: Contains the Next.js frontend application.

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   # Assuming requirements.txt exists, otherwise install manually
   pip install fastapi uvicorn sqlalchemy python-multipart python-jose[cryptography] passlib[bcrypt]
   ```

4. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   bun install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   The application will be available at `http://localhost:3000`.

## Features

- **Employee Management**: Manage employee profiles and details.
- **Attendance**: Track employee check-ins and check-outs.
- **Leave Management**: Manage leave requests and balances.
- **Authentication**: Secure login for Admin, HR, and Employees.
