# ZLX Chatroom System

这是一个基于 Flask 的多模块 Web 应用，支持多人协同开发。

## 模块说明

系统包含以下四个主要模块：

1.  **Chat (聊天应用)**: 负责用户之间的实时聊天功能。
    -   路径: `/chat`
    -   代码: `app/chat/`
2.  **Bot (机器人)**: 负责智能机器人交互功能。
    -   路径: `/bot`
    -   代码: `app/bot/`
3.  **Game (游戏)**: 负责前端游戏功能。
    -   路径: `/game`
    -   代码: `app/game/`
4.  **Admin (后台管理)**: 负责系统管理和配置。
    -   路径: `/admin`
    -   代码: `app/admin/`

## 开发指南

### 环境准备

1.  创建虚拟环境 (可选):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```
2.  安装依赖:
    ```bash
    pip install -r requirements.txt
    ```
3.  初始化数据库:
    ```bash
    # Windows PowerShell
    $env:FLASK_APP = "run.py"
    flask db init      # 仅首次需要
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

### 运行应用

```bash
python run.py
```

访问 `http://localhost:5555` 查看首页。

### 目录结构

```
zlxchatroom/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── extensions.py        # 扩展初始化 (DB, SocketIO, Migrate)
│   ├── models.py            # 数据模型
│   ├── chat/                # 聊天模块 (Blueprint)
│   ├── bot/                 # 机器人模块 (Blueprint)
│   ├── game/                # 游戏模块 (Blueprint)
│   ├── admin/               # 管理模块 (Blueprint)
│   ├── static/              # 全局静态文件
│   └── templates/           # 全局模板
├── config.py                # 配置
├── run.py                   # 启动脚本
└── requirements.txt         # 依赖
```

## 多人协同开发工作流

为了适应5人团队同时开发，建议遵循以下规范：

1.  **模块化开发**:
    -   每位成员负责不同的模块（如 A 负责 Chat，B 负责 Game）。
    -   尽量在各自的 Blueprint 目录下工作 (`app/chat`, `app/game` 等)，避免修改全局文件 (`app/__init__.py`)。

2.  **数据库变更**:
    -   修改 `app/models.py` 后，执行 `flask db migrate -m "描述"` 生成迁移脚本。
    -   提交代码前，确保本地 `flask db upgrade` 成功。
    -   拉取他人代码后，第一时间执行 `flask db upgrade` 同步数据库结构。

3.  **依赖管理**:
    -   引入新库时，使用 `pip freeze > requirements.txt` 更新依赖文件。

4.  **静态文件与模板**:
    -   各模块的特有资源放在 `app/<module>/static` 和 `app/<module>/templates`。
    -   公共资源放在 `app/static` 和 `app/templates`。
