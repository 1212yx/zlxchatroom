class Snake {
    constructor(game, x, y, isAI = false, colorObj = null) {
        this.game = game;
        this.body = [{x: x, y: y}, {x: x, y: y + 1}, {x: x, y: y + 2}]; // Initial length 3
        this.direction = {x: 0, y: -1}; // Moving up initially
        this.nextDirection = {x: 0, y: -1};
        this.isAI = isAI;
        this.growPending = 0;
        this.invincible = false;
        this.invincibleTimer = 0;
        this.speedMultiplier = 1;
        this.isDead = false;
        
        // Colors
        if (colorObj) {
            this.headColor = colorObj.head;
            this.bodyColor = colorObj.body;
        } else {
            this.headColor = isAI ? Utils.COLORS.SNAKE_HEAD_AI : Utils.COLORS.SNAKE_HEAD;
            this.bodyColor = isAI ? Utils.COLORS.SNAKE_BODY_AI : Utils.COLORS.SNAKE_BODY;
        }

        // Stats
        this.score = 0;
        this.length = 3;
        this.comboCount = 0;
        this.lastEatTime = 0;
    }

    update() {
        if (this.isDead) return;

        // Apply next direction
        this.direction = this.nextDirection;

        // AI Logic
        if (this.isAI) {
            this.decideMove();
        }

        // Calculate new head position
        const head = this.body[0];
        let newHead = {
            x: head.x + this.direction.x,
            y: head.y + this.direction.y
        };

        // Handle Boundary
        if (this.game.settings.noBoundary) {
            if (newHead.x < 0) newHead.x = this.game.cols - 1;
            if (newHead.x >= this.game.cols) newHead.x = 0;
            if (newHead.y < 0) newHead.y = this.game.rows - 1;
            if (newHead.y >= this.game.rows) newHead.y = 0;
        } else {
            // Wall collision is handled in Game.checkCollision or here
            // If not wrapping, check bounds
            if (newHead.x < 0 || newHead.x >= this.game.cols || newHead.y < 0 || newHead.y >= this.game.rows) {
                if (!this.invincible) {
                    this.die();
                    return;
                } else {
                    // Invincible bounce or stop? Usually bounce or wrap. 
                    // Requirement says: "Invincible: 5s immunity (pass through wall/self)".
                    // If pass through wall means wrap, then wrap.
                    if (newHead.x < 0) newHead.x = this.game.cols - 1;
                    if (newHead.x >= this.game.cols) newHead.x = 0;
                    if (newHead.y < 0) newHead.y = this.game.rows - 1;
                    if (newHead.y >= this.game.rows) newHead.y = 0;
                }
            }
        }

        // Move body
        this.body.unshift(newHead); // Add new head

        // Check Growth
        if (this.growPending > 0) {
            this.growPending--;
            this.length++;
        } else {
            this.body.pop(); // Remove tail
        }

        // Update Invincible Timer
        if (this.invincible) {
            this.invincibleTimer -= this.game.tickRate; // Use tickRate (logic step) not deltaTime (render step)
            if (this.invincibleTimer <= 0) {
                this.invincible = false;
            }
        }
    }

    changeDirection(newDir) {
        // Prevent reversing
        if (this.direction.x + newDir.x === 0 && this.direction.y + newDir.y === 0) return;
        // Also prevent rapid double turn causing self collision (check against last move if implemented, or just update queue)
        // Here simplifying:
        this.nextDirection = newDir;
    }

    grow(amount = 1) {
        this.growPending += amount;
    }

    shrink(amount = 1) {
        if (this.length > 3) {
            for (let i = 0; i < amount; i++) {
                if (this.body.length > 3) {
                    this.body.pop();
                    this.length--;
                }
            }
        }
    }

    makeInvincible(durationMs) {
        this.invincible = true;
        this.invincibleTimer = durationMs;
    }

    die() {
        this.isDead = true;
        // Game will handle cleanup
    }

    onSnake(pos, ignoreHead = false) {
        for (let i = ignoreHead ? 1 : 0; i < this.body.length; i++) {
            if (Utils.isSamePosition(this.body[i], pos)) {
                return true;
            }
        }
        return false;
    }

    draw(ctx, gridSize) {
        if (this.isDead) return;

        const size = gridSize;

        // Draw Body
        let fillStyle = this.bodyColor;
        if (this.invincible) {
            // Blink if < 2 seconds left (every 200ms)
            if (this.invincibleTimer < 2000) {
                 if (Math.floor(Date.now() / 200) % 2 === 0) {
                     fillStyle = '#FFD700'; // Gold blink
                 } else {
                     fillStyle = '#fff';
                 }
            } else {
                 fillStyle = 'rgba(255, 255, 255, 0.9)'; // Bright white
            }
        }
        ctx.fillStyle = fillStyle;
        
        for (let i = 1; i < this.body.length; i++) {
            const part = this.body[i];
            ctx.fillRect(part.x * size, part.y * size, size, size);
            // Optional: Add borders for visibility
            ctx.strokeStyle = 'rgba(0,0,0,0.1)';
            ctx.strokeRect(part.x * size, part.y * size, size, size);
        }

        // Draw Head
        const head = this.body[0];
        ctx.fillStyle = this.invincible ? '#fff' : this.headColor;
        ctx.fillRect(head.x * size, head.y * size, size, size);

        // Draw Eyes (simple)
        ctx.fillStyle = 'white';
        const eyeSize = size / 5;
        const eyeOffset = size / 3;
        
        // Adjust eyes based on direction
        let eyeX1, eyeY1, eyeX2, eyeY2;
        
        // Simplified eye logic
        ctx.beginPath();
        ctx.arc(head.x * size + size/2, head.y * size + size/2, eyeSize, 0, Math.PI * 2); 
        ctx.fill();
    }

    // AI Logic Helpers
    decideMove() {
        // Find nearest food
        let foods = this.game.foods;
        let target = null;
        let minDist = Infinity;

        for (let food of foods) {
            if (!food.active) continue;
            let d = Math.abs(food.position.x - this.body[0].x) + Math.abs(food.position.y - this.body[0].y);
            if (d < minDist) {
                minDist = d;
                target = food.position;
            }
        }

        if (!target) return; // Keep moving

        // Possible moves
        const moves = [
            {x: 0, y: -1}, // Up
            {x: 0, y: 1},  // Down
            {x: -1, y: 0}, // Left
            {x: 1, y: 0}   // Right
        ];

        // Filter valid moves (not 180 turn)
        let validMoves = moves.filter(m => !(m.x + this.direction.x === 0 && m.y + this.direction.y === 0));

        // Filter safe moves (no collision)
        let safeMoves = validMoves.filter(m => {
            let nextPos = {
                x: this.body[0].x + m.x,
                y: this.body[0].y + m.y
            };
            
            // Check walls
            if (!this.game.settings.noBoundary) {
                if (nextPos.x < 0 || nextPos.x >= this.game.cols || nextPos.y < 0 || nextPos.y >= this.game.rows) return false;
            }
            
            // Check self
            if (this.onSnake(nextPos, true)) return false;
            
            // Check other snakes
            for (let other of this.game.snakes) {
                if (other === this) continue;
                if (other.onSnake(nextPos)) return false;
            }
            
            return true;
        });

        if (safeMoves.length === 0) {
            // No safe moves, just continue (and die)
            return;
        }

        // Pick move that minimizes distance to target
        let bestMove = safeMoves[0];
        let bestDist = Infinity;

        for (let move of safeMoves) {
            let nextPos = {
                x: this.body[0].x + move.x,
                y: this.body[0].y + move.y
            };
            let d = Math.abs(target.x - nextPos.x) + Math.abs(target.y - nextPos.y);
            if (d < bestDist) {
                bestDist = d;
                bestMove = move;
            }
        }

        this.nextDirection = bestMove;
    }
}
