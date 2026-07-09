import rosbag
import rospy
import os
import sys
import tf.transformations as tft
import numpy as np

# 输入和输出路径
input_bag = "/home/yjh/bag/test/0951/2025-09-11-10-05-59_cleanning/rosbag_2025-09-11-10-11-45_2.bag"
output_file = "old_trajectory_tum_tf.txt"

class BagTfToTumConverter:
    def __init__(self, input_bag, output_file, target_frame="map", intermediate_frame="odom", source_frame="base_link"):
        self.input_bag = input_bag
        self.output_file = output_file
        self.target_frame = target_frame
        self.intermediate_frame = intermediate_frame
        self.source_frame = source_frame
        
        # 存储最新的 map -> odom 变换矩阵
        self.map_odom_matrix = None
        
        if not os.path.exists(input_bag):
            raise FileNotFoundError(f"Input bag file not found: {input_bag}")

    def _to_matrix(self, translation, rotation):
        """将位移和四元数转换为4x4变换矩阵"""
        trans_mat = tft.translation_matrix([translation.x, translation.y, translation.z])
        rot_mat = tft.quaternion_matrix([rotation.x, rotation.y, rotation.z, rotation.w])
        return np.dot(trans_mat, rot_mat)

    def convert(self):
        count = 0
        written_count = 0
        
        print(f"开始处理 bag 文件: {self.input_bag}")
        
        try:
            with open(self.output_file, "w") as tum_file, \
                 rosbag.Bag(self.input_bag, "r") as bag:
                
                tum_file.write("# TUM trajectory format\n")
                tum_file.write(f"# timestamp tx ty tz qx qy qz qw | {self.target_frame} -> {self.source_frame}\n")
                
                for topic, msg, t in bag.read_messages(topics=['/tf', '/tf_static']):
                    if hasattr(msg, 'transforms'):
                        for transform in msg.transforms:
                            parent = transform.header.frame_id
                            child = transform.child_frame_id
                            
                            # 更新 map -> odom
                            if parent == self.target_frame and child == self.intermediate_frame:
                                self.map_odom_matrix = self._to_matrix(
                                    transform.transform.translation,
                                    transform.transform.rotation
                                )
                            
                            # 处理 odom -> base_link
                            elif parent == self.intermediate_frame and child == self.source_frame:
                                if self.map_odom_matrix is not None:
                                    # 计算 odom -> base_link 矩阵
                                    odom_base_matrix = self._to_matrix(
                                        transform.transform.translation,
                                        transform.transform.rotation
                                    )
                                    
                                    # 级联: map->base = (map->odom) * (odom->base)
                                    map_base_matrix = np.dot(self.map_odom_matrix, odom_base_matrix)
                                    
                                    # 提取位移
                                    trans = tft.translation_from_matrix(map_base_matrix)
                                    tx, ty, tz = trans[0], trans[1], trans[2]
                                    
                                    # 提取四元数
                                    rot = tft.quaternion_from_matrix(map_base_matrix)
                                    qx, qy, qz, qw = rot[0], rot[1], rot[2], rot[3]
                                    
                                    timestamp = transform.header.stamp.to_sec()
                                    
                                    tum_file.write(f"{timestamp:.6f} {tx:.6f} {ty:.6f} {tz:.6f} "
                                                  f"{qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n")
                                    written_count += 1
                    
                    count += 1
                    if count % 10000 == 0:
                        print(f"处理进度: {count} 消息...")
            
            print(f"处理完成。共 {count} 消息，生成 {written_count} 个位姿。")
            return True
            
        except Exception as e:
            print(f"出错: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_bag = sys.argv[1]
        output_file = sys.argv[2]
        
    converter = BagTfToTumConverter(input_bag, output_file)
    converter.convert()
