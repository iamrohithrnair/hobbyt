# Hobbyt – Gemini Repository Analyzer with Robotics Project Generator

A powerful FastAPI-based application that combines repository analysis with AI-powered robotics project generation using Google Gemini and the Agent Development Kit (ADK).

## Features

### 1. Repository Analysis
- Real-time code analysis using Google ADK agent
- Live updates via polling endpoint
- Comprehensive insights on architecture, hardware mapping, and risks

### 2. Robotics Project Generator
- **AI-Powered Generation**: Uses Google Gemini (`gemini-3.1-flash-lite`)
- **Plain English Input**: Describe your project in natural language
- **Complete Project Output**: 
  - Folder structure
  - Pin wiring diagrams
  - Starter code (Arduino/Python)
  - Comprehensive README documentation

## Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 16+ (for frontend)
- Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### Backend Setup

1. **Clone and Navigate**
   ```bash
   cd backend
   ```

2. **Create Virtual Environment**
   ```bash
   uv venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your Google Gemini credentials:
   ```env
   GEMINI_API_KEY=your_api_key
   GEMINI_MODEL_ID=gemini-3.1-flash-lite
   ```

5. **Start the Server**
   ```bash
   python main.py
   ```
   
   Server runs on `http://localhost:8000`

### Frontend Setup

1. **Navigate to Frontend**
   ```bash
   cd frontend
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```
   
   Frontend runs on `http://localhost:5173`

## API Endpoints

### Repository Analysis

#### `POST /analyze`
Upload a repository file for analysis.

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@repository.zip"
```

#### `GET /live-updates`
Poll for real-time analysis updates from the Gemini agent.

**Response:**
```json
{
  "metadata": {
    "engine": "Google Gemini (ADK Agent)",
    "timestamp": 1715863200,
    "status": "success"
  },
  "insights": {
    "architecture": {...},
    "hardware_mapping": {...},
    "control_flow": {...},
    "risks": [...]
  }
}
```

#### `GET /status`
Check server status and capabilities.

### Robotics Project Generator

#### `POST /generate`
Generate a complete robotics project from a plain English description.

**Request:**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Arduino Uno, 2 DC motors, IR sensor, line follower"
  }'
```

**Response:**
```json
{
  "folder_structure": {
    "line_follower_robot": {
      "src": ["main.ino"],
      "lib": ["motor_control.h", "ir_sensor.h"],
      "docs": ["wiring_diagram.md"],
      "examples": ["calibration.ino"]
    }
  },
  "pin_wiring": {
    "motor_left": {
      "pwm": "5",
      "dir1": "6",
      "dir2": "7",
      "description": "Left DC motor connected to L298N"
    },
    "ir_sensor_left": {
      "signal": "A0",
      "vcc": "5V",
      "gnd": "GND"
    }
  },
  "starter_code": "// Complete Arduino code with comments...",
  "readme": "# Line Follower Robot\n\n## Description..."
}
```

**Example Descriptions:**
- `"Arduino Uno, 2 DC motors, IR sensor, line follower"`
- `"Raspberry Pi 4, servo motor, ultrasonic sensor, obstacle avoidance"`
- `"ESP32, DHT22 sensor, OLED display, WiFi weather station"`
- `"Arduino Mega, 6 servo motors, joystick, robotic arm"`

## Project Structure

```
Hobbyt/
├── backend/
│   ├── main.py              # FastAPI application with /generate endpoint
│   ├── gemini_service.py    # Google ADK agent and tool definitions
│   ├── requirements.txt     # Python dependencies
│   └── .venv/              # Virtual environment
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   └── main.jsx        # Entry point
│   ├── public/             # Static assets
│   └── package.json        # Node dependencies
├── docs/
│   ├── example_response.json           # Repository analysis example
│   ├── generate_example_response.json  # Robotics generation example
│   └── test_generate_endpoint.md       # Testing guide
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore rules
├── setup.sh               # macOS/Linux setup script
├── setup.bat              # Windows setup script
└── README.md              # This file
```

## Google Gemini Integration

### Getting Your API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" → "Create API Key"
4. Copy and save the key securely

### Model Selection

- **Default**: `gemini-3.1-flash-lite` — fast and cost-effective
- **Alternatives**: `gemini-2.5-flash`, `gemini-2.5-pro` (higher quality, slower)
- Set via `GEMINI_MODEL_ID` in your `.env` file

## Testing

### Interactive API Documentation
Visit `http://localhost:8000/docs` for Swagger UI with interactive testing.

### Manual Testing
See `docs/test_generate_endpoint.md` for detailed testing instructions.

### Example Test Script
```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={"description": "Arduino Uno, 2 DC motors, IR sensor, line follower"}
)

print(response.json())
```

## Development

### Adding New Features

1. **New Endpoint**: Add to `backend/main.py`
2. **New Model**: Define Pydantic models for request/response
3. **Frontend Integration**: Update `frontend/src/App.jsx`

### Code Style
- Python: Follow PEP 8
- JavaScript: ESLint configuration in `frontend/eslint.config.js`
- Use async/await for consistency

### Environment Variables
Never commit `.env` files. Always use `.env.example` as a template.

## Troubleshooting

### Backend Issues

**Import errors for google-genai:**
```bash
uv pip install --upgrade google-genai google-adk
```

**Environment variables not loading:**
- Ensure `.env` is in the project root (not in `backend/`)
- Check file permissions
- Verify `python-dotenv` is installed

**API authentication errors:**
- Verify API key is correct at [Google AI Studio](https://aistudio.google.com/)
- Ensure the model ID is valid

### Frontend Issues

**CORS errors:**
- Backend CORS is configured for all origins (`allow_origins=["*"]`)
- For production, restrict to specific domains

**Connection refused:**
- Ensure backend is running on port 8000
- Check firewall settings

## Production Deployment

### Backend
```bash
# Use production ASGI server
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Frontend
```bash
npm run build
# Serve the dist/ folder with nginx or similar
```

### Environment
- Use proper secrets management (Google Secret Manager, etc.)
- Enable HTTPS
- Add rate limiting
- Implement authentication

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: See `docs/` folder
- **API Docs**: http://localhost:8000/docs
- **Issues**: Open an issue on GitHub

## Acknowledgments

- Google Gemini for AI capabilities
- Google Agent Development Kit (ADK) for agent orchestration
- FastAPI for the excellent web framework
- React for the frontend framework

---

**Made with ❤️ using Google Gemini and FastAPI**