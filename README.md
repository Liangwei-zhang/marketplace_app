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
| **前端** | HTML + JS 原生页面 | ✅ |

### 🔄 进行中

- [ ] 评价系统
- [ ] 举报机制
- [ ] 支付集成

### ⏳ 待开发

- [ ] 消息图片发送（前端）
- [ ] 推送通知
- [ ] 商品收藏
- [ ] 用户头像上传
- [ ] 后台管理面板
- [ ] Docker 部署配置

## 技术栈

- **后端**: FastAPI + SQLModel + PostgreSQL + PostGIS
- **认证**: JWT + bcrypt
- **图片**: Pillow 压缩
- **WebSocket**: 原生 FastAPI
- **前端**: 原生 HTML/CSS/JS

## 快速启动

```bash
# 1. 安装依赖
cd marketplace_app
pip install -r requirements.txt

# 2. 启动 PostgreSQL + PostGIS
sudo -u postgres psql -d marketplace -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# 3. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
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
│   └── WebSocket 聊天 websocket/    #
├── public/           # 前端页面
├── tests/            # 测试
└── requirements.txt
```
