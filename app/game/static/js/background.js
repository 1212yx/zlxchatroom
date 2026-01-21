class CyberpunkBackground {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.gridOffset = { x: 0, y: 0 };
        this.neonHue = 180; // 青色起始值
        this.lastPulseTime = 0;
        this.animationId = null;
        
        // 性能配置
        this.particleCount = 5000;
        this.gridSize = 50;
        this.isHighPerformance = this.detectPerformance();
    }

    detectPerformance() {
        // 根据设备性能自动调整
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        return !isMobile && window.devicePixelRatio <= 2;
    }

    init() {
        this.createCanvas();
        this.setupEventListeners();
        this.createParticles();
        this.startAnimation();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100vw';
        this.canvas.style.height = '100vh';
        this.canvas.style.zIndex = '-1';
        this.canvas.style.pointerEvents = 'none';
        
        this.resizeCanvas();
        document.body.appendChild(this.canvas);
    }

    resizeCanvas() {
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = window.innerWidth * dpr;
        this.canvas.height = window.innerHeight * dpr;
        this.ctx.scale(dpr, dpr);
        
        // 调整性能设置
        this.adjustPerformanceSettings();
    }

    adjustPerformanceSettings() {
        const width = window.innerWidth;
        if (width < 768) {
            this.particleCount = 1000; // 移动端减少粒子
        } else if (width < 1280) {
            this.particleCount = 3000; // 中等屏幕
        } else {
            this.particleCount = 5000; // 大屏幕
        }
        
        this.createParticles(); // 重新创建粒子
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.resizeCanvas();
        });

        // 性能监控
        this.setupPerformanceMonitor();
    }

    setupPerformanceMonitor() {
        let lastTime = performance.now();
        let frameCount = 0;
        
        const checkPerformance = () => {
            frameCount++;
            const now = performance.now();
            
            if (now - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (now - lastTime));
                
                if (fps < 30 && this.particleCount > 1000) {
                    this.particleCount = Math.max(1000, this.particleCount - 1000);
                    this.createParticles();
                }
                
                frameCount = 0;
                lastTime = now;
            }
            
            requestAnimationFrame(checkPerformance);
        };
        
        checkPerformance();
    }

    createParticles() {
        this.particles = [];
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                size: 2 + Math.random() * 2,
                speed: 0.1 + Math.random() * 0.1,
                angle: Math.random() * Math.PI * 2,
                noiseOffset: Math.random() * 1000,
                alpha: 0.3 + Math.random() * 0.2
            });
        }
    }

    drawGrid() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        this.ctx.strokeStyle = 'rgba(0, 255, 255, 0.1)';
        this.ctx.lineWidth = 1;
        
        // 水平网格线
        for (let y = this.gridOffset.y % this.gridSize; y < height; y += this.gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(width, y);
            this.ctx.stroke();
        }
        
        // 垂直网格线
        for (let x = this.gridOffset.x % this.gridSize; x < width; x += this.gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, height);
            this.ctx.stroke();
        }
        
        // 网格移动动画
        this.gridOffset.x += 0.2;
        this.gridOffset.y += 0.2;
    }

    drawNeonTubes() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        // 霓虹色调变化
        this.neonHue = (this.neonHue + 0.3) % 360;
        const neonColor = `hsla(${this.neonHue}, 100%, 50%, 0.8)`;
        const purpleColor = 'hsla(270, 100%, 50%, 0.8)';
        
        // 绘制四边框霓虹灯管
        this.ctx.strokeStyle = neonColor;
        this.ctx.lineWidth = 3;
        this.ctx.shadowBlur = 15;
        this.ctx.shadowColor = neonColor;
        
        // 上边框
        this.ctx.beginPath();
        this.ctx.moveTo(20, 20);
        this.ctx.lineTo(width - 20, 20);
        this.ctx.stroke();
        
        // 右边框
        this.ctx.beginPath();
        this.ctx.moveTo(width - 20, 20);
        this.ctx.lineTo(width - 20, height - 20);
        this.ctx.stroke();
        
        // 下边框
        this.ctx.beginPath();
        this.ctx.moveTo(width - 20, height - 20);
        this.ctx.lineTo(20, height - 20);
        this.ctx.stroke();
        
        // 左边框
        this.ctx.beginPath();
        this.ctx.moveTo(20, height - 20);
        this.ctx.lineTo(20, 20);
        this.ctx.stroke();
        
        this.ctx.shadowBlur = 0;
    }

    drawParticles(time) {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        this.particles.forEach(particle => {
            // 使用Perlin噪声生成平滑运动
            const noise = this.perlinNoise(
                particle.noiseOffset + time * 0.001,
                particle.noiseOffset * 0.5
            );
            
            particle.angle = noise * Math.PI * 2;
            particle.x += Math.cos(particle.angle) * particle.speed;
            particle.y += Math.sin(particle.angle) * particle.speed;
            
            // 边界环绕
            if (particle.x < 0) particle.x = width;
            if (particle.x > width) particle.x = 0;
            if (particle.y < 0) particle.y = height;
            if (particle.y > height) particle.y = 0;
            
            // 绘制粒子
            this.ctx.fillStyle = `rgba(0, 255, 255, ${particle.alpha})`;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fill();
        });
    }

    drawEnergyPulse(time) {
        if (time - this.lastPulseTime > 8000) {
            this.lastPulseTime = time;
            
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 2;
            const maxRadius = Math.max(window.innerWidth, window.innerHeight) * 1.5;
            
            const pulse = {
                radius: window.innerHeight * 0.05,
                maxRadius: maxRadius,
                progress: 0,
                color: `hsla(${this.neonHue}, 100%, 70%, 0.3)`
            };
            
            const animatePulse = () => {
                pulse.progress += 0.02;
                if (pulse.progress >= 1) return;
                
                const radius = pulse.radius + (pulse.maxRadius - pulse.radius) * pulse.progress;
                const alpha = 0.3 * (1 - pulse.progress);
                
                this.ctx.fillStyle = `hsla(${this.neonHue}, 100%, 70%, ${alpha})`;
                this.ctx.beginPath();
                this.ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
                this.ctx.fill();
                
                requestAnimationFrame(animatePulse);
            };
            
            animatePulse();
        }
    }

    perlinNoise(x, y) {
        // 简化版Perlin噪声
        const X = Math.floor(x) & 255;
        const Y = Math.floor(y) & 255;
        x -= Math.floor(x);
        y -= Math.floor(y);
        
        const u = this.fade(x);
        const v = this.fade(y);
        
        const A = this.p[X] + Y;
        const B = this.p[X + 1] + Y;
        
        return this.lerp(
            u,
            this.lerp(v, this.grad(this.p[A], x, y), this.grad(this.p[B], x - 1, y)),
            this.lerp(v, this.grad(this.p[A + 1], x, y - 1), this.grad(this.p[B + 1], x - 1, y - 1))
        ) * 0.5 + 0.5;
    }

    fade(t) {
        return t * t * t * (t * (t * 6 - 15) + 10);
    }

    lerp(t, a, b) {
        return a + t * (b - a);
    }

    grad(hash, x, y) {
        const h = hash & 15;
        const u = h < 8 ? x : y;
        const v = h < 4 ? y : h === 12 || h === 14 ? x : 0;
        return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
    }

    p = [151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,224,232,178,185,112,104,218,246,97,228,251,34,242,193,238,210,144,12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180];

    startAnimation() {
        const animate = (time) => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.drawGrid();
            this.drawNeonTubes();
            this.drawParticles(time);
            this.drawEnergyPulse(time);
            
            this.animationId = requestAnimationFrame(animate);
        };
        
        this.animationId = requestAnimationFrame(animate);
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}

// 全局访问
window.CyberpunkBackground = CyberpunkBackground;