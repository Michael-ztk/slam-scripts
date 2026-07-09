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

依赖：`rosbags`, `rosbag`, `livox_ros_driver`（ROS1）
