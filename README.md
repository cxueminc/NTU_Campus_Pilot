# NTU Navigation App

A comprehensive navigation and facility finder application for Nanyang Technological University.

## Project Structure

```
ntu_nav_app/
├── frontend/          # React Native mobile application
│   ├── app/          # App screens and components
│   ├── assets/       # Images, fonts, and other static assets
│   ├── hooks/        # Custom React hooks
│   ├── lib/          # Utility functions and configurations
│   ├── package.json  # Frontend dependencies
│   └── app.json      # Expo configuration
├── backend/          # FastAPI backend server
│   ├── app/          # API application code
│   │   └── main.py   # Main FastAPI application
│   ├── requirements.txt  # Python dependencies
│   ├── test_api.py   # API tests
│   └── test_constraints.py  # Constraint testing
└── README.md
```

## Frontend (React Native with Expo)

### Setup
```bash
cd frontend
npm install
npx expo start
```

### Features
- Interactive campus map
- Facility search and filtering
- Real-time navigation
- User authentication

## Backend (FastAPI)

### Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Features
- RESTful API for facility data
- Intelligent search with LLM integration
- Constraint-based filtering
- Real-time availability checking
- PostgreSQL database integration

### API Endpoints
- `POST /recommend` - Get facility recommendations based on natural language queries
- Additional endpoints documented in the API

## Development

### Prerequisites
- Node.js and npm (for frontend)
- Python 3.8+ (for backend)
- PostgreSQL database
- Expo CLI (for mobile development)

### Environment Variables
Create `.env` files in both frontend and backend directories with necessary configuration.

## Testing

### Frontend
```bash
cd frontend
npm test
```

### Backend
```bash
cd backend
python test_api.py
python test_constraints.py
```

## Deployment

### Frontend
- Deploy to Expo Application Services (EAS)
- Build APK/IPA for app stores

### Backend
- Deploy to cloud platforms (AWS, GCP, Azure)
- Use Docker for containerization
- Set up PostgreSQL database

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is for educational purposes as part of NTU Final Year Project.