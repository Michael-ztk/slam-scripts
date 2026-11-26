# slam-scripts

SLAM 数据处理工具集：bag 格式转换、evo 轨迹处理、CPU 性能分析。

## 目录结构

```
scripts/
├── bag-convert/
│   ├── convert_jazzy_to_humble.py    # Jazzy/新版 ROS2 的 mcap → Humble 可读
│   └── livox_ros2_to_ros1.py         # ROS2 db3 → ROS1 bag（Livox CustomMsg）
├── evo-trajectory/
│   ├── convert_pose.py               # bag 位姿话题 → TUM
│   ├── convert_tf_bag.py             # bag TF 链 → TUM
│   └── merge_bag.py                  # 合并多个 bag
└── cpu/
    ├── arm_plot_cpu.py               # ARM 平台 CPU 曲线
    └── plot_cpu.py                   # x86 平台 CPU 曲线
```

## bag-convert

### convert_jazzy_to_humble.py

新版 ROS2（Jazzy 及以后）录的 mcap bag，metadata 版本是 9，Humble 的 rosbag2 读不了
（报 `yaml-cpp: bad conversion`）。此脚本只改 metadata.yaml，不动 mcap 数据：

- `version` 降为 5（Humble 支持的上限）
- `offered_qos_profiles` 的结构化列表改为空字符串
- 删除 `type_description_hash` 字段
- `history: unknown` → `history: 0`

原 metadata 自动备份为 `*.yaml.bak`。

```bash
python3 scripts/bag-convert/convert_jazzy_to_humble.py <bag_dir> [bag_dir2 ...]
```

### livox_ros2_to_ros1.py

将 Livox ROS2 bag（db3）转换为 ROS1 bag，支持 CustomMsg + IMU。

```bash
source /opt/ros/noetic/setup.bash
source ~/work_ws/devel/setup.bash
python3 scripts/bag-convert/livox_ros2_to_ros1.py <ros2_bag_dir> [output.bag]
```

依赖：`rosbags`、`rosbag`、`livox_ros_driver2`（ROS1）

## evo-trajectory

三个脚本输出 TUM 格式，可直接喂给 [evo](https://github.com/MichaelGrupp/evo) 评估：

```bash
evo_traj tum out.tum -p --plot_mode=xy
```

### convert_pose.py

两种模式：

```bash
# 离线：从 bag 提取位姿话题
python3 scripts/evo-trajectory/convert_pose.py bag \
    -i input.bag -o out.tum -t /pose_with_cov

# 在线：实时订阅 TF 链
python3 scripts/evo-trajectory/convert_pose.py tf \
    -o out.tum --target map --source base_link
```

### convert_tf_bag.py

从 bag 里的 TF 链（默认 map→odom→base_link）合成轨迹：

```bash
python3 scripts/evo-trajectory/convert_tf_bag.py \
    -i input.bag -o out.tum --target map --intermediate odom --source base_link
```

### merge_bag.py

```bash
python3 scripts/evo-trajectory/merge_bag.py -o merged.bag -i a.bag b.bag c.bag
# 只合并指定话题
python3 scripts/evo-trajectory/merge_bag.py -o merged.bag -i *.bag -t /livox/lidar,/livox/imu
```

## cpu

实时 CPU 资源消耗采集与绘图。

```bash
# 1. 采集（每 1 秒一行，只显示活跃进程）
top -i -o +%CPU -d 1 -w 200 -b | grep "load average" -A 35 >> cpu.log

# 2. 绘图
python3 scripts/cpu/arm_plot_cpu.py cpu.log    # ARM 平台
python3 scripts/cpu/plot_cpu.py cpu.log        # x86 平台
```

ARM 和 x86 分开是因为 `top` 输出格式（列宽、字段顺序）不同。

## 依赖

```bash
pip install rosbags pandas matplotlib numpy
```

ROS 相关脚本（`convert_pose.py` 的 tf 模式、`convert_tf_bag.py`）需要 rospy 环境。
