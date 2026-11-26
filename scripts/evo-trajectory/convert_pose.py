#!/usr/bin/env python3
"""将 ROS bag 中的位姿话题或 TF 轨迹导出为 TUM 格式

两种模式：
  bag  从 bag 文件里提取 PoseWithCovarianceStamped 话题（离线）
  tf   实时订阅 TF 链并输出（在线，需 rospy 运行）

用法：
  python3 convert_pose.py bag -i input.bag -o out.tum -t /pose_with_cov
  python3 convert_pose.py tf -o out.tum --target map --source base_link
"""

import argparse
import os
import sys

import rosbag
import rospy
import tf2_ros
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped

class BagToTumConverter:
    def __init__(self, input_bag, output_file, topic_name="/pose_with_cov"):
        """
        ROS Bag转换TUM格式轨迹文件的工具类
        
        :param input_bag: 输入的ROS Bag文件路径
        :param output_file: 输出的TUM格式文件路径
        :param topic_name: 要提取的位姿话题名，默认为'/pose_with_cov'
        """
        self.input_bag = input_bag
        self.output_file = output_file
        self.topic_name = topic_name
        
        # 验证文件路径
        if not os.path.exists(input_bag):
            raise FileNotFoundError(f"Input bag file not found: {input_bag}")
        
    def convert(self):
        """
        执行转换操作
        """
        try:
            with open(self.output_file, "w") as tum_file, \
                 rosbag.Bag(self.input_bag, "r") as bag:
                
                # 写入TUM格式文件头
                tum_file.write("# TUM trajectory format\n")
                tum_file.write("# timestamp tx ty tz qx qy qz qw\n")
                
                for topic, msg, t in bag.read_messages(topics=[self.topic_name]):
                    # 获取时间戳 (ROS Time对象转换为浮点秒数)
                    timestamp = msg.header.stamp.to_sec()
                    
                    # 提取位置和姿态四元数
                    pose = msg.pose.pose
                    x = pose.position.x
                    y = pose.position.y
                    z = pose.position.z
                    qx = pose.orientation.x
                    qy = pose.orientation.y
                    qz = pose.orientation.z
                    qw = pose.orientation.w
                    
                    # 写入TUM格式行 (保留6位小数精度)
                    tum_file.write(f"{timestamp:.6f} {x:.6f} {y:.6f} {z:.6f} "
                                  f"{qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n")
            
            print(f"成功转换 {bag.get_message_count(self.topic_name)} 条消息到 {self.output_file}")
            return True
            
        except Exception as e:
            rospy.logerr(f"转换过程中出错: {str(e)}")
            return False
                

class PoseToTUMConverter:
    def __init__(self, target_frame, source_frame, output_file):
        self.target_frame = target_frame  # 目标坐标系（如 "map"）
        self.source_frame = source_frame  # 源坐标系（如 "base_link"）
        self.output_file = output_file    # 输出TUM文件路径
        
        # 初始化TF监听器
        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(10))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        
        # 打开输出文件（追加模式）
        self.file = open(output_file, 'w')

    def run(self):
        rate = rospy.Rate(10)  # 查询频率（Hz）
        while not rospy.is_shutdown():
            try:
                # 查询最新坐标变换（非阻塞模式）
                trans = self.tf_buffer.lookup_transform(
                    self.target_frame,
                    self.source_frame,
                    rospy.Time(0),  # 获取最新可用时间
                    timeout=rospy.Duration(0.1))
                
                # 提取数据
                timestamp = trans.header.stamp.to_sec()
                x = trans.transform.translation.x
                y = trans.transform.translation.y
                z = trans.transform.translation.z
                qx = trans.transform.rotation.x
                qy = trans.transform.rotation.y
                qz = trans.transform.rotation.z
                qw = trans.transform.rotation.w
                
                # 写入文件
                self.file.write(f"{timestamp:.6f} {x} {y} {z} {qx} {qy} {qz} {qw}\n")
                self.file.flush()  # 确保实时写入磁盘

            except (tf2_ros.LookupException,
                    tf2_ros.ConnectivityException,
                    tf2_ros.ExtrapolationException) as e:
                rospy.logwarn(f"TF查询失败: {e}")
                continue
            
            rate.sleep()

    def __del__(self):
        self.file.close()

def main():
    parser = argparse.ArgumentParser(description="位姿/TF 轨迹转 TUM 格式")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_bag = sub.add_parser("bag", help="从 bag 文件提取位姿话题")
    p_bag.add_argument("-i", "--input", required=True, help="输入 rosbag 路径")
    p_bag.add_argument("-o", "--output", required=True, help="输出 TUM 文件")
    p_bag.add_argument("-t", "--topic", default="/pose_with_cov", help="位姿话题名")

    p_tf = sub.add_parser("tf", help="实时订阅 TF 链导出轨迹")
    p_tf.add_argument("-o", "--output", required=True, help="输出 TUM 文件")
    p_tf.add_argument("--target", default="map", help="目标坐标系")
    p_tf.add_argument("--source", default="base_link", help="源坐标系")

    args = parser.parse_args()

    if args.mode == "bag":
        conv = BagToTumConverter(args.input, args.output, args.topic)
        conv.convert()
    else:
        rospy.init_node("pose_to_tum")
        conv = PoseToTUMConverter(args.target, args.source, args.output)
        try:
            conv.run()
        except rospy.ROSInterruptException:
            pass


if __name__ == "__main__":
    main()
        

