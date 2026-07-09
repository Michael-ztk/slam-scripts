import rosbag
from geometry_msgs.msg import PoseWithCovarianceStamped

import rospy
import tf2_ros
import os
from geometry_msgs.msg import TransformStamped

# 输入和输出路径
input_bag = "/home/yjh/bag/test/0951/2025-09-11-10-05-59_cleanning/rosbag_2025-09-11-10-11-45_2.bag"
old_output_file = "old_trajectory_tum_wave.txt"

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

if __name__ == "__main__":
    rospy.init_node("pose_to_tum")
    
    # 参数设置（可通过ROS参数服务器动态配置）
    target_frame = rospy.get_param("~target_frame", "map")
    source_frame = rospy.get_param("~source_frame", "base_link")
    output_file = rospy.get_param("~output_file", "new_trajectory_tum_tf--initial-0.02.txt")
    
    # 创建转换器并执行转换
    #Bagconverter = BagToTumConverter(input_bag, old_output_file)
    #Bagconverter.convert()    
    
    # 启动转换器
    TFconverter = PoseToTUMConverter(target_frame, source_frame, output_file)
    
    try:
        TFconverter.run()
    except rospy.ROSInterruptException:
        pass
        

