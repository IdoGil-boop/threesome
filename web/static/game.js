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
        this.selectedOpponent = null;  // For move opponent skill
        this.aiEnabled = true;  // AI enabled by default
        this.aiPlayer = 1;      // AI plays as Player 1
        this.aiThinking = false;
        
        // Canvas sizing
        this.cellSize = 60;
        this.pieceRadius = 20;
        
        this.setupEventListeners();
        this.newGame();
    }
    
    setupEventListeners() {
        document.getElementById('new-game-btn').addEventListener('click', () => this.newGame());
        document.getElementById('toggle-skill-btn').addEventListener('click', () => this.toggleSkillMode());
        document.getElementById('toggle-ai-btn').addEventListener('click', () => this.toggleAI());
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
                    num_pieces: 3,
                    ai_enabled: this.aiEnabled,
                    ai_player: this.aiPlayer,
                    ai_depth: 3
                })
            });
            const data = await response.json();
            this.gameId = data.game_id;
            this.gameState = data.state;
            this.selectedPiece = null;
            this.skillMode = false;
            this.highlightedSquares = [];
            this.aiThinking = false;
            document.getElementById('winner-overlay').classList.add('hidden');
            this.updateUI();
            this.render();
        } catch (error) {
            console.error('Error creating new game:', error);
            alert('Failed to create new game. Make sure the server is running.');
        }
    }
    
    async toggleSkillMode() {
        this.skillMode = !this.skillMode;
        this.selectedOpponent = null;  // Clear opponent selection
        // Keep piece selected, just update highlights
        if (this.selectedPiece) {
            await this.updateHighlights();
        }
        this.updateUI();
        this.render();
    }
    
    toggleAI() {
        this.aiEnabled = !this.aiEnabled;
        this.updateUI();
    }
    
    async handleCanvasClick(e) {
        if (!this.gameState || this.gameState.winner !== null || this.aiThinking) return;
        
        // Don't allow human to move if it's AI's turn
        if (this.aiEnabled && this.gameState.turn === this.aiPlayer) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / this.cellSize);
        const y = Math.floor((e.clientY - rect.top) / this.cellSize);
        
        const clickedPiece = this.gameState.pieces.find(p => p.loc[0] === x && p.loc[1] === y);
        
        // Handle move opponent skill
        if (this.skillMode && this.opponentTargets && this.selectedPiece) {
            if (!this.selectedOpponent) {
                // First click: select opponent piece
                if (clickedPiece && clickedPiece.player !== this.gameState.turn) {
                    // Check if this opponent is in our targets
                    const isValidOpponent = this.opponentTargets.some(([pid, _]) => pid === clickedPiece.piece_id);
                    if (isValidOpponent) {
                        this.selectedOpponent = clickedPiece;
                        await this.updateHighlights();
                        this.render();
                        return;
                    }
                }
            } else {
                // Second click: select destination
                if (this.highlightedSquares.some(sq => sq[0] === x && sq[1] === y)) {
                    await this.makeMoveOpponentSkill(this.selectedPiece.piece_id, this.selectedOpponent.piece_id, x, y);
                    return;
                }
                // Click on different opponent to switch selection
                if (clickedPiece && clickedPiece.player !== this.gameState.turn) {
                    const isValidOpponent = this.opponentTargets.some(([pid, _]) => pid === clickedPiece.piece_id);
                    if (isValidOpponent) {
                        this.selectedOpponent = clickedPiece;
                        await this.updateHighlights();
                        this.render();
                        return;
                    }
                }
            }
        }
        
        // Check if clicked on a highlighted square (normal moves)
        if (this.selectedPiece && this.highlightedSquares.some(sq => sq[0] === x && sq[1] === y)) {
            await this.makeMove(this.selectedPiece.piece_id, x, y);
            return;
        }
        
        // Select own piece
        if (clickedPiece && clickedPiece.player === this.gameState.turn) {
            this.selectedPiece = clickedPiece;
            this.selectedOpponent = null;
            await this.updateHighlights();
            this.render();
        } else {
            this.selectedPiece = null;
            this.selectedOpponent = null;
            this.highlightedSquares = [];
            this.opponentTargets = null;
            this.render();
        }
    }
    
    async makeMoveOpponentSkill(pieceId, opponentId, x, y) {
        // For move opponent, we need to find the matching target
        const target = this.opponentTargets.find(([pid, coord]) => 
            pid === opponentId && coord[0] === x && coord[1] === y
        );
        
        if (!target) {
            console.error('Invalid move opponent target');
            return;
        }
        
        try {
            const response = await fetch(`/api/game/${this.gameId}/skill_move`, {
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
            
            const data = await response.json();
            this.gameState = data.state || data;
            this.selectedPiece = null;
            this.selectedOpponent = null;
            this.highlightedSquares = [];
            this.opponentTargets = null;
            this.updateUI();
            this.render();
            
            if (this.gameState.winner !== null) {
                this.showWinner();
                return;
            }
            
            // Check if AI should move
            if (data.ai_should_move || (this.aiEnabled && this.gameState.turn === this.aiPlayer)) {
                await this.makeAIMove();
            }
        } catch (error) {
            console.error('Error making move opponent skill:', error);
            alert('Failed to make skill move: ' + error.message);
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
            const targets = this.skillMode ? data.targets : data.moves;
            
            // Check if this is move opponent skill (targets are [piece_id, coord] tuples)
            if (this.skillMode && targets.length > 0 && Array.isArray(targets[0]) && 
                typeof targets[0][0] === 'number' && Array.isArray(targets[0][1])) {
                // Move opponent skill
                if (!this.selectedOpponent) {
                    // Show opponent pieces to select
                    this.highlightedSquares = [];
                    this.opponentTargets = targets;  // Store for later
                } else {
                    // Show destinations for selected opponent
                    this.highlightedSquares = targets
                        .filter(([pid, coord]) => pid === this.selectedOpponent.piece_id)
                        .map(([pid, coord]) => coord);
                }
            } else {
                // Regular moves or other skills
                this.highlightedSquares = targets;
                this.opponentTargets = null;
            }
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
            
            const data = await response.json();
            console.log('Move response:', data);
            
            // Handle both old format (direct state) and new format (state wrapper)
            this.gameState = data.state || data;
            this.selectedPiece = null;
            this.highlightedSquares = [];
            this.updateUI();
            this.render();
            
            if (this.gameState.winner !== null) {
                this.showWinner();
                return;
            }
            
            // Check if AI should move
            console.log('AI check:', {
                ai_should_move: data.ai_should_move,
                aiEnabled: this.aiEnabled,
                turn: this.gameState.turn,
                aiPlayer: this.aiPlayer
            });
            
            if (data.ai_should_move || (this.aiEnabled && this.gameState.turn === this.aiPlayer)) {
                console.log('Making AI move...');
                await this.makeAIMove();
            }
        } catch (error) {
            console.error('Error making move:', error);
            alert('Failed to make move: ' + error.message);
        }
    }
    
    async makeAIMove() {
        console.log('makeAIMove called, aiThinking:', this.aiThinking, 'aiEnabled:', this.aiEnabled);
        if (this.aiThinking || !this.aiEnabled) return;
        
        this.aiThinking = true;
        this.updateUI();
        
        // Small delay so user can see the board
        await new Promise(resolve => setTimeout(resolve, 500));
        
        try {
            console.log('Fetching AI move for game:', this.gameId);
            const response = await fetch(`/api/game/${this.gameId}/ai_move`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const error = await response.json();
                console.error('AI move failed:', error);
                alert('AI move failed: ' + (error.detail || 'Unknown error'));
                this.aiThinking = false;
                this.updateUI();
                return;
            }
            
            const data = await response.json();
            console.log('AI move response:', data);
            this.gameState = data.state;
            this.aiThinking = false;
            this.updateUI();
            this.render();
            
            if (this.gameState.winner !== null) {
                this.showWinner();
            }
        } catch (error) {
            console.error('Error making AI move:', error);
            alert('Error making AI move: ' + error.message);
            this.aiThinking = false;
            this.updateUI();
        }
    }
    
    updateUI() {
        if (!this.gameState) return;
        
        let turnText = `Player ${this.gameState.turn}`;
        if (this.aiThinking) {
            turnText += ' (AI Thinking...)';
        } else if (this.aiEnabled && this.gameState.turn === this.aiPlayer) {
            turnText += ' (AI)';
        }
        
        document.getElementById('current-turn').textContent = turnText;
        document.getElementById('round').textContent = this.gameState.rounds;
        document.getElementById('mode').textContent = this.skillMode ? 'Skill Mode' : 'Normal';
        
        const skillBtn = document.getElementById('toggle-skill-btn');
        if (this.skillMode) {
            skillBtn.classList.add('active');
        } else {
            skillBtn.classList.remove('active');
        }
        
        const aiBtn = document.getElementById('toggle-ai-btn');
        if (this.aiEnabled) {
            aiBtn.classList.add('active');
            aiBtn.textContent = 'AI: ON';
        } else {
            aiBtn.classList.remove('active');
            aiBtn.textContent = 'AI: OFF';
        }
        
        // Update skills list with expandable details
        const skillsList = document.getElementById('skills-list');
        skillsList.innerHTML = '';
        if (this.gameState.color_skills) {
            for (const [color, skill] of Object.entries(this.gameState.color_skills)) {
                const skillContainer = document.createElement('div');
                skillContainer.className = 'skill-container';
                
                const skillHeader = document.createElement('div');
                skillHeader.className = 'skill-header';
                skillHeader.style.borderLeftColor = color;
                skillHeader.innerHTML = `
                    <span class="skill-title">${color}: ${skill}</span>
                    <span class="expand-icon">▼</span>
                `;
                
                const skillDetails = document.createElement('div');
                skillDetails.className = 'skill-details hidden';
                skillDetails.innerHTML = `
                    <div class="intensity-level"><strong>1x:</strong> ${this.getSkillDescription(skill, 1)}</div>
                    <div class="intensity-level"><strong>2x:</strong> ${this.getSkillDescription(skill, 2)}</div>
                    <div class="intensity-level"><strong>3x:</strong> ${this.getSkillDescription(skill, 3)}</div>
                `;
                
                skillHeader.addEventListener('click', () => {
                    skillDetails.classList.toggle('hidden');
                    const icon = skillHeader.querySelector('.expand-icon');
                    icon.textContent = skillDetails.classList.contains('hidden') ? '▼' : '▲';
                });
                
                skillContainer.appendChild(skillHeader);
                skillContainer.appendChild(skillDetails);
                skillsList.appendChild(skillContainer);
            }
        }
    }
    
    getSkillDescription(skillName, intensity) {
        const descriptions = {
            'Move Extended': {
                1: 'Move 2 squares',
                2: 'Move 3 squares',
                3: 'Move 4 squares'
            },
            'Move Opponent': {
                1: 'Move opponent 1 square',
                2: 'Move opponent 1-2 squares',
                3: 'Move opponent 2 squares'
            },
            'Block Tile': {
                1: 'Block 1 tile for 1 round',
                2: 'Block 1 tile for 2 rounds',
                3: 'Block 1 tile for 3 rounds'
            }
        };
        return descriptions[skillName]?.[intensity] || 'Unknown';
    }
    
    showWinner() {
        const overlay = document.getElementById('winner-overlay');
        const text = document.getElementById('winner-text');
        text.textContent = `🎉 Player ${this.gameState.winner} Wins! 🎉`;
        overlay.classList.remove('hidden');
    }
    
    // Color map - medium intensity (between bold and very light)
    getColor(colorName) {
        const colorMap = {
            'red': 'rgba(255, 102, 102, 0.6)',      // Medium red
            'green': 'rgba(102, 255, 153, 0.6)',    // Medium green
            'blue': 'rgba(102, 153, 255, 0.6)',     // Medium blue
            'yellow': 'rgba(255, 255, 102, 0.6)',   // Medium yellow
            'purple': 'rgba(204, 153, 255, 0.6)',   // Medium purple
            'orange': 'rgba(255, 178, 102, 0.6)',   // Medium orange
            'pink': 'rgba(255, 153, 204, 0.6)',     // Medium pink
            'brown': 'rgba(204, 153, 102, 0.6)',    // Medium brown
            'gray': 'rgba(170, 170, 170, 0.6)',     // Medium gray
            'black': 'rgba(50, 50, 50, 0.6)',
            'white': 'rgba(240, 240, 255, 0.6)'
        };
        return colorMap[colorName] || 'rgba(180, 180, 180, 0.6)';
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
                this.ctx.fillStyle = this.getColor(color);
                this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
                
                // Draw grid lines
                this.ctx.strokeStyle = 'rgba(178, 178, 191, 0.3)';
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
        
        // Draw highlights (subtle gray with border)
        for (const [x, y] of this.highlightedSquares) {
            this.ctx.fillStyle = 'rgba(200, 200, 200, 0.2)';  // Very subtle gray
            this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
            // Add visible border
            this.ctx.strokeStyle = 'rgba(178, 255, 204, 0.9)';
            this.ctx.lineWidth = 3;
            this.ctx.strokeRect(x * this.cellSize + 2, y * this.cellSize + 2, this.cellSize - 4, this.cellSize - 4);
        }
        
        // Highlight opponent pieces for move opponent skill
        if (this.skillMode && this.opponentTargets && !this.selectedOpponent) {
            const opponentPieceIds = [...new Set(this.opponentTargets.map(([pid, _]) => pid))];
            for (const piece of this.gameState.pieces) {
                if (opponentPieceIds.includes(piece.piece_id)) {
                    const [x, y] = piece.loc;
                    this.ctx.fillStyle = 'rgba(255, 178, 217, 0.6)';  // Pink highlight
                    this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
                    this.ctx.strokeStyle = 'rgba(255, 102, 178, 0.9)';
                    this.ctx.lineWidth = 3;
                    this.ctx.strokeRect(x * this.cellSize + 2, y * this.cellSize + 2, this.cellSize - 4, this.cellSize - 4);
                }
            }
        }
        
        // Highlight selected opponent
        if (this.selectedOpponent) {
            const [x, y] = this.selectedOpponent.loc;
            this.ctx.fillStyle = 'rgba(255, 153, 204, 0.7)';
            this.ctx.fillRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
            this.ctx.strokeStyle = 'rgba(255, 51, 153, 1.0)';
            this.ctx.lineWidth = 4;
            this.ctx.strokeRect(x * this.cellSize + 4, y * this.cellSize + 4, this.cellSize - 8, this.cellSize - 8);
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

