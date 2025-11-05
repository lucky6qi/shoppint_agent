# AH购物代理

一个简化的购物代理，用于爬取AH.nl打折商品、管理购物清单历史，并生成智能购物bucket分类。

## 功能

- 🕷️ **爬取打折商品**: 自动爬取ah.nl/bonus页面的所有打折商品信息
- 📊 **商品总结**: 自动总结所有打折商品，按折扣分类
- 📋 **购物清单历史数据库**: 本地JSON数据库，支持索引和多种查询方式
  - 按日期查询（精确日期或日期范围）
  - 按商品名称查询
  - 按类别查询
  - 按备注关键词查询
  - 综合搜索
  - 统计信息（最常购买商品、平均商品数等）
- 🤖 **智能分类**: 根据base_prompt生成base bucket，将商品分类到不同类别
- 🛒 **购物车自动化**: 优雅的自动化接口，一键将商品添加到AH购物车
  - 支持批量添加商品
  - 自动处理登录和cookie
  - 支持从bucket直接添加
  - 进度回调和错误处理

## 安装

### 使用uv (推荐)

```bash
# 安装uv (如果还没有)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd shoppint_agent

# 安装依赖
uv sync

# 运行
uv run python main.py
```

### 手动安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt  # 或直接使用 uv pip install

# 运行
python main.py
```

## 配置

### 环境变量

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

或者在代码中直接设置（不推荐用于生产环境）。

## 使用方法

### 基本使用

```bash
python main.py
```

程序会依次执行：
1. 爬取ah.nl/bonus页面的所有打折商品
2. 生成商品总结
3. 显示最近10次购物清单
4. 根据base_prompt生成base bucket分类
5. 可选择保存购物清单到历史

### 代码使用

```python
from config import Config
from scraper import AHBonusScraper
from history import ShoppingHistory
from bucket_generator import BucketGenerator

# 初始化
config = Config()
scraper = AHBonusScraper(config)
history = ShoppingHistory()

# Scrape products
products = scraper.scrape_bonus_products()

# Generate summary
summary = scraper.summarize_products(products)

# Get history
recent_lists = history.get_recent_lists(10)

# Generate bucket
generator = BucketGenerator(api_key="your_key")
buckets = generator.generate_buckets(
    products=products,
    user_requirements="Buy healthy ingredients for a week"
)

# Query shopping lists
# Query by product name
results = history.query_by_product("melk")
print(f"Found {len(results)} shopping lists containing 'melk'")

# Query by date
results = history.query_by_date(date_str="2024-01-15")
results = history.query_by_date(start_date="2024-01-01", end_date="2024-01-31")

# Query by category
results = history.query_by_category("meat")

# Comprehensive search
results = history.search("kip")

# Get statistics
stats = history.get_statistics()
print(f"Total shopping lists: {stats['total_lists']}")
print(f"Most frequently purchased products: {stats['top_products'][:5]}")
```

### 购物车自动化

```python
from cart_automation import add_to_cart_simple, add_buckets_to_cart, CartAutomation

# Method 1: Simple add products
products = [
    {"title": "AH Halfvolle melk", "product_url": "https://..."},
    {"title": "AH Eieren", "product_url": "https://..."}
]
result = add_to_cart_simple(products)
print(f"Successfully added {result.added_count} products")

# Method 2: Add from buckets (recommended)
result = add_buckets_to_cart(buckets)
print(f"Successfully added {result.added_count} products")

# Method 3: Use context manager (more flexible)
with CartAutomation() as cart:
    result = cart.add_from_buckets(buckets)
    if result.success:
        cart.view_cart()  # View cart
```

## 项目结构

```
shoppint_agent/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── scraper.py           # 爬虫模块
├── history.py           # 购物清单历史数据库（支持索引和查询）
├── bucket_generator.py  # bucket生成器
├── cart_automation.py    # 购物车自动化模块
├── query_examples.py    # 查询功能示例
├── cart_examples.py     # 购物车使用示例
├── example_usage.py     # 使用示例
├── test_shopping_agent.ipynb  # 测试notebook
├── pyproject.toml      # 项目配置（uv）
└── README.md           # 说明文档
```

## 数据文件

- `shopping_history.json`: 购物清单历史数据库（JSON格式，包含索引）
  - 自动索引：按日期、商品名称、类别
  - 支持快速查询和搜索
- `products_cache.json`: 商品数据缓存

### 数据库结构

```json
{
  "version": "1.0",
  "metadata": {
    "created_at": "2024-01-01T00:00:00",
    "last_updated": "2024-01-15T00:00:00"
  },
  "lists": [
    {
      "id": "uuid",
      "date": "2024-01-15T10:30:00",
      "items": [...],
      "notes": "Notes",
      "total_items": 10
    }
  ],
  "indexes": {
    "by_date": {...},
    "by_product": {...},
    "by_category": {...}
  }
}
```

## 依赖

- `beautifulsoup4`: HTML解析
- `requests`: HTTP请求
- `selenium`: 浏览器自动化
- `webdriver-manager`: Chrome驱动管理
- `anthropic`: Claude API

## 注意事项

1. 需要安装Chrome浏览器
2. 首次运行会自动下载ChromeDriver
3. 爬取过程可能需要几分钟时间
4. 需要Anthropic API key才能使用bucket生成功能

## License

MIT
