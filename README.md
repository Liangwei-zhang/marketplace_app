# Marketplace App - 二手交易平台

## 项目状态

### ✅ 已完成

| 模块 | 功能 | 状态 |
|------|------|------|
| **后端** | FastAPI + SQLModel + PostgreSQL | ✅ |
| **认证** | 用户注册/登录/JWT + 限流 | ✅ |
| **密码重置** | 邮箱验证码 | ✅ |
| **商品 CRUD** | 发布/编辑/删除/查看 | ✅ |
| **图片上传** | 压缩存储（本地） | ✅ |
| **商品分类** | 7 个分类 | ✅ |
| **LBS 搜索** | PostGIS 高效半径搜索 | ✅ |
| **即时通讯** | WebSocket 实时聊天 + 图片 | ✅ |
| **交易流程** | 创建/确认/完成/取消 | ✅ |
| **评价系统** | 交易完成后互相评价 | ✅ |
| **举报机制** | 欺诈/虚假商品举报 | ✅ |
| **后台管理** | 仪表盘/用户管理 | ✅ |
| **收藏功能** | 商品收藏 | ✅ |
| **用户头像** | 头像上传 | ✅ |
| **前端** | HTML + JS 原生页面 | ✅ |
| **Docker** | 一键部署 | ✅ |
| **安全** | Rate limiting, datetime 修复 | ✅ |

### ⏳ 可选增强

- [ ] 推送通知（WebPush）
- [ ] 商品浏览历史
- [ ] 用户关注
- [ ] 消息已读状态
- [ ] 搜索历史记录
- [ ] 数据统计/Analytics

## 技术栈

- **后端**: FastAPI + SQLModel + PostgreSQL + PostGIS
- **认证**: JWT + bcrypt
- **图片**: Pillow 压缩
- **WebSocket**: 原生 FastAPI
- **前端**: 原生 HTML/CSS/JS
- **部署**: Docker + docker-compose

## 快速启动

### Docker（推荐）
```bash
git clone https://github.com/Liangwei-zhang/marketplace_app.git
cd marketplace_app
docker-compose up -d
```

### 本地开发
```bash
pip install -r requirements.txt
# 启动 PostgreSQL + PostGIS
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000
