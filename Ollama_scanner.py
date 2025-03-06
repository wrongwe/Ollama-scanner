import asyncio
import aiohttp
import os
import re
from collections import defaultdict
from urllib.parse import urlparse

# 配置参数
CONCURRENCY = 200
TIMEOUT = 20
PORT = 11434


class ModelCentricScanner:
    def __init__(self):
        self.model_hosts = defaultdict(list)
        self.failed_hosts = []
        self.output_dir = "scan_results"

    def _init_output(self):
        """初始化输出目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 清理旧数据但保留目录结构
        for f in os.listdir(self.output_dir):
            if f.endswith(".txt"):
                os.remove(os.path.join(self.output_dir, f))

    def _safe_filename(self, model_name):
        """生成安全的文件名"""
        return re.sub(r'[\\/*?:"<>|]', "_", model_name).replace(" ", "_").lower()

    async def _check_host(self, session, host):
        """获取主机的模型列表"""
        try:
            async with session.get(f"http://{host}/api/tags", timeout=TIMEOUT) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return host, [m["name"] for m in data.get("models", [])]
        except:
            return host, None

    async def _worker(self, session, queue):
        """处理队列任务"""
        while not queue.empty():
            raw_host = await queue.get()
            try:
                # 标准化主机格式
                parsed = urlparse(raw_host if '://' in raw_host else f"http://{raw_host}")
                host = f"{parsed.hostname}:{parsed.port if parsed.port else PORT}"

                # 执行检测
                detected_host, models = await self._check_host(session, host)

                if models is not None:
                    for model in set(models):  # 去重处理
                        self.model_hosts[model].append(detected_host)
                else:
                    self.failed_hosts.append(host)

            finally:
                queue.task_done()

    def _save_results(self):
        """保存分类结果"""
        # 保存模型分类
        for model, hosts in self.model_hosts.items():
            filename = os.path.join(self.output_dir, f"{self._safe_filename(model)}.txt")
            with open(filename, "w") as f:
                f.write(f"# {model} 共{len(hosts)}个主机\n")
                f.write("\n".join(sorted(hosts, key=lambda x: x.split(":")[0])))

        # 保存失败列表
        with open(os.path.join(self.output_dir, "failed_hosts.txt"), "w") as f:
            f.write("\n".join(sorted(self.failed_hosts)))

    async def run_scan(self, targets):
        """启动扫描任务"""
        self._init_output()
        queue = asyncio.Queue()

        # 去重处理
        unique_targets = list({t.strip() for t in targets})
        for target in unique_targets:
            await queue.put(target)

        async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=CONCURRENCY),
                headers={'User-Agent': 'ModelScanner/1.0'}
        ) as session:
            workers = [asyncio.create_task(self._worker(session, queue))
                       for _ in range(CONCURRENCY)]

            # 进度监控
            total = len(unique_targets)
            while not queue.empty():
                done = total - queue.qsize()
                print(f"\r扫描进度: {done}/{total} | 识别到{len(self.model_hosts)}种模型", end='')
                await asyncio.sleep(0.5)

            await queue.join()
            for task in workers:
                task.cancel()

        self._save_results()


def get_targets():
    """交互式获取目标"""
    while True:
        path = input("请输入目标文件路径: ").strip()
        if os.path.isfile(path):
            with open(path) as f:
                return [line.strip() for line in f if line.strip()]
        print("文件不存在，请重新输入！")


if __name__ == '__main__':
    print("=== 模型中心化扫描器 ===")
    print("输入包含主机列表的文件（每行一个IP/域名）")

    scanner = ModelCentricScanner()
    targets = get_targets()

    asyncio.run(scanner.run_scan(targets))

    print(f"\n扫描完成！结果保存在 [{scanner.output_dir}] 目录")
    print(f"识别到 {len(scanner.model_hosts)} 种不同模型")
    print(f"失败主机数: {len(scanner.failed_hosts)}")