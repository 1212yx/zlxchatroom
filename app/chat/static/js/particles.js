/**
 * 智联星队Chat - 动态粒子波浪背景
 * 实现：Canvas 2D
 * 效果：深色背景 + 顶部紫色光晕 + 蓝青色波浪 + 萤火虫粒子 + 波浪飞溅粒子
 */

const canvas = document.getElementById('bgCanvas');
const ctx = canvas.getContext('2d');

let width, height;
let particles = [];
let waves = [];

// 配置参数
const config = {
    bgColor: '#05070a', // 深邃暗色背景
    glowColor: 'rgba(138, 43, 226, 0.15)', // 顶部紫色光晕
    waveColors: [
        'rgba(0, 191, 255, 0.05)', // 淡蓝
        'rgba(0, 255, 255, 0.08)', // 青色
        'rgba(30, 144, 255, 0.1)'  // 深蓝
    ],
    particleCount: 80,
    particleColor: 'rgba(64, 224, 208, 0.8)', // 绿松石/青色
    splashProbability: 0.02 // 波浪飞溅概率
};

// 初始化 Canvas
function init() {
    resize();
    window.addEventListener('resize', resize);
    createParticles();
    createWaves();
    animate();
}

function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
}

// 粒子类
class Particle {
    constructor(isSplash = false, x, y) {
        this.isSplash = isSplash;
        this.reset(x, y);
    }

    reset(x, y) {
        if (this.isSplash) {
            // 飞溅粒子
            this.x = x || Math.random() * width;
            this.y = y || height / 2 + (Math.random() - 0.5) * 100;
            this.vx = (Math.random() - 0.5) * 2;
            this.vy = -Math.random() * 3 - 1; // 向上飞溅
            this.life = 1.0;
            this.decay = Math.random() * 0.02 + 0.01;
            this.radius = Math.random() * 1.5 + 0.5;
        } else {
            // 环境萤火虫粒子
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.life = Math.random() * 0.5 + 0.5; // 透明度
            this.radius = Math.random() * 2 + 1;
            this.phase = Math.random() * Math.PI * 2; // 闪烁相位
        }
    }

    update() {
        if (this.isSplash) {
            this.x += this.vx;
            this.y += this.vy;
            this.vy += 0.05; // 重力
            this.life -= this.decay;
            if (this.life <= 0 || this.y > height) {
                // 飞溅粒子消失后不立即重生，由波浪触发新的
                this.dead = true;
            }
        } else {
            this.x += this.vx;
            this.y += this.vy;
            
            // 边界检查
            if (this.x < 0) this.x = width;
            if (this.x > width) this.x = 0;
            if (this.y < 0) this.y = height;
            if (this.y > height) this.y = 0;

            // 闪烁效果
            this.phase += 0.05;
            this.currentAlpha = 0.3 + Math.abs(Math.sin(this.phase)) * 0.5;
        }
    }

    draw() {
        if (this.dead) return;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        
        if (this.isSplash) {
            ctx.fillStyle = `rgba(100, 255, 255, ${this.life})`;
        } else {
            ctx.fillStyle = config.particleColor.replace('0.8)', `${this.currentAlpha})`);
        }
        
        ctx.fill();
        
        // 淡淡的光晕
        ctx.shadowBlur = 10;
        ctx.shadowColor = this.isSplash ? 'white' : 'cyan';
        ctx.shadowBlur = 0; // 重置以避免影响其他绘制
    }
}

// 波浪类
class Wave {
    constructor(index, total) {
        this.index = index;
        this.total = total;
        this.phase = 0;
        this.speed = 0.01 + index * 0.005;
        this.amplitude = 50 + index * 20;
        this.yOffset = height * 0.6; // 波浪基准高度
    }

    update() {
        this.phase += this.speed;
    }

    draw() {
        ctx.beginPath();
        ctx.moveTo(0, height);
        
        let splashX = -1;
        let splashY = -1;

        for (let x = 0; x <= width; x += 20) {
            // 叠加正弦波
            let y = this.yOffset + 
                    Math.sin(x * 0.005 + this.phase) * this.amplitude + 
                    Math.sin(x * 0.01 + this.phase * 2) * (this.amplitude * 0.5);
            
            ctx.lineTo(x, y);

            // 随机检测波峰产生飞溅
            if (Math.random() < 0.001 && y < this.yOffset - 20) {
                splashX = x;
                splashY = y;
            }
        }

        ctx.lineTo(width, height);
        ctx.closePath();
        ctx.fillStyle = config.waveColors[this.index % config.waveColors.length];
        ctx.fill();

        // 产生飞溅粒子
        if (splashX > 0) {
            createSplash(splashX, splashY);
        }
    }
}

function createParticles() {
    for (let i = 0; i < config.particleCount; i++) {
        particles.push(new Particle(false));
    }
}

function createWaves() {
    for (let i = 0; i < 3; i++) {
        waves.push(new Wave(i, 3));
    }
}

let splashParticles = [];

function createSplash(x, y) {
    for (let i = 0; i < 5; i++) {
        splashParticles.push(new Particle(true, x, y));
    }
}

function animate() {
    ctx.clearRect(0, 0, width, height);

    // 1. 绘制背景
    ctx.fillStyle = config.bgColor;
    ctx.fillRect(0, 0, width, height);

    // 2. 绘制顶部紫色光晕
    let gradient = ctx.createRadialGradient(width / 2, 0, 0, width / 2, 0, height * 0.8);
    gradient.addColorStop(0, config.glowColor);
    gradient.addColorStop(1, 'transparent');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    // 3. 绘制波浪
    waves.forEach(wave => {
        wave.update();
        wave.draw();
    });

    // 4. 绘制环境粒子
    particles.forEach(p => {
        p.update();
        p.draw();
    });

    // 5. 绘制飞溅粒子
    for (let i = splashParticles.length - 1; i >= 0; i--) {
        let p = splashParticles[i];
        p.update();
        p.draw();
        if (p.dead) {
            splashParticles.splice(i, 1);
        }
    }

    requestAnimationFrame(animate);
}

// 启动
window.onload = init;