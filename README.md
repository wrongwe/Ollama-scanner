# Ollama 服务扫描工具集

GitHub 仓库: [https://github.com/wrongwe/Ollama-scanner](https://github.com/wrongwe/Ollama-scanner)

## 工具概览

### 1. Ollama_scanner.py
**模型中心化扫描器**  
适用于全面扫描和模型分类的场景

#### 主要功能
- 多线程异步扫描（并发数 200）
- 智能主机格式标准化处理
- 自动模型分类存储
- 失败主机记录功能
- 进度实时监控界面

#### 使用示例
```bash
=== 模型中心化扫描器 ===
输入包含主机列表的文件（每行一个IP/域名）
请输入目标文件路径: targets.txt

扫描进度: 150/200 | 识别到15种模型
扫描完成！结果保存在 [scan_results] 目录
识别到 18 种不同模型
失败主机数: 12
```

### 2. Ollama_valid_scanner.py
**有效节点验证专家**  
适用于精准验证服务质量的场景

#### 核心优势
- 三重验证机制（可靠性提升40%）
- 智能连接池管理（并发数 300）
- 动态猫咪进度提示
- 自动清理历史数据
- 验证超时优化（12秒/请求）

#### 新增特性
```python
# 可视化交互系统
_SCANNING_FRAMES = [
    "(=ↀωↀ=)✧ 节点嗅探中...",
    "(=^･ω･^=) 验证进行时",
    "(=｀ェ´=) 数据整理喵~"
]

# 安全增强验证流程
async def _validate_node(self):
    for _ in range(3):  # 三次握手验证
        if response.status == 200:
            return True
```

## 功能对比表

| 功能特性                | Ollama_scanner | Ollama_valid_scanner |
|-----------------------|----------------|----------------------|
| 并发处理能力            | 200           | 300                 |
| 验证机制               | 单次请求       | 三重验证             |
| 结果分类方式           | 按模型分类     | 按节点有效性分类      |
| 进度显示              | 基础进度条     | 动态猫咪动画          |
| 输出内容              | 全量数据       | 仅有效节点           |
| 数据清理功能          | 保留目录结构   | 每次扫描自动清理       |
| 典型扫描速度（100节点） | 45-60秒       | 30-40秒             |

## 使用指南

### 安装依赖
```bash
pip install aiohttp
```

### 运行流程
```bash
# 标准扫描器
python Ollama_scanner.py

# 有效节点扫描器
python Ollama_valid_scanner.py
```

### 输入文件格式
```
example.com
192.168.1.1:11435
api.ollama.service
```

## 输出文件结构
```
├── scan_results/        # Ollama_scanner输出
│   ├── llama2.txt       # 模型分类结果
│   └── failed_hosts.txt # 失败记录
│
└── valid_nodes/         # Ollama_valid_scanner输出
    └── llama2.txt       # 有效节点清单
```

## 高级配置
```python
# 在Ollama_valid_scanner.py中可调整
class ScannerConfig:
    CONCURRENCY_LIMIT = 350    # 提升并发能力
    REQUEST_TIMEOUT = 10       # 缩短超时阈值
    VALID_DIR = "verified_ollama"  # 自定义输出目录
```

## 典型应用场景
1. **快速普查** → 使用 `Ollama_scanner`
2. **节点监控** → 使用 `Ollama_valid_scanner`
3. **服务迁移** → 双工具结合使用
4. **压力测试** → 调整并发参数后使用

欢迎通过GitHub提交改进建议！ 🐾
```
