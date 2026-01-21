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
    },

    // 皮肤定义
    SKINS: {
        default: { head: '#4CAF50', body: '#81C784', name: '经典绿' },
        blue: { head: '#2196F3', body: '#64B5F6', name: '海洋蓝' },
        purple: { head: '#9C27B0', body: '#BA68C8', name: '神秘紫' },
        gold: { head: '#FFC107', body: '#FFD54F', name: '土豪金' },
        dark: { head: '#212121', body: '#616161', name: '暗夜黑' },
        kuromi: { head: '#FFC0CB', body: '#FF0000', name: '宅女琪洛米', type: 'custom', render: 'kuromi' },
        orange_soda: { head: '#FF9800', body: '#FFCC80', name: '橘子汽水', type: 'custom', render: 'orange_soda' },
        flower_fairy: { head: '#FF69B4', body: '#E1BEE7', name: '鲜花精灵', type: 'custom', render: 'flower_fairy' },
        graceful_lady: { head: '#F48FB1', body: '#F8BBD0', name: '婉约佳人', type: 'custom', render: 'graceful_lady' },
        moon_goddess: { head: '#4FC3F7', body: '#FFF176', name: '月亮女神', type: 'custom', render: 'moon_goddess' }
    }
};
