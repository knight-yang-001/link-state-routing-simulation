import time
import copy
from core.lsa_exchange import *
from core.dijkstra import compute_routes
from visualization.graph_viewer import draw_topology
from scripts.json_watcher import start_json_watcher

def main():
    json_path = "config/topology.json"
    topology = load_topology_from_json(json_path)

    # 启动网络
    routers = initialize_routers(topology, verbose=True)
    start_routers(routers)
    observer = start_json_watcher(json_path, routers, verbose=True)
    print("✅ 所有 Router 启动，监听器就绪")

    # 初始等待网络泛洪收敛
    time.sleep(3)
    print_all_lsdb(routers)
    print_all_adjacents(routers)

    # 自动更新可视化逻辑
    source = "A"
    prev_lsdb = {}

    try:
        while True:
            current_lsdb = routers[source].get_lsdb()

            # 深比较，只有变化时才更新
            if current_lsdb != prev_lsdb:
                print(f"\n📡 检测到 LSDB 更新，重新计算路径中...")
                routes = compute_routes(current_lsdb, source)

                print(f"\n📍 从 {source} 出发的最新路由：")
                for dst, info in routes.items():
                    print(f"{source} -> {dst}：路径 = {info['path']}, 总代价 = {info['cost']}")

                if "D" in routes:
                    draw_topology(current_lsdb, highlight_path=routes["D"]["path"],
                                  title="自动更新：从 A 到 D 的路径")

                prev_lsdb = copy.deepcopy(current_lsdb)

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 手动中断，正在关闭...")
        stop_routers(routers)
        observer.stop()
        observer.join()
        print("✅ 所有线程已安全关闭")

if __name__ == "__main__":
    main()
