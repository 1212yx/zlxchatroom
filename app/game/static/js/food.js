class Food {
    constructor(game, type = 'normal') {
        this.game = game;
        this.type = type; // normal, bonus, shorten, invincible
        this.position = this.getRandomPosition();
        this.active = true;
        
        // Static Image Cache (prevent reloading)
        if (!Food.images) {
            Food.images = {
                normal: new Image(),
                bonus: new Image(),
                shorten: new Image(),
                invincible: new Image()
            };
            // Use Flask generated paths if available, or relative paths
            // We need a way to pass these paths from HTML or assume structure
            // Assuming static/images/
            const getPath = (name) => {
                // Check if global variable set in index.html exists, otherwise guess
                if (window.GAME_ASSETS && window.GAME_ASSETS[name]) return window.GAME_ASSETS[name];
                return `/game/static/images/${name}`; 
            };
            
            Food.images.normal.src = getPath('cabbage.svg');
            Food.images.bonus.src = getPath('watermelon.svg');
            Food.images.shorten.src = getPath('chili.svg');
            Food.images.invincible.src = getPath('chicken_leg.svg');
        }

        // 根据类型设置属性
        switch(type) {
            case 'normal':
                this.color = Utils.COLORS.FOOD_NORMAL;
                this.score = 10;
                this.effect = 'grow';
                this.image = Food.images.normal;
                break;
            case 'bonus':
                this.color = Utils.COLORS.FOOD_BONUS;
                this.score = 20; // 基础分翻倍 (10 * 2)
                this.effect = 'grow';
                this.image = Food.images.bonus;
                break;
            case 'shorten':
                this.color = Utils.COLORS.FOOD_SHORTEN;
                this.score = 0; // 不加分，功能性食物
                this.effect = 'shrink';
                this.image = Food.images.shorten;
                break;
            case 'invincible':
                this.color = Utils.COLORS.FOOD_INVINCIBLE;
                this.score = 0; // 不加分，功能性食物
                this.effect = 'invincible';
                this.image = Food.images.invincible;
                break;
        }
    }

    getRandomPosition() {
        // 全图随机生成 (不再局限于蛇身周围)
        // User Request: "食物不止在蛇身周围分布，界面之内都行"
        
        let position;
        let isValid = false;
        let attempts = 0;
        const maxAttempts = 100;

        while (!isValid && attempts < maxAttempts) {
            attempts++;
            position = Utils.randomGridPosition(this.game.cols, this.game.rows);
            isValid = true;

            // Check Snake
            for (let snake of this.game.snakes) {
                if (snake.onSnake(position)) {
                    isValid = false;
                    break;
                }
            }

            // Check Obstacles
            if (isValid && this.game.obstacles) {
                for (let obs of this.game.obstacles) {
                    if (Utils.isSamePosition(obs, position)) {
                        isValid = false;
                        break;
                    }
                }
            }
            
             // Check Food Spacing (Ensure they don't overlap too much)
             if (isValid) {
                 for (let food of this.game.foods) {
                    if (food === this) continue;
                    if (!food.active) continue;
                    // Simple check: don't spawn on exact same spot
                    if (Utils.isSamePosition(position, food.position)) {
                        isValid = false;
                        break;
                    }
                }
             }
        }
        
        // 如果尝试100次都失败，直接返回最后一个位置
        return position;
    }

    // Deprecated: getRandomPositionFallback merged into main logic
    // getRandomPositionFallback() { ... }

    draw(ctx, gridSize) {
        if (!this.active) return;

        const x = this.position.x * gridSize;
        const y = this.position.y * gridSize;
        const size = gridSize;
        const center = size / 2;

        // Draw Image if loaded, otherwise fallback to shape
        if (this.image && this.image.complete && this.image.naturalHeight !== 0) {
             ctx.drawImage(this.image, x, y, size, size);
        } else {
             // Fallback to original shape drawing
            ctx.fillStyle = this.color;
            ctx.beginPath();
            if (this.type === 'normal') {
                // 圆形
                ctx.arc(x + center, y + center, size / 2 - 2, 0, Math.PI * 2);
            } else if (this.type === 'bonus') {
                // 星星 (简化为菱形)
                ctx.moveTo(x + center, y);
                ctx.lineTo(x + size, y + center);
                ctx.lineTo(x + center, y + size);
                ctx.lineTo(x, y + center);
            } else if (this.type === 'shorten') {
                // 矩形
                ctx.rect(x + 2, y + 2, size - 4, size - 4);
            } else if (this.type === 'invincible') {
                // 三角形
                ctx.moveTo(x + center, y + 2);
                ctx.lineTo(x + size - 2, y + size - 2);
                ctx.lineTo(x + 2, y + size - 2);
            }
            ctx.fill();
            ctx.closePath();
        }

        // 闪烁效果 (对于特殊食物)
        if (this.type !== 'normal') {
            ctx.shadowColor = this.color;
            ctx.shadowBlur = 10;
        } else {
            ctx.shadowBlur = 0;
        }
    }
}
