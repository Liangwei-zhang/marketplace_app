# Marketplace App - 二手交易平台

## 项目状态

### ✅ 已完成

| 模块 | 功能 | 状态 |
|------|------|------|
| **后端** | FastAPI + SQLModel + PostgreSQL | ✅ |
| **认证** | 用户注册/登录/JWT | ✅ |
| **密码重置** | 邮箱验证码（开发模式返回 token） | ✅ |
| **商品 CRUD** | 发布/编辑/删除/查看 | ✅ |
| **图片上传** | 压缩存储（本地） | ✅ |
| **商品分类** | 7 个分类 | ✅ |
| **LBS 搜索** | PostGIS 高效半径搜索 | ✅ |
| **即时通讯** | WebSocket 实时聊天 | ✅ |
| **交易流程** | 创建/确认/完成/取消 | ✅ |
| **评价系统** | 交易完成后互相评价 | ✅ |
| **举报机制** | 欺诈/虚假商品举报 | ✅ |
| **后台管理** | 仪表盘/用户管理 | ✅ |
| **前端** | HTML + JS 原生页面 | ✅ |
| **Docker** | 一键部署 | ✅ |

### ⏳ 待开发

- [ ] 消息图片发送（前端）
- [ ] 推送通知
- [ ] 商品收藏
- [ ] 用户头像上传

## 技术栈

- **后端**: FastAPI + SQLModel + PostgreSQL + PostGIS
- **认证**: JWT + bcrypt
- **图片**: Pillow 压缩
- **WebSocket**: 原生 FastAPI
- **前端**: 原生 HTML/CSS/JS
- **部署**: Docker + docker-compose

## Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Liangwei-zhang/marketplace_app.git
cd marketplace_app

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 访问
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# 前端: http://localhost:8000
```

## 本地开发启动

```bash
# 1. 安装依赖
cd marketplace_app
pip install -r requirements.txt

# 2. 启动 PostgreSQL + PostGIS
sudo -u postgres psql -d marketplace -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# 3. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000

## API 文档

启动后访问 http://localhost:8000/docs

## 项目结构

```
marketplace_app/
├── app/
│   ├── api/          # REST API 路由
│   ├── core/         # 配置/数据库/安全
│   ├── models/       # SQLModel 模型
│   ├── schemas/      # Pydantic 验证
│   ├── services/     # 业务逻辑
│   └── websocket/    # WebSocket 聊天
├── public/           # 前端页面
├── tests/            # 测试
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
