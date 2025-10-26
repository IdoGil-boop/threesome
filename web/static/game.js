// Threesome Web Game - Frontend Logic

class Game {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.gameId = null;
        this.gameState = null;
        this.selectedPiece = null;
        this.skillMode = false;
        this.highlightedSquares = [];
        
        // Canvas sizing
        this.cellSize = 60;
        this.pieceRadius = 20;
        
        this.setupEventListeners();
        this.newGame();
    }
    
    setupEventListeners() {
        document.getElementById('new-game-btn').addEventListener('click', () => this.newGame());
        document.getElementById('toggle-skill-btn').addEventListener('click', () => this.toggleSkillMode());
        document.getElementById('play-again-btn').addEventListener('click', () => this.newGame());
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
    }
    
    async newGame() {
        try {
            const response = await fetch('/api/new_game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    width: 8,
                    height: 8,
                    num_pieces: 3
                })
            });
            const data = await response.json();
            this.gameId = data.game_id;
            this.gameState = data.state;
            this.selectedPiece = null;
            this.skillMode = false;
            this.highlightedSquares = [];
            document.getElementById('winner-overlay').classList.add('hidden');
            this.updateUI();
            this.render();
        } catch (error) {
            console.error('Error creating new game:', error);
            alert('Failed to create new game. Make sure the server is running.');
        }
    }
    
    toggleSkillMode() {
        this.skillMode = !this.skillMode;
        this.selectedPiece = null;
        this.highlightedSquares = [];
        this.updateUI();
        this.render();
    }
    
    async handleCanvasClick(e) {
        if (!this.gameState || this.gameState.winner !== null) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / this.cellSize);
        const y = Math.floor((e.clientY - rect.top) / this.cellSize);
        
        // Check if clicked on a highlighted square
        if (this.selectedPiece && this.highlightedSquares.some(sq => sq[0] === x && sq[1] === y)) {
            await this.makeMove(this.selectedPiece.piece_id, x, y);
            return;
        }
        
        // Check if clicked on a piece
        const clickedPiece = this.gameState.pieces.find(p => p.loc[0] === x && p.loc[1] === y);
        
        if (clickedPiece && clickedPiece.player === this.gameState.turn) {
            this.selectedPiece = clickedPiece;
            await this.updateHighlights();
            this.render();
        } else {
            this.selectedPiece = null;
            this.highlightedSquares = [];
            this.render();
        }
    }
    
    async updateHighlights() {
        if (!this.selectedPiece) {
            this.highlightedSquares = [];
            return;
        }
        
        try {
            const endpoint = this.skillMode ? 'skill_targets' : 'legal_moves';
            const response = await fetch(`/api/game/${this.gameId}/${endpoint}/${this.selectedPiece.piece_id}`);
            const data = await response.json();
            this.highlightedSquares = this.skillMode ? data.targets : data.moves;
        } catch (error) {
            console.error('Error fetching highlights:', error);
            this.highlightedSquares = [];
        }
    }
    
    async makeMove(pieceId, x, y) {
        try {
            const endpoint = this.skillMode ? 'skill_move' : 'move';
            const response = await fetch(`/api/game/${this.gameId}/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    piece_id: pieceId,
                    target_x: x,
                    target_y: y
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                alert(error.detail || 'Invalid move');
                return;
            }
            
            this.gameState = await response.json();
            this.selectedPiece = null;
            this.highlightedSquares = [];
            this.updateUI();
            this.render();
            
            if (this.gameState.winner !== null) {
                this.showWinner();
            }
        } catch (error) {
            console.error('Error making move:', error);
            alert('Failed to make move');
        }
    }
    
    updateUI() {
        if (!this.gameState) return;
        
        document.getElementById('current-turn').textContent = `Player ${this.gameState.turn}`;
        document.getElementById('round').textContent = this.gameState.rounds;
        document.getElementById('mode').textContent = this.skillMode ? 'Skill Mode' : 'Normal';
        
        const skillBtn = document.getElementById('toggle-skill-btn');
        if (this.skillMode) {
            skillBtn.classList.add('active');
        } else {
            skillBtn.classList.remove('active');
        }
        
        // Update skills list
        const skillsList = document.getElementById('skills-list');
        skillsList.innerHTML = '';
        if (this.gameState.color_skills) {
            for (const [color, skill] of Object.entries(this.gameState.color_skills)) {
                const skillItem = document.createElement('div');
                skillItem.className = 'skill-item';
                skillItem.style.borderLeftColor = color;
                skillItem.textContent = `${color}: ${skill}`;
                skillsList.appendChild(skillItem);
            }
        }
    }
    
    showWinner() {
        const overlay = document.getElementById('winner-overlay');
        const text = document.getElementById('winner-text');
        text.textContent = `🎉 Player ${this.gameState.winner} Wins! 🎉`;
        overlay.classList.remove('hidden');
    }
    
    render() {
        if (!this.gameState) return;
        
        const width = this.gameState.width;
        const height = this.gameState.height;
        
        // Resize canvas
        this.canvas.width = width * this.cellSize;
        this.canvas.height = height * this.cellSize;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw color grid
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const color = this.gameState.color_grid[y][x];
                this.ctx.fillStyle = color || '#cccccc';
                this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
                
                // Draw grid lines
                this.ctx.strokeStyle = '#ffffff';
                this.ctx.lineWidth = 1;
                this.ctx.strokeRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
            }
        }
        
        // Draw blocked tiles
        for (const [coord, turns] of Object.entries(this.gameState.blocked_tiles || {})) {
            const [x, y] = coord.split(',').map(Number);
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
            
            // Draw X
            this.ctx.strokeStyle = '#ff0000';
            this.ctx.lineWidth = 3;
            const offset = 10;
            this.ctx.beginPath();
            this.ctx.moveTo(x * this.cellSize + offset, y * this.cellSize + offset);
            this.ctx.lineTo((x + 1) * this.cellSize - offset, (y + 1) * this.cellSize - offset);
            this.ctx.moveTo((x + 1) * this.cellSize - offset, y * this.cellSize + offset);
            this.ctx.lineTo(x * this.cellSize + offset, (y + 1) * this.cellSize - offset);
            this.ctx.stroke();
            
            // Draw turns remaining
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = 'bold 16px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(turns.toString(), (x + 0.5) * this.cellSize, (y + 0.5) * this.cellSize);
        }
        
        // Draw highlights
        for (const [x, y] of this.highlightedSquares) {
            this.ctx.fillStyle = 'rgba(0, 255, 0, 0.4)';
            this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
        }
        
        // Draw selected piece highlight
        if (this.selectedPiece) {
            const [x, y] = this.selectedPiece.loc;
            this.ctx.fillStyle = 'rgba(255, 255, 0, 0.4)';
            this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
        }
        
        // Draw pieces
        for (const piece of this.gameState.pieces) {
            const [x, y] = piece.loc;
            const centerX = (x + 0.5) * this.cellSize;
            const centerY = (y + 0.5) * this.cellSize;
            
            // Draw piece circle with tile color fill
            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY, this.pieceRadius, 0, 2 * Math.PI);
            this.ctx.fillStyle = piece.tile_color || '#888888';
            this.ctx.fill();
            
            // Draw border based on player
            this.ctx.strokeStyle = piece.color || (piece.player === 0 ? 'white' : 'black');
            this.ctx.lineWidth = 4;
            this.ctx.stroke();
            
            // Draw piece ID
            this.ctx.fillStyle = piece.player === 0 ? '#000000' : '#ffffff';
            this.ctx.font = 'bold 14px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(piece.piece_id.toString(), centerX, centerY);
        }
    }
}

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Game();
});

