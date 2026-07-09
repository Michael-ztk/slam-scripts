
#!/usr/bin/env python3
import re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def parse_log(log_path, cpu_threshold=1.0):
    """解析TOP日志并标记低负载进程"""
    records = []
    current_ts = None
    
    with open(log_path) as f:
        for line in f:
            if line.startswith('top - '):
                time_str = re.search(r'\d{2}:\d{2}:\d{2}', line).group()
                current_ts = pd.to_datetime(time_str)
                continue
                
            if line[0].isdigit():
                parts = re.split(r'\s+', line.strip(), maxsplit=11)
                if len(parts) < 12:
                    continue
                
                try:
                    records.append({
                        'command': parts[11].split('/')[-1][:25],
                        'cpu': float(parts[8]),
                        'is_idle': float(parts[8]) < cpu_threshold,
                        'timestamp': current_ts
                    })
                except (ValueError, IndexError) as e:
                    print(f"解析异常：{line.strip()} | 错误：{str(e)}")
                    continue
    
    return pd.DataFrame(records)

def analyze_activity(df):
    """分析活跃进程数据"""
    if df.empty:
        return pd.DataFrame()
    
    active_df = df[~df['is_idle']]
    stats = active_df.groupby('command')['cpu'].agg(
        avg_cpu='mean',
        max_cpu='max',
        min_cpu='min',
        samples='count'
    )
    return stats.nlargest(10, 'avg_cpu')

def visualize_analysis(stats, output='cpu_analysis.png'):
    """可视化分析结果"""
    if stats.empty:
        print("无有效数据可供可视化")
        return

    plt.figure(figsize=(14, 8))
    ax = plt.gca()
    
    bars = ax.bar(
        stats.index, stats['avg_cpu'], 
        yerr=[stats['avg_cpu']-stats['min_cpu'], stats['max_cpu']-stats['avg_cpu']],
        color='steelblue',
        capsize=5,
        error_kw={'elinewidth': 1, 'ecolor': 'darkred'}
    )
    
    # 新增均值标注
    for idx, (proc, data) in enumerate(stats.iterrows()):
        # 均值标注
        ax.text(
            idx, data['avg_cpu']/2, 
            f"{data['avg_cpu']:.1f}%", 
            ha='center', 
            va='center',
            color='white',
            fontsize=9,
            weight='bold'
        )
        
        # 最大值标注
        ax.annotate(
            f"{data['max_cpu']:.1f}%", 
            xy=(idx, data['max_cpu']), 
            xytext=(0, 3), 
            textcoords='offset points',
            ha='center', 
            va='bottom',
            color='crimson',
            fontsize=9
        )
        
        # 最小值标注
        ax.annotate(
            f"{data['min_cpu']:.1f}%", 
            xy=(idx, data['min_cpu']), 
            xytext=(0, -3), 
            textcoords='offset points',
            ha='center', 
            va='top',
            color='crimson',
            fontsize=9
        )
    
    ax.set_ylabel('CPU Utilization (%)', fontsize=12)
    ax.set_xlabel('Process Name', fontsize=12)
    ax.set_title(
        f'Top {len(stats)} Processes by CPU Usage\n'
        f'(Excluding processes < {args.threshold}% CPU)', 
        pad=20, 
        fontsize=14
    )
    
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches='tight')
    print(f"分析报告已生成：{output}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='进程级CPU使用分析工具',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('logfile', help='TOP日志文件路径')
    parser.add_argument('-t', '--threshold', type=float, default=5.0,
                       help='CPU阈值（%%），低于此值视为空闲进程')
    parser.add_argument('-o', '--output', default='cpu_report.png',
                       help='输出图片文件名')
    
    args = parser.parse_args()
    
    df = parse_log(args.logfile, args.threshold)
    if df.empty:
        print("错误：未解析到有效日志数据")
        exit(1)
        
    stats = analyze_activity(df)
    if not stats.empty:
        visualize_analysis(stats, args.output)
    else:
        print("提示：未发现超过阈值的活跃进程")

