"""为 Workbenchmark 任务合成每块积木的【初始(取料)位置】。

benchmark 只保留了成品 yaml(blocks 的最终 pos/rotation),不含初始坐标。
本脚本据成品清单生成初始摆放,满足:
  - 全部【摆正】(rotation = [0,0,0],长边沿 +X);
  - 落在机械臂正前方的取料区域 REGION 内(可达);
  - 随机散布,但任意两块【边到边】最近距离 >= 2 studs(注意:不是中心距);
  - 用任务名做确定性随机种子 -> 同一任务每次结果一致(可复现)。

用法:
  python generate_initial_positions.py benchmark_tasks/tier3_task_003.yaml          # 打印
  python generate_initial_positions.py benchmark_tasks/tier3_task_003.yaml -o out.yaml
  python generate_initial_positions.py --all [--outdir benchmark_tasks_with_initial]

输出在原 yaml 基础上新增:
  initial_blocks:
  - {name, type, color, pos: [x, y, z], rotation: [0,0,0]}
"""
import os, sys, glob, random, hashlib, argparse, yaml

STUD = 0.016
GAP_MIN = 2 * STUD                  # 硬约束:边到边最近距离 >= 2 studs
JIT = 0.012                         # 每块随机抖动幅度(±12mm)
X0, Y0, COLS = 0.26, -0.12, 4       # 抖动网格锚点/列数(桌面右侧 -Y, 紧凑可达)
INIT_Z = 0.0495                     # 初始积木在桌面上的中心高度

def half_extent(btype):
    """摆正(长边沿X)时的半尺寸 (hx, hy)。4x2=64x32mm, 2x2=32x32mm。"""
    return (0.032, 0.016) if btype == "brick_4x2" else (0.016, 0.016)

def edge_gap(a, b):
    """两块轴对齐矩形 (x,y,hx,hy) 的边到边最近距离(重叠则 0)。"""
    ax, ay, ahx, ahy = a; bx, by, bhx, bhy = b
    gx = max(0.0, abs(ax - bx) - (ahx + bhx))
    gy = max(0.0, abs(ay - by) - (ahy + bhy))
    return (gx * gx + gy * gy) ** 0.5

def synth_initial(blocks, seed):
    """抖动网格:网格点 + 随机抖动 + 打乱分配。pitch 留足抖动余量,
    保证任意两块边到边 >= 2 studs(最坏:两块4x2相邻正好=2 studs)。返回 [(x,y), ...]。"""
    rng = random.Random(seed)
    pitch_x = 2 * 0.032 + GAP_MIN + 2 * JIT   # 0.12
    pitch_y = 2 * 0.016 + GAP_MIN + 2 * JIT   # 0.088
    cells = [(X0 + (i % COLS) * pitch_x, Y0 - (i // COLS) * pitch_y)
             for i in range(len(blocks))]
    rng.shuffle(cells)
    return [(cx + rng.uniform(-JIT, JIT), cy + rng.uniform(-JIT, JIT)) for cx, cy in cells]

def min_edge_gap(blocks, picks):
    R = [(x, y, *half_extent(b["type"])) for b, (x, y) in zip(blocks, picks)]
    m = float("inf")
    for i in range(len(R)):
        for j in range(i + 1, len(R)):
            m = min(m, edge_gap(R[i], R[j]))
    return m

def process(path):
    """读取一个任务 yaml,返回 (data_with_initial, min_gap)。"""
    data = yaml.safe_load(open(path))
    blocks = data["blocks"]
    # 与装配顺序一致(自底向上),保证随机序列可复现
    order = sorted(blocks, key=lambda b: (round(b["pos"][2], 4), b["name"]))
    seed = int(hashlib.md5(os.path.basename(path).encode()).hexdigest()[:8], 16)
    picks = synth_initial(order, seed)
    g = min_edge_gap(order, picks)
    assert g >= GAP_MIN - 1e-9, f"间距约束被破坏: {g:.4f} < {GAP_MIN}"
    data["initial_blocks"] = [
        {"name": b["name"], "type": b["type"], "color": b.get("color"),
         "pos": [round(x, 4), round(y, 4), round(INIT_Z, 4)], "rotation": [0, 0, 0]}
        for b, (x, y) in zip(order, picks)
    ]
    return data, g

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", help="单个任务 yaml")
    ap.add_argument("-o", "--out", help="输出 yaml 路径")
    ap.add_argument("--all", action="store_true", help="处理 benchmark_tasks 下全部")
    ap.add_argument("--outdir", default="benchmark_tasks_with_initial")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    if a.all:
        os.makedirs(a.outdir, exist_ok=True)
        files = sorted(glob.glob(os.path.join(here, "benchmark_tasks", "*.yaml")))
        worst = 0.0
        for f in files:
            data, g = process(f)
            yaml.safe_dump(data, open(os.path.join(a.outdir, os.path.basename(f)), "w"),
                           sort_keys=False, allow_unicode=True)
            worst = max(worst, GAP_MIN - g)
        print(f"处理 {len(files)} 个任务 -> {a.outdir} (全部满足边到边>=2studs)")
    elif a.task:
        data, g = process(a.task)
        out = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        if a.out:
            open(a.out, "w").write(out); print(f"写入 {a.out}")
        else:
            print(out)
        print(f"# 边到边最小间距 = {g*1000:.1f}mm ({g/STUD:.2f} studs)", file=sys.stderr)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
