
#!/usr/bin/env python3
import re
import pandas as pd
import matplotlib.pyplot as plt

def parse_log_file(log_path):
    """解析top命令日志文件"""
    pattern = re.compile(r'^\s*\d+\s+\S+\s+.+?\s+(\d+\.\d+)\s+.+?(\S+)$')
    processes = []
    
    with open(log_path) as f:
        for line in f:
            match = pattern.match(line)
            if match:
                cpu = float(match.group(1))
                cmd = match.group(2).split('/')[-1][:25]  # 提取命令名
                processes.append({'command': cmd, 'cpu': cpu})
    
    return pd.DataFrame(processes)

def visualize_top10(df, output_file='cpu_top10.png'):
    """生成纵向柱状图"""
    avg_cpu = df.groupby('command')['cpu'].mean().reset_index()
    top10 = avg_cpu.nlargest(10, 'cpu').sort_values('cpu', ascending=False)
    
    plt.figure(figsize=(12, 8))
    bars = plt.bar(top10['command'], top10['cpu'], color='#1f77b4')
    
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.ylabel('Average CPU Usage (%)', fontsize=12)
    plt.title('Top 10 CPU Intensive Processes (Average)', fontsize=14, pad=20)
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height,
                f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=120)
    print(f"可视化结果已保存至: {output_file}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 script.py <log_file>")
        sys.exit(1)
    
    df = parse_log_file(sys.argv[1])
    visualize_top10(df)

