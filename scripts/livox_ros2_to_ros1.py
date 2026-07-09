#!/usr/bin/env python3
"""Convert a ROS2 bag (db3) with livox CustomMsg + IMU to ROS1 bag.

Usage:
    source /opt/ros/noetic/setup.bash
    source ~/work_ws/devel/setup.bash
    python3 ros2bag_to_ros1bag.py <ros2_bag_dir> [output.bag]

Example:
    python3 ros2bag_to_ros1bag.py /home/yjh/bag/3d/livox/mapping/20260424/2
"""

import sys
import os
import struct

import rospy
import rosbag
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3, Quaternion
from std_msgs.msg import Header
from livox_ros_driver.msg import CustomMsg, CustomPoint

from rosbags.rosbag2 import Reader
from rosbags.serde import deserialize_cdr
from rosbags.typesys import Stores, get_typestore, get_types_from_msg


def register_livox_types(typestore):
    """Register livox custom message types with rosbags typestore."""
    point_def = (
        'uint32 offset_time\n'
        'float32 x\n'
        'float32 y\n'
        'float32 z\n'
        'uint8 reflectivity\n'
        'uint8 tag\n'
        'uint8 line\n'
    )
    msg_def = (
        'std_msgs/msg/Header header\n'
        'uint64 timebase\n'
        'uint32 point_num\n'
        'uint8 lidar_id\n'
        'uint8[3] rsvd\n'
        'livox_ros_driver2/msg/CustomPoint[] points\n'
    )
    # Must register CustomPoint first, then CustomMsg which depends on it
    typestore.register(get_types_from_msg(point_def, 'livox_ros_driver2/msg/CustomPoint'))
    typestore.register(get_types_from_msg(msg_def, 'livox_ros_driver2/msg/CustomMsg'))


def nsec_to_rospy_time(nsec):
    """Convert nanoseconds to rospy.Time."""
    sec = int(nsec // 1_000_000_000)
    nsec_rem = int(nsec % 1_000_000_000)
    return rospy.Time(sec, nsec_rem)


def convert_imu(ros2_msg):
    """Convert deserialized ROS2 Imu to ROS1 Imu."""
    msg = Imu()
    h = ros2_msg.header
    msg.header = Header()
    msg.header.seq = 0
    msg.header.stamp = nsec_to_rospy_time(h.stamp.sec * 1_000_000_000 + h.stamp.nanosec)
    msg.header.frame_id = h.frame_id

    msg.orientation = Quaternion(
        ros2_msg.orientation.x,
        ros2_msg.orientation.y,
        ros2_msg.orientation.z,
        ros2_msg.orientation.w,
    )
    msg.orientation_covariance = list(ros2_msg.orientation_covariance)

    msg.angular_velocity = Vector3(
        ros2_msg.angular_velocity.x,
        ros2_msg.angular_velocity.y,
        ros2_msg.angular_velocity.z,
    )
    msg.angular_velocity_covariance = list(ros2_msg.angular_velocity_covariance)

    msg.linear_acceleration = Vector3(
        ros2_msg.linear_acceleration.x,
        ros2_msg.linear_acceleration.y,
        ros2_msg.linear_acceleration.z,
    )
    msg.linear_acceleration_covariance = list(ros2_msg.linear_acceleration_covariance)

    return msg


def convert_custom_msg(ros2_msg):
    """Convert deserialized ROS2 livox CustomMsg to ROS1 CustomMsg."""
    msg = CustomMsg()
    h = ros2_msg.header
    msg.header = Header()
    msg.header.seq = 0
    msg.header.stamp = nsec_to_rospy_time(h.stamp.sec * 1_000_000_000 + h.stamp.nanosec)
    msg.header.frame_id = h.frame_id

    msg.timebase = ros2_msg.timebase
    msg.point_num = ros2_msg.point_num
    msg.lidar_id = ros2_msg.lidar_id
    msg.rsvd = list(ros2_msg.rsvd)

    for p in ros2_msg.points:
        pt = CustomPoint()
        pt.offset_time = p.offset_time
        pt.x = p.x
        pt.y = p.y
        pt.z = p.z
        pt.reflectivity = p.reflectivity
        pt.tag = p.tag
        pt.line = p.line
        msg.points.append(pt)

    return msg


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    ros2_bag_dir = sys.argv[1]
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = ros2_bag_dir.rstrip('/') + '_ros1.bag'

    if not os.path.isdir(ros2_bag_dir):
        print(f"Error: {ros2_bag_dir} is not a directory")
        sys.exit(1)

    # Setup rosbags typestore with livox custom types
    typestore = get_typestore(Stores.ROS2_FOXY)
    register_livox_types(typestore)

    print(f"Input:  {ros2_bag_dir}")
    print(f"Output: {output_path}")

    converters = {
        '/livox/imu': ('sensor_msgs/msg/Imu', convert_imu),
        '/livox/lidar': ('livox_ros_driver2/msg/CustomMsg', convert_custom_msg),
    }

    count = 0
    with Reader(ros2_bag_dir) as reader, rosbag.Bag(output_path, 'w') as outbag:
        for connection, timestamp, rawdata in reader.messages():
            topic = connection.topic
            if topic not in converters:
                print(f"  Skipping unknown topic: {topic}")
                continue

            msgtype_str, converter = converters[topic]
            msgtype = typestore.types[msgtype_str]

            # Deserialize ROS2 CDR
            ros2_msg = typestore.deserialize_cdr(rawdata, msgtype_str)

            # Convert to ROS1
            ros1_msg = converter(ros2_msg)

            # Timestamp for bag index
            t = nsec_to_rospy_time(timestamp)

            outbag.write(topic, ros1_msg, t)
            count += 1

            if count % 5000 == 0:
                print(f"  Converted {count} messages...")

    print(f"Done! Converted {count} messages to {output_path}")


if __name__ == '__main__':
    main()
