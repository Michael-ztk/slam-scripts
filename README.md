# slam-scripts

SLAM 数据处理工具集。

## 脚本列表

| 脚本 | 说明 |
|------|------|
| `scripts/livox_ros2_to_ros1.py` | 将 Livox ROS2 bag (db3) 转换为 ROS1 bag，支持 CustomMsg + IMU |

## 使用方法

### livox_ros2_to_ros1.py

```bash
source /opt/ros/noetic/setup.bash
source ~/work_ws/devel/setup.bash
python3 scripts/livox_ros2_to_ros1.py <ros2_bag_dir> [output.bag]
```

依赖：`rosbags`, `rosbag`, `livox_ros_driver2`（ROS1）

### cpu/

实时 CPU 资源消耗采集与绘图：

```bash
# 1. 采集数据
top -i -o +%CPU -d 1 -w 200 -b | grep "load average" -A 35 >> cpu.log

# 2. 绘图（ARM 平台）
python3 scripts/cpu/arm_plot_cpu.py cpu.log

# 3. 绘图（x86 平台）
python3 scripts/cpu/plot_cpu.py cpu.log
```
