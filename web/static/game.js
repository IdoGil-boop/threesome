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
        this.playerName = null;
        this.gameStartTime = null;
        this.currentStreak = 0;
        this.streakActive = false;
        this.lastGameConfig = null;  // Store last game configuration
        
        // Canvas sizing
        this.cellSize = 60;
        this.pieceRadius = 20;
        
        this.setupEventListeners();
        this.setupNavigation();
        // Don't auto-start game - show menu instead
    }
    
    setupEventListeners() {
        document.getElementById('new-game-btn').addEventListener('click', () => this.newGame(this.lastGameConfig));
        document.getElementById('toggle-skill-btn').addEventListener('click', () => this.toggleSkillMode());
        document.getElementById('toggle-ai-btn').addEventListener('click', () => this.toggleAI());
        document.getElementById('play-again-btn').addEventListener('click', () => this.newGame(this.lastGameConfig));
        document.getElementById('save-score-btn').addEventListener('click', () => this.showSaveScoreModal());
        document.getElementById('back-to-menu-btn').addEventListener('click', () => this.showMenu());
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
    }
    
    setupNavigation() {
        // Menu buttons
        document.getElementById('start-game-btn').addEventListener('click', () => {
            this.showView('game');
            this.newGame();
        });
        
        document.getElementById('leaderboard-btn').addEventListener('click', () => {
            this.showView('leaderboard');
            this.loadLeaderboard();
        });
        
        document.getElementById('board-builder-btn').addEventListener('click', () => {
            this.showView('board-builder');
        });
        
        document.getElementById('instructions-btn').addEventListener('click', () => {
            this.showView('instructions');
        });
        
        // Back buttons
        document.querySelectorAll('.back-btn').forEach(btn => {
            btn.addEventListener('click', () => this.showMenu());
        });
        
        // Board builder
        document.getElementById('create-board-btn').addEventListener('click', () => this.createCustomBoard());
        document.getElementById('num-colors').addEventListener('change', () => this.updateColorFields());
        
        // Initialize board builder
        this.availableColors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray'];
        this.updateColorFields();
    }
    
    showView(viewName) {
        // Hide all views
        document.getElementById('start-menu').classList.add('hidden');
        document.getElementById('leaderboard-view').classList.add('hidden');
        document.getElementById('instructions-view').classList.add('hidden');
        document.getElementById('board-builder-view').classList.add('hidden');
        document.getElementById('game-view').classList.add('hidden');
        
        // Show requested view
        if (viewName === 'menu') {
            document.getElementById('start-menu').classList.remove('hidden');
        } else if (viewName === 'game') {
            document.getElementById('game-view').classList.remove('hidden');
        } else if (viewName === 'leaderboard') {
            document.getElementById('leaderboard-view').classList.remove('hidden');
        } else if (viewName === 'instructions') {
            document.getElementById('instructions-view').classList.remove('hidden');
        } else if (viewName === 'board-builder') {
            document.getElementById('board-builder-view').classList.remove('hidden');
        }
    }
    
    showMenu() {
        // Going back to menu ends the streak
        if (this.streakActive && this.currentStreak > 0) {
            this.currentStreak = 0;
            this.streakActive = false;
        }
        this.showView('menu');
    }
    
    updateColorFields() {
        const numColors = parseInt(document.getElementById('num-colors').value);
        const paletteContainer = document.getElementById('color-palette-container');
        const proportionsContainer = document.getElementById('color-proportions-container');
        const forceSelect = document.getElementById('force-starting-color');
        
        // Clear existing
        paletteContainer.innerHTML = '';
        proportionsContainer.innerHTML = '';
        
        // Default colors for each slot
        const defaultColors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray'];
        
        // Create color palette dropdowns
        for (let i = 0; i < numColors; i++) {
            const row = document.createElement('div');
            row.className = 'color-palette-row';
            
            const label = document.createElement('label');
            label.textContent = `Color ${i + 1}:`;
            row.appendChild(label);
            
            const select = document.createElement('select');
            select.id = `color-${i}`;
            select.className = 'color-select';
            
            this.availableColors.forEach(color => {
                const option = document.createElement('option');
                option.value = color;
                option.textContent = color.charAt(0).toUpperCase() + color.slice(1);
                if (color === defaultColors[i]) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
            
            select.addEventListener('change', () => this.updateProportionsAndForce());
            row.appendChild(select);
            paletteContainer.appendChild(row);
        }
        
        this.updateProportionsAndForce();
    }
    
    updateProportionsAndForce() {
        const numColors = parseInt(document.getElementById('num-colors').value);
        const proportionsContainer = document.getElementById('color-proportions-container');
        const forceSelect = document.getElementById('force-starting-color');
        
        // Clear proportions
        proportionsContainer.innerHTML = '';
        
        // Get selected colors
        const selectedColors = [];
        for (let i = 0; i < numColors; i++) {
            const select = document.getElementById(`color-${i}`);
            if (select) {
                selectedColors.push(select.value);
            }
        }
        
        // Create proportion inputs
        const defaultProportion = (1.0 / numColors).toFixed(2);
        selectedColors.forEach((color, index) => {
            const row = document.createElement('div');
            row.className = 'color-proportion-row';
            
            const label = document.createElement('label');
            label.textContent = `${color.charAt(0).toUpperCase() + color.slice(1)}:`;
            row.appendChild(label);
            
            const input = document.createElement('input');
            input.type = 'number';
            input.id = `proportion-${color}`;
            input.min = '0';
            input.max = '1';
            input.step = '0.1';
            input.value = defaultProportion;
            row.appendChild(input);
            
            proportionsContainer.appendChild(row);
        });
        
        // Update force starting color options
        forceSelect.innerHTML = '<option value="Random">Random</option>';
        selectedColors.forEach(color => {
            const option = document.createElement('option');
            option.value = color;
            option.textContent = color.charAt(0).toUpperCase() + color.slice(1);
            forceSelect.appendChild(option);
        });
    }
    
    async createCustomBoard() {
        const width = parseInt(document.getElementById('board-width').value);
        const height = parseInt(document.getElementById('board-height').value);
        const pieces = parseInt(document.getElementById('board-pieces').value);
        const numColors = parseInt(document.getElementById('num-colors').value);
        
        // Validation
        if (width < 3 || width > 20 || height < 3 || height > 20) {
            alert('Board dimensions must be between 3 and 20');
            return;
        }
        
        if (pieces < 1 || pieces > 10) {
            alert('Pieces must be between 1 and 10');
            return;
        }
        
        // Get selected colors
        const colors = [];
        for (let i = 0; i < numColors; i++) {
            const select = document.getElementById(`color-${i}`);
            if (select) {
                colors.push(select.value);
            }
        }
        
        // Check for duplicates
        const uniqueColors = new Set(colors);
        if (uniqueColors.size !== colors.length) {
            alert('Error: Duplicate colors detected. Each color must be unique.');
            return;
        }
        
        // Get proportions
        const proportions = {};
        let totalProportion = 0;
        colors.forEach(color => {
            const input = document.getElementById(`proportion-${color}`);
            if (input) {
                const value = parseFloat(input.value);
                proportions[color] = value;
                totalProportion += value;
            }
        });
        
        // Validate proportions
        if (totalProportion > 1.0) {
            alert(`Error: Color proportions sum to ${totalProportion.toFixed(2)}, which exceeds 1.0`);
            return;
        }
        
        // Get force starting color
        const forceColor = document.getElementById('force-starting-color').value;
        
        // Create config object to store
        const boardConfig = { 
            width, 
            height, 
            num_pieces: pieces,
            colors: colors,
            proportions: proportions,
            force_starting_color: forceColor === 'Random' ? null : forceColor
        };
        
        this.showView('game');
        await this.newGame(boardConfig);
    }
    
    async loadLeaderboard() {
        const content = document.getElementById('leaderboard-content');
        content.innerHTML = '<div class="loading">Loading...</div>';
        
        try {
            const response = await fetch('/api/leaderboard');
            const data = await response.json();
            
            if (!data.scores || data.scores.length === 0) {
                content.innerHTML = '<div class="loading">No streaks yet. Win games to start your streak!</div>';
                return;
            }
            
            let html = '';
            data.scores.forEach((entry, index) => {
                const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
                const date = new Date(entry.timestamp).toLocaleDateString();
                const streak = entry.streak || 0;
                const streakLabel = streak === 1 ? 'win' : 'wins';
                html += `
                    <div class="leaderboard-entry">
                        <div class="leaderboard-rank ${rankClass}">#${index + 1}</div>
                        <div class="leaderboard-name">${entry.name}</div>
                        <div class="leaderboard-score">🔥 ${streak} ${streakLabel}</div>
                        <div class="leaderboard-date">${date}</div>
                    </div>
                `;
            });
            
            content.innerHTML = html;
        } catch (error) {
            console.error('Error loading leaderboard:', error);
            content.innerHTML = '<div class="loading">No streaks yet. Win games to start your streak!</div>';
        }
    }
    
    async newGame(customSettings = null) {
        try {
            this.gameStartTime = Date.now();
            
            // Use last config if no custom settings provided
            const config = customSettings || this.lastGameConfig || {};
            
            const settings = {
                width: config.width || 8,
                height: config.height || 8,
                num_pieces: config.num_pieces || 3,
                ai_enabled: this.aiEnabled,
                ai_player: this.aiPlayer,
                ai_depth: 3
            };
            
            // Only add optional settings if they're actually provided
            if (config.colors) {
                settings.colors = config.colors;
            }
            if (config.proportions) {
                settings.proportions = config.proportions;
            }
            if (config.force_starting_color !== undefined) {
                settings.force_starting_color = config.force_starting_color;
            } else {
                // Explicitly pass None to avoid Board's default of RED
                settings.force_starting_color = null;
            }
            
            // Store this configuration for next "New Game"
            this.lastGameConfig = config;
            
            const response = await fetch('/api/new_game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create game');
            }
            
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
            alert('Failed to create new game: ' + error.message);
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
        const clickY = Math.floor((e.clientY - rect.top) / this.cellSize);
        const y = this.gameState.height - 1 - clickY;  // Flip Y axis for click detection
        
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
        
        if (this.gameState.winner === 0) {
            // Player won - continue or start streak
            this.currentStreak++;
            this.streakActive = true;
            text.textContent = `🎉 You Win! 🎉\n🔥 Streak: ${this.currentStreak}`;
        } else {
            // Player lost - end streak
            this.currentStreak = 0;
            this.streakActive = false;
            text.textContent = `💀 AI Wins! 💀\nStreak ended.`;
        }
        
        overlay.classList.remove('hidden');
    }
    
    showSaveScoreModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Save Your Score</h3>
                <input type="text" id="player-name-input" placeholder="Enter your name" maxlength="20">
                <div class="modal-buttons">
                    <button class="btn btn-primary" id="submit-score-btn">Submit</button>
                    <button class="btn btn-secondary" id="cancel-score-btn">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        const nameInput = document.getElementById('player-name-input');
        nameInput.focus();
        
        const submitScore = async () => {
            const name = nameInput.value.trim();
            if (!name) {
                alert('Please enter your name');
                return;
            }
            
            await this.saveScore(name);
            document.body.removeChild(modal);
        };
        
        document.getElementById('submit-score-btn').addEventListener('click', submitScore);
        document.getElementById('cancel-score-btn').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        nameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') submitScore();
        });
    }
    
    async saveScore(name) {
        if (!this.gameState || this.gameState.winner !== 0) {
            alert('You can only save streaks when you win!');
            return;
        }
        
        const gameTime = Math.floor((Date.now() - this.gameStartTime) / 1000);
        this.playerName = name;  // Remember player name for streak continuation
        
        try {
            const response = await fetch('/api/leaderboard', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    score: this.currentStreak,  // Send streak as score
                    rounds: this.gameState.rounds,
                    time_seconds: gameTime
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                const streakLabel = this.currentStreak === 1 ? 'win' : 'wins';
                alert(`Streak saved! 🔥 ${this.currentStreak} ${streakLabel}!\nPress "Play Again" to continue your streak!`);
            } else {
                alert('Failed to save streak');
            }
        } catch (error) {
            console.error('Error saving streak:', error);
            alert('Failed to save streak');
        }
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
            'cream': 'rgb(232, 212, 180, 1)',     // Medium cream
            'black': 'rgba(50, 50, 50, 0.6)',
            'white': 'rgba(240, 240, 255, 0.6)'
        };
        return colorMap[colorName] || 'rgba(180, 180, 180, 0.9)';
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
        
        // Draw color grid (flipped so Player 0 at bottom)
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const color = this.gameState.color_grid[y][x];
                this.ctx.fillStyle = this.getColor(color);
                const renderY = (height - 1 - y) * this.cellSize;  // Flip Y axis
                this.ctx.fillRect(x * this.cellSize, renderY, this.cellSize, this.cellSize);
                
                // Draw grid lines
                this.ctx.strokeStyle = 'rgba(178, 178, 191, 0.3)';
                this.ctx.lineWidth = 1;
                this.ctx.strokeRect(x * this.cellSize, renderY, this.cellSize, this.cellSize);
            }
        }
        
        // Draw blocked tiles
        for (const [coord, turns] of Object.entries(this.gameState.blocked_tiles || {})) {
            const [x, y] = coord.split(',').map(Number);
            const renderY = (height - 1 - y) * this.cellSize;  // Flip Y axis
            
            // Draw darker background overlay
            this.ctx.fillStyle = 'rgba(128, 128, 140, 0.6)';
            this.ctx.fillRect(x * this.cellSize, renderY, this.cellSize, this.cellSize);
            
            // Draw red outline rectangle (matching Kivy style)
            this.ctx.strokeStyle = 'rgba(255, 102, 110, 0.9)';
            this.ctx.lineWidth = 3;
            this.ctx.strokeRect(x * this.cellSize + 5, renderY + 5, this.cellSize - 10, this.cellSize - 10);
            
            // Draw countdown number in bright red (matching Kivy style)
            this.ctx.fillStyle = 'rgba(255, 51, 76, 1.0)';
            this.ctx.font = `bold ${Math.floor(this.cellSize * 0.5)}px sans-serif`;
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(turns.toString(), (x + 0.5) * this.cellSize, renderY + this.cellSize * 0.5);
        }
        
        // Draw highlights (subtle gray with border)
        for (const [x, y] of this.highlightedSquares) {
            const renderY = (height - 1 - y) * this.cellSize;  // Flip Y axis
            this.ctx.fillStyle = 'rgba(200, 200, 200, 0.3)';  // Very subtle gray
            this.ctx.fillRect(x * this.cellSize, renderY, this.cellSize, this.cellSize);
            // Add visible border
            this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.65)';
            this.ctx.lineWidth = 1;
            this.ctx.strokeRect(x * this.cellSize + 2, renderY + 2, this.cellSize - 4, this.cellSize - 4);
        }
        
        // Highlight opponent pieces for move opponent skill
        if (this.skillMode && this.opponentTargets && !this.selectedOpponent) {
            const opponentPieceIds = [...new Set(this.opponentTargets.map(([pid, _]) => pid))];
            for (const piece of this.gameState.pieces) {
                if (opponentPieceIds.includes(piece.piece_id)) {
                    const [x, y] = piece.loc;
                    const renderY = (height - 1 - y) * this.cellSize;  // Flip Y axis
                    this.ctx.fillStyle = 'rgba(255, 178, 217, 0.6)';  // Pink highlight
                    this.ctx.fillRect(x * this.cellSize, renderY, this.cellSize, this.cellSize);
                    this.ctx.strokeStyle = 'rgba(255, 102, 178, 0.9)';
                    this.ctx.lineWidth = 3;
                    this.ctx.strokeRect(x * this.cellSize + 2, renderY + 2, this.cellSize - 4, this.cellSize - 4);
                }
            }
        }
        
        // Highlight selected opponent
        if (this.selectedOpponent) {
            const [x, y] = this.selectedOpponent.loc;
            const renderY = (height - 1 - y) * this.cellSize;  // Flip Y axis
            this.ctx.fillStyle = 'rgba(255, 153, 204, 0.7)';
            this.ctx.fillRect(x * this.cellSize, renderY, this.cellSize, this.cellSize);
            this.ctx.strokeStyle = 'rgba(255, 51, 153, 1.0)';
            this.ctx.lineWidth = 4;
            this.ctx.strokeRect(x * this.cellSize + 4, renderY + 4, this.cellSize - 8, this.cellSize - 8);
        }
        
        // Draw selected piece highlight
        if (this.selectedPiece) {
            const [x, y] = this.selectedPiece.loc;
            const renderY = (height - 1 - y) * this.cellSize;  // Flip Y axis
            this.ctx.fillStyle = 'rgba(255, 255, 0, 0.4)';
            this.ctx.fillRect(x * this.cellSize, renderY, this.cellSize, this.cellSize);
        }
        
        // Draw pieces
        for (const piece of this.gameState.pieces) {
            const [x, y] = piece.loc;
            const renderY = (height - 1 - y) * this.cellSize;  // Flip Y axis
            const centerX = (x + 0.5) * this.cellSize;
            const centerY = renderY + (0.5 * this.cellSize);
            
            // Draw piece circle with brown/cream fill
            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY, this.pieceRadius, 0, 2 * Math.PI);
            this.ctx.fillStyle = piece.player === 1 ? 'rgb(139, 90, 43)' : 'rgb(232, 212, 180)';  // Brown for AI, cream for player
            this.ctx.fill();
            
            // Draw border (darker version of fill)
            this.ctx.strokeStyle = piece.player === 1 ? 'rgb(90, 60, 30)' : 'rgb(180, 160, 130)';
            this.ctx.lineWidth = 3;
            this.ctx.stroke();
        }
    }
}

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const game = new Game();
    // Show menu on start
    game.showMenu();
});

