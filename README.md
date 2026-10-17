# 抖音视频/图片批量下载工具

一款简洁高效的抖音内容批量下载工具，支持下载指定博主的视频和图片，并自动整理归类。

## 功能特性

- **批量下载**：支持同时下载多位抖音博主的内容
- **自动分类**：视频和图片自动分类存储
- **断点续传**：智能识别已下载内容，避免重复下载
- **格式转换**：图片自动从 WebP 格式转换为 JPG
- **时间命名**：使用发布时间作为文件名，方便管理
- **去重机制**：通过 URL 特征码识别重复内容
- **UTF-8 编码**：源码、日志、列表与 URL 记录全部以 UTF-8 读写，不受 Windows 默认 GBK 编码影响

## 目录结构

```
douyin/
├── main.py                # 程序入口
├── cli.py                 # 命令行交互界面
├── config.py              # 配置常量
├── paths.py               # 路径管理
├── url_parser.py          # JSON 解析与 URL 提取
├── downloader.py          # 下载与格式转换
├── utils.py               # 工具函数
├── json.log               # API 响应日志（手动导入）
├── download/              # 下载目录（自动生成）
│   ├── aweme_list.json    # 博主列表（自动生成）
│   ├── {博主名称}/
│   │   ├── url.txt        # 已下载 URL 记录
│   │   ├── *.mp4          # 视频文件
│   │   └── picture/       # 图片目录
│   │       └── *.jpg      # 图片文件
│   └── ...
└── README.md              # 说明文档
```

## 使用方法

### 第一步：获取抖音数据

1. 打开抖音网页版 (https://www.douyin.com)
2. 登录后进入目标博主的主页
3. 按 F12 打开开发者工具，切换到 **Network** 标签
4. 向下滚动加载博主所有视频内容
5. 找到类型为 `fetch/xhr` 且包含 `aweme_list` 的请求
6. 复制 Response 内容，追加到 `json.log` 文件中（每行一条 JSON，文件放在脚本目录下；放不进去时程序也会读取下载目录下的同名文件）

### 第二步：运行程序

```bash
python main.py
```

### 第三步：功能选择

程序启动后显示主菜单：

| 指令 | 功能 |
|------|------|
| `a` | 开始下载所有博主的内容 |
| `b` | 删除指定博主（清除已下载内容） |
| `c` | 查看博主列表 |
| `x` | 退出程序 |

## 配置说明

### 修改下载路径

在 [config.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/config.py) 中修改 `CONFIGURED_DOWNLOAD_DIR` 常量：

```python
CONFIGURED_DOWNLOAD_DIR = 'F:/图片/douyin/'  # 修改为你的目标路径
```

该路径不可用时会自动回退到脚本目录下的 `download/`。

### User-Agent 配置

如遇下载失败，可在 [config.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/config.py) 中更新 `HEADER` 字典中的浏览器标识：

```python
HEADER = {
    'User-Agent': '你的浏览器User-Agent',
    ...
}
```

## 环境依赖

- **Python 3.x**
- **Pillow** (图片格式转换)

安装依赖：

```bash
pip install Pillow
```

**标准库依赖**：`urllib`, `ssl`, `json`, `os`, `time`, `socket`, `sys`, `re`, `shutil`, `datetime`

## 项目架构

项目采用模块化设计，各模块职责清晰：

| 模块 | 职责 |
|------|------|
| [main.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/main.py) | 程序入口，初始化和协调各模块 |
| [cli.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/cli.py) | 命令行交互界面，菜单控制 |
| [config.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/config.py) | 配置常量（编码、请求头、路径等） |
| [paths.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/paths.py) | 路径管理（下载目录、文件路径） |
| [url_parser.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/url_parser.py) | JSON 解析与 URL 提取 |
| [downloader.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/downloader.py) | 网络下载、去重、WebP 转 JPG |
| [utils.py](file:///d:/Git%E4%BB%93%E5%BA%93/douyin/utils.py) | 通用工具函数（文件读写、编码处理） |

## 注意事项

1. **文件编码**：`json.log`、`aweme_list.json`、`url.txt` 均按 UTF-8 读取；若为早期未指定编码（GBK）写入的旧文件，程序会自动回退读取，无需手动转码
2. **数据时效性**：抖音 API 数据具有时效性，建议获取后尽快下载
3. **登录状态**：确保抖音账号已登录，否则可能无法获取完整数据
4. **下载频率**：大量下载时建议适当增加延时，避免触发风控
5. **存储空间**：视频文件较大，请确保目标磁盘空间充足

## 免责声明

本工具仅供学习交流使用，请勿用于商业传播或任何盈利性活动。下载内容仅供个人学习研究使用，遵守抖音平台服务协议及相关法律法规。
