
#!/usr/bin/env python
import rosbag
import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(description='合并多个ROS bag文件')
    parser.add_argument('-o', '--output', required=True, help='输出bag文件路径')
    parser.add_argument('-i', '--input', nargs='+', required=True, 
                       help='输入bag文件列表（支持通配符）')
    parser.add_argument('-t', '--topics', default=None,
                       help='指定合并的话题（逗号分隔）')
    return parser.parse_args()

def merge_bags():
    args = parse_args()
    try:
        with rosbag.Bag(args.output, 'w') as outbag:
            for bag_file in args.input:
                with rosbag.Bag(bag_file) as inbag:
                    topics = args.topics.split(',') if args.topics else None
                    for topic, msg, t in inbag.read_messages(topics=topics):
                        outbag.write(topic, msg, t)
        print(f"成功合并到 {args.output}")
    except Exception as e:
        print(f"合并失败: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    merge_bags()

