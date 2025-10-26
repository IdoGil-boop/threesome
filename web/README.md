# Threesome Web Version

Play Threesome in your browser!

## Quick Start

1. **Install dependencies:**
```bash
cd /Users/idogil/threesome
source venv/bin/activate
pip install -r requirements.txt
```

2. **Run the server:**
```bash
cd web
python server.py
```

3. **Open your browser:**
Navigate to http://localhost:8000

## Architecture

- **Backend:** FastAPI server wraps the existing game logic
- **Frontend:** HTML5 Canvas with vanilla JavaScript
- **API:** REST endpoints for game state and moves

## API Endpoints

- `POST /api/new_game` - Create new game session
- `GET /api/game/{game_id}` - Get game state
- `POST /api/game/{game_id}/move` - Make normal move
- `POST /api/game/{game_id}/skill_move` - Make skill move
- `GET /api/game/{game_id}/legal_moves/{piece_id}` - Get legal moves
- `GET /api/game/{game_id}/skill_targets/{piece_id}` - Get skill targets
- `DELETE /api/game/{game_id}` - Delete game session

## Deployment

### Local Network
```bash
# Other devices on your network can access via your IP
python server.py
# Then visit http://YOUR_IP:8000 from other devices
```

### Production (e.g., Railway, Heroku, DigitalOcean)

1. Create `Procfile`:
```
web: cd web && uvicorn server:app --host 0.0.0.0 --port $PORT
```

2. Deploy to platform of choice

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "web.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Features

✅ Full game logic preserved from original
✅ Beautiful modern UI
✅ Canvas-based rendering
✅ Responsive design
✅ Real-time game state updates
✅ Normal and skill modes
✅ Winner detection
✅ Mobile-friendly

## Future Enhancements

- [ ] WebSocket for real-time multiplayer
- [ ] Game lobby/matchmaking
- [ ] Player accounts and stats
- [ ] Replay system
- [ ] AI opponent integration
- [ ] Custom board configurations via UI

