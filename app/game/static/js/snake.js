class Snake {
    constructor(game, x, y, isAI = false, colorObj = null, name = null) {
        this.game = game;
        this.name = name;
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
            this.skinConfig = colorObj;
        } else {
            this.headColor = isAI ? Utils.COLORS.SNAKE_HEAD_AI : Utils.COLORS.SNAKE_HEAD;
            this.bodyColor = isAI ? Utils.COLORS.SNAKE_BODY_AI : Utils.COLORS.SNAKE_BODY;
        }

        // Stats
        this.score = 0;
        this.length = 3;
        this.comboCount = 0;
        this.lastEatTime = 0;

        // Exploration Logic (Anti-loop)
        this.stuckTimer = 0;
        this.lastRegionCenter = {x: x, y: y};
        this.isExploring = false;
        this.explorationTarget = null;
    }

    update() {
        if (this.isDead) return;

        // Apply next direction
        this.direction = this.nextDirection;

        // Check Area for Stuck Logic (Only for AI)
        if (this.isAI) {
            const head = this.body[0];
            const distFromCenter = Math.hypot(head.x - this.lastRegionCenter.x, head.y - this.lastRegionCenter.y);
            
            // If moved out of 5-unit radius, reset timer
            if (distFromCenter > 5) {
                this.lastRegionCenter = {x: head.x, y: head.y};
                this.stuckTimer = 0;
                // If we were exploring, we can stop now if we moved far enough? 
                // Or let exploration finish its target. Let's let it finish or reset if successfully moved.
                if (this.isExploring) {
                    this.isExploring = false;
                    this.explorationTarget = null;
                }
            } else {
                this.stuckTimer += this.game.tickRate;
            }

            // Trigger Exploration if stuck for 10s
            if (this.stuckTimer > 10000 && !this.isExploring) {
                this.isExploring = true;
                this.stuckTimer = 0; // Reset to avoid re-triggering immediately
                // Pick a random target that is safe
                let validTarget = false;
                let attempts = 0;
                while (!validTarget && attempts < 10) {
                    const pos = Utils.randomGridPosition(this.game.cols, this.game.rows);
                    if (this.isSafe(pos)) {
                        this.explorationTarget = pos;
                        validTarget = true;
                    }
                    attempts++;
                }
                if (!validTarget) {
                    this.explorationTarget = Utils.randomGridPosition(this.game.cols, this.game.rows);
                }
                console.log("AI stuck, triggering exploration to:", this.explorationTarget);
            }
        }

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

        // Custom Skin Rendering
        if (this.skinConfig) {
            if (this.skinConfig.render === 'kuromi') {
                this.drawKuromi(ctx, size);
                return;
            } else if (this.skinConfig.render === 'orange_soda') {
                this.drawOrangeSoda(ctx, size);
                return;
            } else if (this.skinConfig.render === 'flower_fairy') {
                this.drawFlowerFairy(ctx, size);
                return;
            } else if (this.skinConfig.render === 'graceful_lady') {
                this.drawGracefulLady(ctx, size);
                return;
            } else if (this.skinConfig.render === 'moon_goddess') {
                this.drawMoonGoddess(ctx, size);
                return;
            }
        }

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

        // Draw Name
        if (this.name) {
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'center';
            ctx.shadowColor = 'rgba(0,0,0,0.8)';
            ctx.shadowBlur = 3;
            ctx.fillText(this.name, head.x * size + size/2, head.y * size - 5);
            ctx.shadowColor = 'transparent';
            ctx.shadowBlur = 0;
        }

        // Draw Eyes (simple)
        ctx.fillStyle = 'white';
        const eyeSize = size / 5;
        
        // Simplified eye logic
        ctx.beginPath();
        ctx.arc(head.x * size + size/2, head.y * size + size/2, eyeSize, 0, Math.PI * 2); 
        ctx.fill();
    }

    drawKuromi(ctx, size) {
        // Draw Body (Strawberries) - Tail to Neck order for correct overlap (Neck over Body)
        // Actually, if we want head on top of neck, neck on top of body...
        // We must draw Tail FIRST (lowest Z), then Body... then Neck, then Head (highest Z).
        // This is the standard Painter's Algorithm.
        
        for (let i = this.body.length - 1; i > 0; i--) {
             const part = this.body[i];
             this.drawStrawberry(ctx, part.x * size, part.y * size, size);
        }

        // Draw Head (Last = Top)
        const head = this.body[0];
        this.drawKuromiHead(ctx, head.x * size, head.y * size, size);
    }

    drawStrawberry(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;
        
        // Shadow
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 5;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;

        // Berry (Red rounded triangle) - 3D Gradient
        const gradient = ctx.createRadialGradient(cx - size*0.1, cy - size*0.1, size*0.1, cx, cy, size*0.5);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            gradient.addColorStop(0, '#FFF59D');
            gradient.addColorStop(1, '#FFD700');
        } else {
            gradient.addColorStop(0, '#FF5252'); // Highlight
            gradient.addColorStop(1, '#B71C1C'); // Shadow
        }
        ctx.fillStyle = gradient;
        
        ctx.beginPath();
        // Shape: Top wider, bottom pointy
        ctx.moveTo(cx - size*0.35, cy - size*0.2);
        // Left curve to bottom
        ctx.bezierCurveTo(cx - size*0.4, cy + size*0.1, cx, cy + size*0.45, cx, cy + size*0.45);
        // Right curve to top
        ctx.bezierCurveTo(cx, cy + size*0.45, cx + size*0.4, cy + size*0.1, cx + size*0.35, cy - size*0.2);
        // Top curve
        ctx.quadraticCurveTo(cx, cy - size*0.25, cx - size*0.35, cy - size*0.2);
        ctx.fill();

        // Reset Shadow for details
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;

        // Seeds (Dots) - Embossed look
        const seeds = [
            {dx: 0, dy: 0},
            {dx: -0.15, dy: -0.1}, {dx: 0.15, dy: -0.1},
            {dx: -0.1, dy: 0.15}, {dx: 0.1, dy: 0.15},
            {dx: 0, dy: 0.25}
        ];
        
        seeds.forEach(s => {
            const sx = cx + size*s.dx;
            const sy = cy + size*s.dy;
            
            // Seed shadow
            ctx.fillStyle = 'rgba(0,0,0,0.2)';
            ctx.beginPath(); ctx.arc(sx, sy + 1, size*0.05, 0, Math.PI*2); ctx.fill();
            
            // Seed body
            ctx.fillStyle = '#FFD700'; 
            ctx.beginPath(); ctx.arc(sx, sy, size*0.05, 0, Math.PI*2); ctx.fill();
            
            // Seed highlight
            ctx.fillStyle = '#FFF'; 
            ctx.beginPath(); ctx.arc(sx - 1, sy - 1, size*0.02, 0, Math.PI*2); ctx.fill();
        });

        // Leaves (Green) - 3D Gradient
        const leafGrad = ctx.createLinearGradient(cx, cy - size*0.4, cx, cy - size*0.2);
        leafGrad.addColorStop(0, '#66BB6A');
        leafGrad.addColorStop(1, '#2E7D32');
        ctx.fillStyle = leafGrad;
        
        // Drop shadow for leaves
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 2;
        ctx.shadowOffsetY = 1;

        ctx.beginPath();
        ctx.moveTo(cx, cy - size*0.2); // Center base
        ctx.lineTo(cx - size*0.3, cy - size*0.35); // Left tip
        ctx.lineTo(cx - size*0.1, cy - size*0.25); // Left inner
        ctx.lineTo(cx, cy - size*0.4); // Top tip
        ctx.lineTo(cx + size*0.1, cy - size*0.25); // Right inner
        ctx.lineTo(cx + size*0.3, cy - size*0.35); // Right tip
        ctx.lineTo(cx, cy - size*0.2); // Close
        ctx.fill();

        // Reset Shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;
    }

    drawKuromiHead(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;
        
        // Hood (Pink) - 3D Sphere Gradient
        const hoodGrad = ctx.createRadialGradient(cx - size*0.15, cy - size*0.15, size*0.1, cx, cy, size*0.5);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            hoodGrad.addColorStop(0, '#FFF59D');
            hoodGrad.addColorStop(1, '#FFD700');
        } else {
            hoodGrad.addColorStop(0, '#F48FB1'); // Light Pink
            hoodGrad.addColorStop(1, '#C2185B'); // Dark Pink
        }
        ctx.fillStyle = hoodGrad;
        
        // Shadow for head
        ctx.shadowColor = 'rgba(0,0,0,0.4)';
        ctx.shadowBlur = 8;
        ctx.shadowOffsetY = 3;

        // Ears
        ctx.beginPath();
        // Left Ear
        ctx.ellipse(cx - size*0.25, cy - size*0.3, size*0.12, size*0.25, -0.2, 0, Math.PI*2);
        // Right Ear
        ctx.ellipse(cx + size*0.25, cy - size*0.3, size*0.12, size*0.25, 0.2, 0, Math.PI*2);
        ctx.fill();
        
        // Head Base
        ctx.beginPath();
        ctx.arc(cx, cy + size*0.05, size*0.4, 0, Math.PI*2);
        ctx.fill();

        // Reset Shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;

        // Face (White) - Slight Gradient
        const faceGrad = ctx.createRadialGradient(cx, cy + size*0.1, size*0.05, cx, cy + size*0.1, size*0.3);
        faceGrad.addColorStop(0, '#FFFFFF');
        faceGrad.addColorStop(1, '#F5F5F5');
        ctx.fillStyle = faceGrad;
        
        ctx.beginPath();
        ctx.ellipse(cx, cy + size*0.1, size*0.3, size*0.22, 0, 0, Math.PI*2);
        ctx.fill();

        // Eyes (Black) with Shine
        ctx.fillStyle = '#000';
        ctx.beginPath(); ctx.arc(cx - size*0.12, cy + size*0.1, size*0.04, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx + size*0.12, cy + size*0.1, size*0.04, 0, Math.PI*2); ctx.fill();
        
        // Eye Shine
        ctx.fillStyle = '#FFF';
        ctx.beginPath(); ctx.arc(cx - size*0.13, cy + size*0.09, size*0.015, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx + size*0.11, cy + size*0.09, size*0.015, 0, Math.PI*2); ctx.fill();

        // Nose (Pink)
        ctx.fillStyle = '#FF69B4'; 
        ctx.beginPath(); ctx.arc(cx, cy + size*0.16, size*0.03, 0, Math.PI*2); ctx.fill();

        // Skull Icon (Purple Oval) - Embossed
        const skullGrad = ctx.createRadialGradient(cx, cy - size*0.2, 0, cx, cy - size*0.2, size*0.08);
        skullGrad.addColorStop(0, '#BA68C8');
        skullGrad.addColorStop(1, '#6A1B9A');
        ctx.fillStyle = skullGrad;
        
        ctx.shadowColor = 'rgba(0,0,0,0.5)';
        ctx.shadowBlur = 2;
        
        ctx.beginPath();
        ctx.ellipse(cx, cy - size*0.2, size*0.08, size*0.06, 0, 0, Math.PI*2);
        ctx.fill();
        
        // Reset Shadow
        ctx.shadowColor = 'transparent';
    }

    drawOrangeSoda(ctx, size) {
        // Draw Body (Orange Slices) - Tail to Neck order for overlap (Bottom slices under top ones)
        // Similar to Kuromi, we want a tower look.
        // Stack bottom-up visual, but Painter's algorithm means back-to-front.
        // If "Head" is top, and Body[1] is below Head, Body[2] below Body[1]...
        // We draw Tail (Body[last]) first, then ... Body[1], then Head.
        
        for (let i = this.body.length - 1; i > 0; i--) {
             const part = this.body[i];
             this.drawOrangeSlice(ctx, part.x * size, part.y * size, size);
        }

        // Draw Head (Glass Cup)
        const head = this.body[0];
        this.drawOrangeSodaHead(ctx, head.x * size, head.y * size, size);
    }

    drawOrangeSlice(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;
        const radius = size * 0.45;

        // Shadow
        ctx.shadowColor = 'rgba(0,0,0,0.2)';
        ctx.shadowBlur = 4;
        ctx.shadowOffsetY = 2;

        // Peel (Orange) - 3D Gradient
        const peelGrad = ctx.createRadialGradient(cx - size*0.1, cy - size*0.1, size*0.1, cx, cy, radius);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            peelGrad.addColorStop(0, '#FFF59D');
            peelGrad.addColorStop(1, '#FFD700');
        } else {
            peelGrad.addColorStop(0, '#FFA726'); // Light
            peelGrad.addColorStop(1, '#EF6C00'); // Dark
        }
        ctx.fillStyle = peelGrad;
        
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fill();

        // Reset Shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;

        // Pith (White) - Slight inner shadow
        ctx.fillStyle = '#FFF3E0';
        ctx.beginPath();
        ctx.arc(cx, cy, radius * 0.9, 0, Math.PI * 2);
        ctx.fill();

        // Segments (Orange Flesh) - Gradient
        const fleshGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            fleshGrad.addColorStop(0, '#FFEE58');
            fleshGrad.addColorStop(1, '#FBC02D');
        } else {
            fleshGrad.addColorStop(0, '#FFCC80'); // Center Light
            fleshGrad.addColorStop(1, '#FB8C00'); // Edge Dark
        }
        ctx.fillStyle = fleshGrad;
        
        const segments = 8;
        for (let i = 0; i < segments; i++) {
            ctx.beginPath();
            const startAngle = (i * 2 * Math.PI) / segments + 0.1;
            const endAngle = ((i + 1) * 2 * Math.PI) / segments - 0.1;
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, radius * 0.85, startAngle, endAngle);
            ctx.fill();
        }
        
        // Highlight (Gloss)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.beginPath();
        ctx.arc(cx - size*0.1, cy - size*0.1, radius*0.3, 0, Math.PI*2);
        ctx.fill();
    }

    drawOrangeSodaHead(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;
        
        // Glass Cup Shape (Trapezoid-ish)
        const topW = size * 0.7;
        const bottomW = size * 0.5;
        const h = size * 0.8;
        const topY = cy - h/2;
        const bottomY = cy + h/2;

        // Liquid (Orange Soda) - Gradient
        const liquidGrad = ctx.createLinearGradient(cx, topY, cx, bottomY);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            liquidGrad.addColorStop(0, '#FFF59D');
            liquidGrad.addColorStop(1, '#FBC02D');
        } else {
            liquidGrad.addColorStop(0, '#FFA726'); // Top Light
            liquidGrad.addColorStop(1, '#EF6C00'); // Bottom Dark
        }
        ctx.fillStyle = liquidGrad;
        
        ctx.beginPath();
        ctx.moveTo(cx - topW/2 + size*0.05, topY + size*0.1); // Slightly below rim
        ctx.lineTo(cx + topW/2 - size*0.05, topY + size*0.1);
        ctx.lineTo(cx + bottomW/2, bottomY);
        ctx.lineTo(cx - bottomW/2, bottomY);
        ctx.closePath();
        ctx.fill();

        // Ice Cubes (3D-ish)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.lineWidth = 1;
        
        const drawIce = (ix, iy, is) => {
            ctx.fillRect(ix, iy, is, is);
            ctx.strokeRect(ix, iy, is, is);
            // Shine
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.fillRect(ix, iy, is, is*0.2);
            ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        };
        
        drawIce(cx - size*0.1, cy + size*0.05, size*0.15);
        drawIce(cx + size*0.05, cy - size*0.1, size*0.12);

        // Bubbles
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.beginPath(); ctx.arc(cx - size*0.15, cy + size*0.2, size*0.04, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx + size*0.15, cy + size*0.15, size*0.03, 0, Math.PI*2); ctx.fill();

        // Glass Body - Cylindrical Gradient
        const glassGrad = ctx.createLinearGradient(cx - topW/2, cy, cx + topW/2, cy);
        glassGrad.addColorStop(0, 'rgba(255, 255, 255, 0.4)');
        glassGrad.addColorStop(0.2, 'rgba(255, 255, 255, 0.1)');
        glassGrad.addColorStop(0.8, 'rgba(255, 255, 255, 0.1)');
        glassGrad.addColorStop(1, 'rgba(255, 255, 255, 0.4)');
        
        ctx.fillStyle = glassGrad;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.lineWidth = 2;
        
        ctx.beginPath();
        ctx.moveTo(cx - topW/2, topY);
        ctx.lineTo(cx + topW/2, topY);
        ctx.lineTo(cx + bottomW/2, bottomY);
        ctx.lineTo(cx - bottomW/2, bottomY);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Lemon Slice (Inside/On Rim)
        ctx.fillStyle = '#FFEB3B'; 
        ctx.beginPath();
        ctx.arc(cx - size*0.1, topY + size*0.1, size*0.15, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#FBC02D';
        ctx.lineWidth = 1;
        ctx.stroke();
        // Inner lemon details
        ctx.beginPath(); ctx.moveTo(cx - size*0.1, topY + size*0.1); ctx.lineTo(cx - size*0.1 + size*0.15, topY + size*0.1); ctx.stroke();

        // Straw (Pink) - Cylinder Gradient
        ctx.save();
        ctx.lineWidth = size * 0.08;
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#F06292'; 
        // 3D effect on stroke is hard, simple color for now or use fill path
        ctx.beginPath();
        ctx.moveTo(cx + size*0.1, bottomY - size*0.1); 
        ctx.lineTo(cx + size*0.2, topY - size*0.2); 
        ctx.lineTo(cx + size*0.3, topY - size*0.2); 
        ctx.stroke();
        ctx.restore();

        // Orange Slice Decoration (Rim) - 3D
        const rimGrad = ctx.createRadialGradient(cx - topW/2, topY, 0, cx - topW/2, topY, size*0.2);
        rimGrad.addColorStop(0, '#FFA726');
        rimGrad.addColorStop(1, '#EF6C00');
        ctx.fillStyle = rimGrad;
        
        ctx.beginPath();
        ctx.arc(cx - topW/2, topY, size*0.2, 0, Math.PI, true); 
        ctx.fill();
        ctx.strokeStyle = '#FFF';
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    drawFlowerFairy(ctx, size) {
        // Draw Body (Vine Flowers) - Tail to Neck order
        for (let i = this.body.length - 1; i > 0; i--) {
             const part = this.body[i];
             this.drawVineFlower(ctx, part.x * size, part.y * size, size, i);
        }

        // Draw Head (Fairy)
        const head = this.body[0];
        this.drawFairyHead(ctx, head.x * size, head.y * size, size);
    }

    drawVineFlower(ctx, x, y, size, index) {
        const cx = x + size/2;
        const cy = y + size/2;
        const radius = size * 0.45;

        // Shadow
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 4;
        ctx.shadowOffsetY = 2;

        // Vine (Green swirl) - 3D effect via multiple strokes or just shadow
        ctx.strokeStyle = '#388E3C'; // Darker green for base
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.arc(cx, cy, radius * 0.8, 0 + index, Math.PI * 1.5 + index); 
        ctx.stroke();

        ctx.strokeStyle = '#66BB6A'; // Lighter green for highlight
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cx - 1, cy - 1, radius * 0.8, 0 + index, Math.PI * 1.5 + index); 
        ctx.stroke();

        // Reset Shadow for details
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;

        // Leaves - 3D Gradient
        const leafGrad = ctx.createLinearGradient(cx - size*0.3, cy, cx + size*0.3, cy);
        leafGrad.addColorStop(0, '#A5D6A7');
        leafGrad.addColorStop(1, '#2E7D32');
        ctx.fillStyle = leafGrad;
        
        ctx.shadowColor = 'rgba(0,0,0,0.2)';
        ctx.shadowBlur = 2;

        ctx.beginPath();
        ctx.ellipse(cx - size*0.3, cy + size*0.1, size*0.15, size*0.08, Math.PI/4, 0, Math.PI*2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(cx + size*0.3, cy - size*0.1, size*0.15, size*0.08, -Math.PI/4, 0, Math.PI*2);
        ctx.fill();

        // Flower (Pink/Purple Gradient)
        const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            gradient.addColorStop(0, '#FFF59D');
            gradient.addColorStop(1, '#FFD700');
        } else {
            gradient.addColorStop(0, '#F8BBD0'); // Light Pink
            gradient.addColorStop(0.6, '#EC407A'); // Darker Pink
            gradient.addColorStop(1, '#880E4F'); // Deep Purple/Red
        }
        
        ctx.fillStyle = gradient;
        ctx.shadowColor = 'rgba(0,0,0,0.4)';
        ctx.shadowBlur = 5;
        
        // Flower Petals (5 petals)
        for (let i = 0; i < 5; i++) {
            ctx.beginPath();
            const angle = (i * 2 * Math.PI) / 5;
            const px = cx + Math.cos(angle) * size * 0.25;
            const py = cy + Math.sin(angle) * size * 0.25;
            ctx.arc(px, py, size * 0.22, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Flower Center - 3D Sphere
        const centerGrad = ctx.createRadialGradient(cx - size*0.05, cy - size*0.05, 0, cx, cy, size*0.12);
        centerGrad.addColorStop(0, '#FFF9C4');
        centerGrad.addColorStop(1, '#FBC02D');
        
        ctx.fillStyle = centerGrad;
        ctx.beginPath();
        ctx.arc(cx, cy, size * 0.12, 0, Math.PI * 2);
        ctx.fill();

        // Reset Shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
    }

    drawFairyHead(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;

        // Wings (Transparent Blue/White) - Glassy 3D
        ctx.save();
        const wingGrad = ctx.createLinearGradient(cx, cy - size*0.4, cx, cy + size*0.4);
        wingGrad.addColorStop(0, 'rgba(224, 247, 250, 0.8)');
        wingGrad.addColorStop(0.5, 'rgba(179, 229, 252, 0.4)');
        wingGrad.addColorStop(1, 'rgba(224, 247, 250, 0.8)');
        
        ctx.fillStyle = wingGrad;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.lineWidth = 2;
        ctx.shadowColor = 'rgba(179, 229, 252, 0.6)';
        ctx.shadowBlur = 10;
        
        // Left Wing
        ctx.beginPath();
        ctx.ellipse(cx - size*0.3, cy, size*0.3, size*0.4, -0.2, 0, Math.PI*2);
        ctx.fill();
        ctx.stroke();
        // Right Wing
        ctx.beginPath();
        ctx.ellipse(cx + size*0.3, cy, size*0.3, size*0.4, 0.2, 0, Math.PI*2);
        ctx.fill();
        ctx.stroke();
        ctx.restore();

        // Hair (Gold) - Gradient
        const hairGrad = ctx.createLinearGradient(cx, cy - size*0.5, cx, cy + size*0.5);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
             hairGrad.addColorStop(0, '#FFFFFF');
             hairGrad.addColorStop(1, '#FFF59D');
        } else {
             hairGrad.addColorStop(0, '#FFECB3'); // Light Gold
             hairGrad.addColorStop(1, '#FFB300'); // Dark Gold
        }
        ctx.fillStyle = hairGrad;
        
        // Drop shadow for head/hair
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 5;
        ctx.shadowOffsetY = 2;

        // Back hair
        ctx.beginPath();
        ctx.arc(cx, cy, size * 0.45, Math.PI, 0, true); // Top half
        ctx.lineTo(cx + size*0.45, cy + size*0.4);
        ctx.lineTo(cx - size*0.45, cy + size*0.4);
        ctx.fill();

        // Face - 3D Sphere
        const faceGrad = ctx.createRadialGradient(cx - size*0.1, cy, size*0.05, cx, cy + size*0.1, size*0.3);
        faceGrad.addColorStop(0, '#FFF9C4'); // Highlight
        faceGrad.addColorStop(1, '#FFE082'); // Shadow skin tone
        ctx.fillStyle = faceGrad;
        
        ctx.beginPath();
        ctx.arc(cx, cy + size*0.1, size*0.3, 0, Math.PI * 2);
        ctx.fill();

        // Dress (Top part visible) - Blue/Pink Gradient
        const dressGrad = ctx.createLinearGradient(cx, cy + size*0.1, cx, cy + size*0.7);
        dressGrad.addColorStop(0, '#81D4FA');
        dressGrad.addColorStop(1, '#0288D1');
        ctx.fillStyle = dressGrad;
        
        ctx.beginPath();
        ctx.arc(cx, cy + size*0.4, size*0.3, Math.PI, 0);
        ctx.fill();

        // Reset Shadow for face details
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;

        // Eyes (Blue) with shine
        ctx.fillStyle = '#0277BD';
        ctx.beginPath(); ctx.arc(cx - size*0.12, cy + size*0.1, size*0.04, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx + size*0.12, cy + size*0.1, size*0.04, 0, Math.PI*2); ctx.fill();
        
        ctx.fillStyle = '#FFF';
        ctx.beginPath(); ctx.arc(cx - size*0.13, cy + size*0.09, size*0.015, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx + size*0.11, cy + size*0.09, size*0.015, 0, Math.PI*2); ctx.fill();

        // Mouth (Smile)
        ctx.strokeStyle = '#E91E63';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(cx, cy + size*0.15, size*0.1, 0, Math.PI);
        ctx.stroke();

        // Flower Decoration on Hair - 3D
        const decoGrad = ctx.createRadialGradient(cx - size*0.32, cy - size*0.22, 0, cx - size*0.3, cy - size*0.2, size*0.1);
        decoGrad.addColorStop(0, '#F48FB1');
        decoGrad.addColorStop(1, '#C2185B');
        ctx.fillStyle = decoGrad;
        
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 2;
        ctx.beginPath();
        ctx.arc(cx - size*0.3, cy - size*0.2, size*0.1, 0, Math.PI*2);
        ctx.fill();
        
        ctx.shadowColor = 'transparent';
    }

    drawGracefulLady(ctx, size) {
        // Draw Body (Skirt Segments) - Tail to Head order
        for (let i = this.body.length - 1; i > 0; i--) {
            const part = this.body[i];
            this.drawGracefulLadySkirt(ctx, part.x * size, part.y * size, size);
        }

        // Draw Head
        const head = this.body[0];
        this.drawGracefulLadyHead(ctx, head.x * size, head.y * size, size);
    }

    drawGracefulLadySkirt(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;

        // Skirt Base (Pink Trapezoid) - 3D Gradient
        const skirtGrad = ctx.createLinearGradient(cx, cy - size*0.4, cx, cy + size*0.4);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            skirtGrad.addColorStop(0, '#FFFFFF');
            skirtGrad.addColorStop(1, '#E0E0E0');
        } else {
            skirtGrad.addColorStop(0, '#F8BBD0'); // Light
            skirtGrad.addColorStop(1, '#EC407A'); // Dark
        }
        ctx.fillStyle = skirtGrad;
        
        // Shadow
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 4;
        ctx.shadowOffsetY = 2;

        ctx.beginPath();
        // Top narrower than bottom
        ctx.moveTo(cx - size*0.35, cy - size*0.4);
        ctx.lineTo(cx + size*0.35, cy - size*0.4);
        // Bottom wider
        ctx.lineTo(cx + size*0.45, cy + size*0.4);
        ctx.lineTo(cx - size*0.45, cy + size*0.4);
        ctx.closePath();
        ctx.fill();
        
        // Reset Shadow for details
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;

        // Gold Knot Decoration - 3D
        ctx.strokeStyle = '#FFD54F'; 
        ctx.lineWidth = size * 0.08;
        
        // Horizontal band with shadow
        ctx.shadowColor = 'rgba(0,0,0,0.2)';
        ctx.shadowBlur = 2;
        ctx.beginPath();
        ctx.moveTo(cx - size*0.3, cy - size*0.1);
        ctx.lineTo(cx + size*0.3, cy - size*0.1);
        ctx.stroke();

        // Knot center - 3D Sphere
        const knotGrad = ctx.createRadialGradient(cx - size*0.03, cy - size*0.13, 0, cx, cy - size*0.1, size*0.1);
        knotGrad.addColorStop(0, '#FFF59D');
        knotGrad.addColorStop(1, '#FFA000');
        ctx.fillStyle = knotGrad;
        
        ctx.beginPath();
        ctx.arc(cx, cy - size*0.1, size*0.1, 0, Math.PI*2);
        ctx.fill();

        // Tassel vertical
        ctx.strokeStyle = '#FFCA28';
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx, cy + size*0.3);
        ctx.stroke();
        
        ctx.shadowColor = 'transparent';
    }

    drawGracefulLadyHead(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;

        // Hair (Black, Long back) - 3D Sheen
        const hairGrad = ctx.createLinearGradient(cx - size*0.2, cy - size*0.3, cx + size*0.2, cy);
        hairGrad.addColorStop(0, '#424242');
        hairGrad.addColorStop(0.3, '#757575'); // Shine
        hairGrad.addColorStop(1, '#212121');
        ctx.fillStyle = hairGrad;

        // Head shadow
        ctx.shadowColor = 'rgba(0,0,0,0.4)';
        ctx.shadowBlur = 5;

        ctx.beginPath();
        // Back hair
        ctx.moveTo(cx - size*0.4, cy - size*0.3);
        ctx.lineTo(cx + size*0.4, cy - size*0.3);
        ctx.lineTo(cx + size*0.45, cy + size*0.4); // Long hair down
        ctx.lineTo(cx - size*0.45, cy + size*0.4);
        ctx.fill();

        // Face (Skin tone) - 3D Sphere
        const faceGrad = ctx.createRadialGradient(cx - size*0.05, cy - size*0.15, size*0.05, cx, cy - size*0.1, size*0.35);
        faceGrad.addColorStop(0, '#FFF9C4');
        faceGrad.addColorStop(1, '#FFE082');
        ctx.fillStyle = faceGrad;
        
        ctx.beginPath();
        ctx.arc(cx, cy - size*0.1, size*0.35, 0, Math.PI*2);
        ctx.fill();

        // Reset Shadow for face details
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;

        // Bangs (Black) - Matches hair
        ctx.fillStyle = hairGrad;
        ctx.beginPath();
        ctx.arc(cx, cy - size*0.1, size*0.35, Math.PI, 0); // Top half
        ctx.fill();

        // Eyes
        ctx.fillStyle = '#3E2723';
        ctx.beginPath(); ctx.arc(cx - size*0.12, cy - size*0.05, size*0.04, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx + size*0.12, cy - size*0.05, size*0.04, 0, Math.PI*2); ctx.fill();

        // Blush
        ctx.fillStyle = 'rgba(255, 105, 180, 0.4)';
        ctx.beginPath(); ctx.arc(cx - size*0.2, cy + size*0.05, size*0.06, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx + size*0.2, cy + size*0.05, size*0.06, 0, Math.PI*2); ctx.fill();

        // Kimono Shoulders (Pink) - Gradient
        const kimonoGrad = ctx.createLinearGradient(cx, cy + size*0.15, cx, cy + size*0.5);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            kimonoGrad.addColorStop(0, '#FFF');
            kimonoGrad.addColorStop(1, '#EEE');
        } else {
            kimonoGrad.addColorStop(0, '#F48FB1');
            kimonoGrad.addColorStop(1, '#C2185B');
        }
        ctx.fillStyle = kimonoGrad;
        
        ctx.beginPath();
        ctx.moveTo(cx - size*0.3, cy + size*0.25);
        ctx.quadraticCurveTo(cx, cy + size*0.15, cx + size*0.3, cy + size*0.25); // Collar
        ctx.lineTo(cx + size*0.4, cy + size*0.5); // Shoulder down
        ctx.lineTo(cx - size*0.4, cy + size*0.5);
        ctx.fill();

        // Red Hair Ornament - 3D Sphere
        const ornGrad = ctx.createRadialGradient(cx - size*0.28, cy - size*0.38, 0, cx - size*0.25, cy - size*0.35, size*0.08);
        ornGrad.addColorStop(0, '#FF5252');
        ornGrad.addColorStop(1, '#B71C1C');
        ctx.fillStyle = ornGrad;
        
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 2;
        ctx.beginPath();
        ctx.arc(cx - size*0.25, cy - size*0.35, size*0.08, 0, Math.PI*2);
        ctx.fill();
        
        // Tassel from ornament
        ctx.strokeStyle = '#D32F2F';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cx - size*0.25, cy - size*0.35);
        ctx.lineTo(cx - size*0.25, cy - size*0.15);
        ctx.stroke();

        // Blue Object (Fan or Gem) - 3D
        const fanGrad = ctx.createLinearGradient(cx - size*0.1, cy + size*0.3, cx + size*0.1, cy + size*0.45);
        fanGrad.addColorStop(0, '#42A5F5');
        fanGrad.addColorStop(1, '#1565C0');
        ctx.fillStyle = fanGrad;
        
        ctx.beginPath();
        ctx.rect(cx - size*0.1, cy + size*0.3, size*0.2, size*0.15);
        ctx.fill();
        
        ctx.shadowColor = 'transparent';
    }

    drawMoonGoddess(ctx, size) {
        // Draw Body (Moon Segments) - Tail to Head order
        for (let i = this.body.length - 1; i > 0; i--) {
            const part = this.body[i];
            this.drawMoonSegment(ctx, part.x * size, part.y * size, size);
        }

        // Draw Head
        const head = this.body[0];
        this.drawMoonGoddessHead(ctx, head.x * size, head.y * size, size);
    }

    drawMoonSegment(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;
        const radius = size * 0.45;

        // Glowing Moon (Golden Yellow) - 3D Gradient
        const moonGrad = ctx.createRadialGradient(cx, cy, radius*0.5, cx, cy, radius);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            moonGrad.addColorStop(0, '#FFFFFF');
            moonGrad.addColorStop(1, '#FFF9C4');
        } else {
            moonGrad.addColorStop(0, '#FFF59D'); // Light center
            moonGrad.addColorStop(1, '#FBC02D'); // Dark edge
        }
        ctx.fillStyle = moonGrad;
        
        // Glow
        ctx.shadowColor = 'rgba(255, 235, 59, 0.6)';
        ctx.shadowBlur = 10;
        
        ctx.beginPath();
        // Crescent shape
        ctx.arc(cx, cy, radius, 0.1 * Math.PI, 1.9 * Math.PI, true); 
        ctx.bezierCurveTo(cx - size*0.2, cy - size*0.4, cx - size*0.2, cy + size*0.4, cx + size*0.1, cy + size*0.4);
        ctx.fill();

        // Reset Shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;

        // Small Stars Decoration - Glowing
        ctx.fillStyle = '#FFF';
        ctx.shadowColor = '#FFF';
        ctx.shadowBlur = 4;
        this.drawStar(ctx, cx + size*0.1, cy - size*0.1, size*0.1, 5);
        this.drawStar(ctx, cx - size*0.1, cy + size*0.2, size*0.06, 4);
        
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
    }

    drawMoonGoddessHead(ctx, x, y, size) {
        const cx = x + size/2;
        const cy = y + size/2;

        // Moon Seat (Yellow Crescent) - 3D
        const seatGrad = ctx.createRadialGradient(cx, cy + size*0.1, 0, cx, cy + size*0.1, size*0.4);
        seatGrad.addColorStop(0, '#FFF176');
        seatGrad.addColorStop(1, '#F57F17');
        ctx.fillStyle = seatGrad;
        
        ctx.shadowColor = 'rgba(255, 193, 7, 0.4)';
        ctx.shadowBlur = 8;

        ctx.beginPath();
        ctx.arc(cx, cy + size*0.1, size*0.4, 0, Math.PI, false); // Bottom arc
        ctx.bezierCurveTo(cx - size*0.4, cy - size*0.1, cx + size*0.4, cy - size*0.1, cx + size*0.4, cy + size*0.1);
        ctx.fill();

        // Reset Shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;

        // Goddess Body (Dress) - Gradient
        const dressGrad = ctx.createLinearGradient(cx, cy, cx, cy + size*0.3);
        if (this.invincible && (Math.floor(Date.now() / 200) % 2 === 0)) {
            dressGrad.addColorStop(0, '#FFF');
            dressGrad.addColorStop(1, '#EEE');
        } else {
            dressGrad.addColorStop(0, '#E1F5FE');
            dressGrad.addColorStop(1, '#81D4FA');
        }
        ctx.fillStyle = dressGrad;
        
        ctx.beginPath();
        ctx.moveTo(cx, cy - size*0.2); // Neck
        ctx.lineTo(cx + size*0.25, cy + size*0.3); // Right bottom dress
        ctx.lineTo(cx - size*0.25, cy + size*0.3); // Left bottom dress
        ctx.fill();

        // Hair (Light Blue, Long) - Gradient
        const hairGrad = ctx.createLinearGradient(cx, cy - size*0.3, cx, cy + size*0.3);
        hairGrad.addColorStop(0, '#B3E5FC');
        hairGrad.addColorStop(1, '#0288D1');
        ctx.fillStyle = hairGrad;
        
        ctx.shadowColor = 'rgba(3, 169, 244, 0.3)';
        ctx.shadowBlur = 5;

        ctx.beginPath();
        ctx.arc(cx, cy - size*0.25, size*0.35, Math.PI, 0); // Top hair
        ctx.lineTo(cx + size*0.35, cy + size*0.2); // Right flowing
        ctx.lineTo(cx - size*0.35, cy + size*0.2); // Left flowing
        ctx.fill();

        // Face - 3D Sphere
        const faceGrad = ctx.createRadialGradient(cx - size*0.05, cy - size*0.25, size*0.05, cx, cy - size*0.2, size*0.25);
        faceGrad.addColorStop(0, '#FFF9C4');
        faceGrad.addColorStop(1, '#FFE082');
        ctx.fillStyle = faceGrad;
        
        ctx.beginPath();
        ctx.arc(cx, cy - size*0.2, size*0.25, 0, Math.PI*2);
        ctx.fill();

        // Reset Shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;

        // Eyes
        ctx.fillStyle = '#1565C0';
        ctx.beginPath(); ctx.arc(cx - size*0.08, cy - size*0.2, size*0.03, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx + size*0.08, cy - size*0.2, size*0.03, 0, Math.PI*2); ctx.fill();

        // Crown (Gold) - 3D
        const crownGrad = ctx.createLinearGradient(cx - size*0.15, cy - size*0.5, cx + size*0.15, cy - size*0.4);
        crownGrad.addColorStop(0, '#FFECB3');
        crownGrad.addColorStop(0.5, '#FFD700');
        crownGrad.addColorStop(1, '#FFECB3');
        ctx.fillStyle = crownGrad;
        
        ctx.shadowColor = 'rgba(255, 215, 0, 0.5)';
        ctx.shadowBlur = 4;
        
        ctx.beginPath();
        ctx.moveTo(cx - size*0.15, cy - size*0.4);
        ctx.lineTo(cx - size*0.08, cy - size*0.55); // Left point
        ctx.lineTo(cx, cy - size*0.45); // Middle dip
        ctx.lineTo(cx + size*0.08, cy - size*0.55); // Right point
        ctx.lineTo(cx + size*0.15, cy - size*0.4);
        ctx.fill();
        
        ctx.shadowColor = 'transparent';
    }

    drawStar(ctx, cx, cy, r, p) {
        ctx.beginPath();
        for(let i=0; i<p*2; i++) {
            const rot = Math.PI/2 * 3;
            const x = cx + Math.cos(rot + i * Math.PI / p) * (i%2 ? r/2 : r);
            const y = cy + Math.sin(rot + i * Math.PI / p) * (i%2 ? r/2 : r);
            ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fill();
    }

    // AI Logic Helpers
    decideMove() {
        const head = this.body[0];
        
        // Priority 0: Exploration Mode (Force move to target)
        if (this.isExploring && this.explorationTarget) {
            // Check if reached (or close enough)
            const dist = Math.hypot(head.x - this.explorationTarget.x, head.y - this.explorationTarget.y);
            if (dist < 2) {
                this.isExploring = false;
                this.explorationTarget = null;
            } else {
                const path = this.bfs(head, this.explorationTarget);
                if (path && path.length > 0) {
                    this.setDirectionTowards(head, path[0]);
                    return;
                }
                // If no path to exploration target, fall back to normal logic (might pick new target later or just survive)
            }
        }

        const foods = this.game.foods.filter(f => f.active);

        // Sort foods by distance (Euclidean as requested)
        foods.sort((a, b) => {
            const da = Math.hypot(a.position.x - head.x, a.position.y - head.y);
            const db = Math.hypot(b.position.x - head.x, b.position.y - head.y);
            return da - db;
        });

        // 1. Try to find path to closest reachable food
        let bestPath = null;
        for (let food of foods) {
            // Limit search depth/time if needed, but grid is small enough for BFS
            const path = this.bfs(head, food.position);
            if (path) {
                bestPath = path;
                break; // Found path to closest reachable food
            }
        }

        if (bestPath && bestPath.length > 0) {
            const nextStep = bestPath[0];
            this.setDirectionTowards(head, nextStep);
            return;
        }

        // 2. If no food reachable, survive (Wander / Chase Tail)
        // Simple heuristic: pick move that maximizes available space (Flood Fill)
        const safeMoves = this.getSafeMoves(head);
        
        if (safeMoves.length === 0) return; // No hope

        let bestMove = safeMoves[0];
        let maxSpace = -1;

        // Shuffle moves to avoid bias
        safeMoves.sort(() => Math.random() - 0.5);

        for (let move of safeMoves) {
            const nextPos = this.getNewHeadPosition(head, move);
            // Quick flood fill (limit depth to save perf)
            const space = this.measureSpace(nextPos, 100); 
            if (space > maxSpace) {
                maxSpace = space;
                bestMove = move;
            }
        }

        this.nextDirection = bestMove;
    }

    bfs(start, target) {
        const queue = [[start]];
        const visited = new Set();
        visited.add(`${start.x},${start.y}`);

        // Limit iterations to prevent lag
        let iterations = 0;
        const maxIterations = this.game.cols * this.game.rows; // Dynamic limit based on grid size 

        while (queue.length > 0) {
            if (iterations++ > maxIterations) return null;
            
            const path = queue.shift();
            const current = path[path.length - 1];

            if (current.x === target.x && current.y === target.y) {
                return path.slice(1); // Return steps excluding start
            }

            const moves = [
                {x: 0, y: -1}, {x: 0, y: 1}, 
                {x: -1, y: 0}, {x: 1, y: 0}
            ];

            for (let move of moves) {
                const next = this.getNewHeadPosition(current, move);
                
                // Validate Move
                if (!this.isSafe(next)) continue;

                const key = `${next.x},${next.y}`;
                if (!visited.has(key)) {
                    visited.add(key);
                    const newPath = [...path, next];
                    queue.push(newPath);
                }
            }
        }
        return null;
    }

    measureSpace(startNode, limit) {
        let count = 0;
        const queue = [startNode];
        const visited = new Set();
        visited.add(`${startNode.x},${startNode.y}`);

        while (queue.length > 0 && count < limit) {
            const current = queue.shift();
            count++;

            const moves = [
                {x: 0, y: -1}, {x: 0, y: 1}, 
                {x: -1, y: 0}, {x: 1, y: 0}
            ];

            for (let move of moves) {
                const next = this.getNewHeadPosition(current, move);
                if (this.isSafe(next)) {
                    const key = `${next.x},${next.y}`;
                    if (!visited.has(key)) {
                        visited.add(key);
                        queue.push(next);
                    }
                }
            }
        }
        return count;
    }

    getSafeMoves(fromPos) {
        const moves = [
            {x: 0, y: -1}, {x: 0, y: 1}, 
            {x: -1, y: 0}, {x: 1, y: 0}
        ];
        
        return moves.filter(move => {
            // Prevent 180 reverse
            if (move.x + this.direction.x === 0 && move.y + this.direction.y === 0) return false;
            
            const next = this.getNewHeadPosition(fromPos, move);
            return this.isSafe(next);
        });
    }

    getNewHeadPosition(pos, move) {
        let nextPos = { x: pos.x + move.x, y: pos.y + move.y };
        if (this.game.settings.noBoundary) {
            if (nextPos.x < 0) nextPos.x = this.game.cols - 1;
            if (nextPos.x >= this.game.cols) nextPos.x = 0;
            if (nextPos.y < 0) nextPos.y = this.game.rows - 1;
            if (nextPos.y >= this.game.rows) nextPos.y = 0;
        }
        return nextPos;
    }

    isSafe(pos) {
        // 1. Boundary
        if (!this.game.settings.noBoundary) {
            if (pos.x < 0 || pos.x >= this.game.cols || pos.y < 0 || pos.y >= this.game.rows) return false;
        }

        // 2. Self (Body) - Be conservative, treat whole body as obstacle
        if (this.onSnake(pos, true)) return false;

        // 3. Other Snakes
        if (this.game.snakes) {
            for (let other of this.game.snakes) {
                if (other === this) continue;
                if (other.onSnake(pos)) return false;
            }
        }
        
        // 4. Obstacles
        if (this.game.settings.obstacles && this.game.obstacles) {
            for (let obs of this.game.obstacles) {
                if (Utils.isSamePosition(pos, obs)) return false;
            }
        }

        return true;
    }

    setDirectionTowards(from, to) {
        let dx = to.x - from.x;
        let dy = to.y - from.y;

        // Handle wrapping direction
        if (this.game.settings.noBoundary) {
            const w = this.game.cols;
            const h = this.game.rows;
            if (dx > w / 2) dx -= w;
            else if (dx < -w / 2) dx += w;
            if (dy > h / 2) dy -= h;
            else if (dy < -h / 2) dy += h;
        }

        this.nextDirection = { x: dx, y: dy };
    }
}
