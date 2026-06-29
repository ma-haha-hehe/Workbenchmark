"""校验 Workbenchmark 每个任务的成品结构:
  - 禁止重叠:任意两块的 3D 包围盒不得有正体积相交(同层错位/堆叠相接都允许)。
  - 禁止悬空:除贴底板的块外,每块下方必须有块支撑(底面与下块顶面相接且足印重叠)。
用法: python validate_tasks.py            # 校验 benchmark_tasks 全部, 打印违规
      python validate_tasks.py <file>     # 单个
"""
import os, sys, glob, yaml

H = 0.0191          # 积木高度(层间距)
PLATE_TOP = 0.0     # 成品坐标里 z=0 即贴底板层
EPS = 1e-4

def footprint_half(b):
    """足印半尺寸 (hx, hy),按 type 与 rotation_z(0/90)。"""
    rz = int(b["rotation"][2]) % 180
    if b["type"] == "brick_4x2":
        return (0.016, 0.032) if rz == 90 else (0.032, 0.016)
    return (0.016, 0.016)

def aabb(b):
    x, y, z = b["pos"]; hx, hy = footprint_half(b)
    return (x - hx, x + hx, y - hy, y + hy, z, z + H)

def overlap_volume(a, b):
    ox = min(a[1], b[1]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[2], b[2])
    oz = min(a[5], b[5]) - max(a[4], b[4])
    return ox, oy, oz

def check(path):
    blocks = yaml.safe_load(open(path))["blocks"]
    boxes = [aabb(b) for b in blocks]
    overlaps, floats = [], []
    # 重叠
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            ox, oy, oz = overlap_volume(boxes[i], boxes[j])
            if ox > EPS and oy > EPS and oz > EPS:
                overlaps.append((blocks[i]["name"], blocks[j]["name"],
                                 round(min(ox, oy, oz), 4)))
    # 悬空
    for i, b in enumerate(blocks):
        zb = b["pos"][2]
        if zb <= PLATE_TOP + EPS:
            continue                      # 贴底板
        supported = False
        for j, o in enumerate(blocks):
            if i == j: continue
            zt = o["pos"][2] + H
            if abs(zt - zb) < EPS:          # 下块顶面=本块底面
                ox = min(boxes[i][1], boxes[j][1]) - max(boxes[i][0], boxes[j][0])
                oy = min(boxes[i][3], boxes[j][3]) - max(boxes[i][2], boxes[j][2])
                if ox > EPS and oy > EPS:
                    supported = True; break
        if not supported:
            floats.append(b["name"])
    return overlaps, floats

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        files = [sys.argv[1]]
    else:
        files = sorted(glob.glob(os.path.join(here, "benchmark_tasks", "*.yaml")))
    bad_overlap, bad_float = [], []
    for f in files:
        ov, fl = check(f)
        name = os.path.basename(f)[:-5]
        if ov: bad_overlap.append((name, ov))
        if fl: bad_float.append((name, fl))
    print(f"校验 {len(files)} 个任务")
    print(f"  重叠违规: {len(bad_overlap)} 个")
    for n, ov in bad_overlap[:20]:
        print(f"    {n}: {ov[:3]}")
    print(f"  悬空违规: {len(bad_float)} 个")
    for n, fl in bad_float[:20]:
        print(f"    {n}: {fl}")

if __name__ == "__main__":
    main()
