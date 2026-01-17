# SVA-Chatbot Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (running locally or remote)
- Groq API Key

## Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your:
# - GROQ_API_KEY
# - MONGODB_URL (if not using default localhost)
# - JWT_SECRET_KEY (generate a secure random string)

# Start the backend
bash start_dev.sh
```

Backend will run on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env if needed (defaults should work for local development)

# Start the frontend
npm run dev
```

Frontend will run on `http://localhost:5173`

## First Time Usage

### 1. Register a User

1. Open `http://localhost:5173/login`
2. The backend should already have your user registered:
   - Email: gkt2work@gmail.com
   - Password: Gautam@2
3. Click "Sign in"

### 2. Create a Project

1. Navigate to "Projects" from the navigation menu
2. Click "+ New Project"
3. Enter project name and description
4. Click "Create Project"

### 3. Upload Files

1. From the Projects page, click "Upload Files" on your project
2. Upload specification documents:
   - Supported formats: PDF, DOCX, MD, TXT
   - Max size: 50MB per file
3. Upload RTL design files:
   - Supported formats: .sv, .v
   - Max size: 50MB per file

### 4. Generate Assertions

The AI agents will automatically process your files and generate assertions. You can monitor progress in real-time via WebSocket connection.

### 5. View Assertions

1. From the Projects page, click "View Assertions" on your project
2. Browse generated assertions
3. Click on an assertion to view details:
   - SystemVerilog code
   - Confidence and quality scores
   - Traceability to requirements
   - RTL signals and modules

### 6. Export Assertions

1. On the Assertions page, click "Export All"
2. Download the generated .sv file
3. Integrate into your verification environment

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Projects

- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project
- `DELETE /api/projects/{id}` - Delete project

### File Upload

- `POST /api/projects/{id}/upload-spec` - Upload specification
- `POST /api/projects/{id}/upload-rtl` - Upload RTL file

### Assertions

- `GET /api/assertions/project/{id}` - Get assertions
- `GET /api/projects/{id}/export` - Export assertions

### WebSocket

- `WS /ws/generation/{projectId}` - Real-time updates

## Troubleshooting

### Backend won't start

- Check MongoDB is running: `mongosh` or `mongo`
- Verify GROQ_API_KEY is set in `.env`
- Check port 8000 is not in use

### Frontend won't start

- Run `npm install` again
- Clear node_modules: `rm -rf node_modules && npm install`
- Check port 5173 is not in use

### Can't login

- Check backend is running
- Verify user is registered in MongoDB
- Check browser console for errors
- Clear localStorage and try again

### File upload fails

- Check file size (max 50MB)
- Verify file type is supported
- Check backend logs for errors
- Ensure project ID is valid

### No assertions generated

- Check backend logs for processing errors
- Verify Groq API key is valid
- Check MongoDB for stored data
- Monitor WebSocket connection for status updates

## Development Tips

### Backend Development

- Logs are in `backend/server.log`
- Use `--reload` flag for auto-restart on code changes
- MongoDB data is in `sva_chatbot` database

### Frontend Development

- Hot reload is enabled by default
- Check browser console for errors
- Use React DevTools for debugging
- Network tab shows API calls

### Testing

- Backend tests: `cd backend && pytest`
- Frontend tests: `cd frontend && npm test`

## Production Deployment

See `DEPLOYMENT.md` for production deployment instructions.

## Support

For issues or questions:

1. Check logs (backend/server.log)
2. Check browser console
3. Verify environment variables
4. Review API documentation in `docs/API.md`
