"""
Ollama 超速扫描验证系统【有效节点专版】
版本: 3.3-miao
功能：
1. 仅输出有效节点报告
2. 优化扫描性能
3. 强化验证机制
"""
import re
import asyncio
import aiohttp
import signal
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse
from typing import List

# ================= 喵星人视觉系统 =================
_MAIN_CAT = r"""
　　　／l丶　　　　　　＿＿
　　（ﾟ､ ｡ ７　　　／⌒ヽ　 
　  l　 ~ヽ　　　/ へ　 ヽ 
　　じしf_, )ノ／ﾆ､　 　l　 
　　　　　｜/　(__ノヽ＿ノ
"""

_SCANNING_FRAMES = [
    r"(=ↀωↀ=)✧ 节点嗅探中...",
    r"(=^･ω･^=) 验证进行时",
    r"(=｀ェ´=) 数据整理喵~"
]

# ================= 核心配置类 =================
class ScannerConfig:
    CONCURRENCY_LIMIT = 300     # 并发连接数
    REQUEST_TIMEOUT = 12        # 超时时间
    DEFAULT_PORT = 11434        # 服务端口
    VALID_DIR = "valid_nodes"   # 有效节点目录

# ================= 主扫描器类 =================
class OllamaCatScanner:
    def __init__(self):
        self._show_startup_cat()
        self.valid_nodes = defaultdict(list)
        self.scanned_targets = set()
        self.running = True

        self._init_signal_handler()
        self._prepare_workspace()

    def _show_startup_cat(self):
        """显示启动画面"""
        print("\033[2J\033[H")  # 清屏
        print("\033[36m" + _MAIN_CAT + "\033[0m")
        print("\033[33m★☆★ Ollama 有效节点猎手 ★☆★\033[0m\n")

    # ================= 系统初始化 =================
    def _init_signal_handler(self):
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    def _prepare_workspace(self):
        """准备输出目录"""
        valid_dir = Path(ScannerConfig.VALID_DIR)
        valid_dir.mkdir(exist_ok=True, parents=True)
        # 清理旧数据
        for f in valid_dir.glob("*.txt"):
            f.unlink()

    # ================= 核心扫描逻辑 =================
    async def _probe_service(self, session: aiohttp.ClientSession, host: str):
        """服务探测"""
        try:
            async with session.get(
                f"http://{host}/api/tags",
                timeout=aiohttp.ClientTimeout(total=ScannerConfig.REQUEST_TIMEOUT)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception:
            return []

    async def _validate_node(self, session: aiohttp.ClientSession, host: str, model: str):
        """三重验证机制"""
        for _ in range(3):  # 增加验证次数
            try:
                async with session.post(
                    f"http://{host}/api/generate",
                    json={"model": model, "prompt": "ping"},
                    timeout=aiohttp.ClientTimeout(total=ScannerConfig.REQUEST_TIMEOUT)
                ) as response:
                    if response.status == 200:
                        return True
            except Exception:
                continue
        return False

    # ================= 任务调度系统 =================
    async def _worker(self, session: aiohttp.ClientSession, queue: asyncio.Queue):
        """工作线程"""
        while self.running and not queue.empty():
            target = await queue.get()
            try:
                parsed = urlparse(target if '://' in target else f"http://{target}")
                host = f"{parsed.hostname}:{parsed.port or ScannerConfig.DEFAULT_PORT}"

                if host in self.scanned_targets:
                    continue

                # 执行深度验证
                models = await self._probe_service(session, host)
                if models:
                    async with aiohttp.ClientSession() as validation_session:
                        for model in set(models):
                            if await self._validate_node(validation_session, host, model):
                                self.valid_nodes[model].append(host)

                self.scanned_targets.add(host)
            finally:
                queue.task_done()

    # ================= 进度显示系统 =================
    async def _dynamic_display(self, total: int):
        """动态显示"""
        frame_idx = 0
        while self.running:
            frame = _SCANNING_FRAMES[frame_idx % len(_SCANNING_FRAMES)]
            print(f"\r{frame}  已验证节点: {len(self.scanned_targets)}/{total}", end="")
            frame_idx += 1
            await asyncio.sleep(0.4)

    # ================= 报告生成系统 =================
    def _generate_reports(self):
        """生成有效节点报告"""
        for model, hosts in self.valid_nodes.items():
            self._save_report(
                Path(ScannerConfig.VALID_DIR)/f"{self._safe_name(model)}.txt",
                hosts
            )

    def _save_report(self, path: Path, hosts: list):
        """保存报告"""
        try:
            with path.open('w', encoding='utf-8') as f:
                f.write("\n".join(sorted(hosts)))
        except Exception as e:
            print(f"\n[!] 报告保存失败: {path.name} - {str(e)}")

    def _safe_name(self, name: str) -> str:
        """文件名安全处理"""
        return re.sub(r'[\\/*?:"<>|]', "_", name).replace(" ", "_").lower()[:45]

    # ================= 主流程控制 =================
    async def execute_scan(self, targets: List[str]):
        """执行扫描任务"""
        queue = asyncio.Queue()
        unique_targets = list(set(targets))
        total = len(unique_targets)

        for target in unique_targets:
            await queue.put(target)

        # 启动进度显示
        display_task = asyncio.create_task(self._dynamic_display(total))

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=ScannerConfig.CONCURRENCY_LIMIT),
            headers={'User-Agent': 'OllamaCatScanner/3.3'}
        ) as session:
            workers = [asyncio.create_task(self._worker(session, queue))
                      for _ in range(ScannerConfig.CONCURRENCY_LIMIT)]

            try:
                await queue.join()
            finally:
                self.running = False
                await asyncio.gather(*workers, return_exceptions=True)
                display_task.cancel()
                self._generate_reports()

    def graceful_shutdown(self, signum=None, frame=None):
        """优雅关闭"""
        print("\n[系统] 正在安全退出...")
        sys.exit(0)

# ================= 主程序入口 =================
if __name__ == "__main__":
    scanner = OllamaCatScanner()

    # 文件输入交互
    while True:
        try:
            input_file = input("\n(^=◕ᴥ◕=^) 请输入目标文件路径: ").strip()
            if not input_file:
                print("[!] 必须输入有效路径")
                continue

            target_path = Path(input_file).expanduser().resolve()
            if not target_path.exists():
                print(f"[!] 文件不存在: {target_path}")
                continue

            with target_path.open() as f:
                targets = [ln.strip() for ln in f if ln.strip()]
            if not targets:
                print("[!] 文件内容为空")
                continue
            break
        except Exception as e:
            print(f"[!] 文件错误: {str(e)}")

    # 执行扫描
    try:
        asyncio.run(scanner.execute_scan(targets))
    except KeyboardInterrupt:
        scanner.graceful_shutdown()
    finally:
        # 最终输出
        total_valid = sum(len(v) for v in scanner.valid_nodes.values())
        print(f"\n\n[最终报告] 有效节点总数: {total_valid}")
        print(f"保存路径: {Path(ScannerConfig.VALID_DIR).resolve()}")
        print("(=^‥^=) 任务完成！")