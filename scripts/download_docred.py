"""
DocRED 数据下载脚本
从 Google Drive 下载 DocRED 数据集
"""

import os
import gdown
import json


def download_docred_data(output_dir: str = "data/DocRED/data"):
    """
    下载 DocRED 数据集
    
    Args:
        output_dir: 输出目录
    """
    # DocRED 数据在 Google Drive 的文件夹 ID
    # 根据 README，数据在: https://drive.google.com/drive/folders/1c5-0YwnoJx8NS6CV2f-NoTHR__BdkNqw
    folder_id = "1c5-0YwnoJx8NS6CV2f-NoTHR__BdkNqw"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("正在从 Google Drive 下载 DocRED 数据...")
    print("这可能需要一些时间，请耐心等待...")
    print(f"目标目录: {os.path.abspath(output_dir)}")
    
    try:
        # 使用 gdown 下载整个文件夹
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        print(f"下载链接: {url}")
        gdown.download_folder(url, output=output_dir, quiet=False, use_cookies=False)
        print(f"\n✓ 数据已下载到: {os.path.abspath(output_dir)}")
        
        # 检查下载的文件
        json_files = find_docred_files(output_dir)
        if json_files:
            print(f"✓ 找到 {len(json_files)} 个 JSON 文件")
        else:
            print("⚠️  未找到 JSON 文件，请检查下载是否完整")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print("\n请手动下载数据:")
        print("1. 访问: https://drive.google.com/drive/folders/1c5-0YwnoJx8NS6CV2f-NoTHR__BdkNqw")
        print(f"2. 下载数据文件到: {os.path.abspath(output_dir)}")
        print("\n或者尝试:")
        print("  - 检查网络连接")
        print("  - 确保有足够的磁盘空间")
        print("  - 尝试使用浏览器手动下载")
        raise


def find_docred_files(data_dir: str = "data/DocRED/data"):
    """
    查找 DocRED JSON 文件
    
    Returns:
        找到的文件路径列表
    """
    json_files = []
    if os.path.exists(data_dir):
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
    return json_files


if __name__ == "__main__":
    import sys
    
    # 检查是否安装 gdown
    try:
        import gdown
    except ImportError:
        print("请先安装 gdown: pip install gdown")
        sys.exit(1)
    
    # 下载数据
    try:
        download_docred_data()
        files = find_docred_files()
        print(f"\n找到 {len(files)} 个 JSON 文件:")
        for f in files[:5]:  # 只显示前5个
            print(f"  - {f}")
        if len(files) > 5:
            print(f"  ... 还有 {len(files) - 5} 个文件")
    except Exception as e:
        print(f"错误: {e}")
