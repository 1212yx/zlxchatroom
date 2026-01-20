const Utils = {
    // 生成随机整数 [min, max)
    randomInt: (min, max) => {
        return Math.floor(Math.random() * (max - min)) + min;
    },

    // 生成随机网格坐标
    randomGridPosition: (cols, rows) => {
        return {
            x: Utils.randomInt(0, cols),
            y: Utils.randomInt(0, rows)
        };
    },

    // 检测两个位置是否重叠
    isSamePosition: (pos1, pos2) => {
        return pos1.x === pos2.x && pos1.y === pos2.y;
    },

    // 颜色常量
    COLORS: {
        SNAKE_HEAD: '#4CAF50',
        SNAKE_BODY: '#81C784',
        SNAKE_HEAD_AI: '#F44336',
        SNAKE_BODY_AI: '#E57373',
        FOOD_NORMAL: '#FF5722',    // 普通食物 - 红色
        FOOD_BONUS: '#FFC107',     // 加分食物 - 金色
        FOOD_SHORTEN: '#00BCD4',   // 缩短食物 - 蓝色/青色
        FOOD_INVINCIBLE: '#9C27B0' // 无敌食物 - 紫色
    }
};
