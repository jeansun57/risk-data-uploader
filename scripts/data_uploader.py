import os
import json
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from datetime import datetime

def upload_to_cos():
    """
    上传数据文件到腾讯云COS
    """
    # 从环境变量获取配置
    secret_id = os.environ.get('TENCENT_SECRET_ID')
    secret_key = os.environ.get('TENCENT_SECRET_KEY')
    region = os.environ.get('COS_REGION', 'ap-beijing')
    bucket = os.environ.get('COS_BUCKET_NAME')
    
    if not all([secret_id, secret_key, bucket]):
        raise ValueError("缺少必要的环境变量配置")
    
    # 配置COS客户端
    config = CosConfig(
        Region=region,
        SecretId=secret_id,
        SecretKey=secret_key
    )
    client = CosS3Client(config)
    
    # 上传文件列表
    today = datetime.now().strftime("%Y-%m-%d")
    files_to_upload = [
        {
            'local': f"data/risk-matrix-{today}.json",
            'remote': f"data/risk-matrix/{today}.json"
        },
        {
            'local': "data/risk-matrix-latest.json", 
            'remote': "data/risk-matrix/latest.json"
        }
    ]
    
    for file_info in files_to_upload:
        local_path = file_info['local']
        remote_path = file_info['remote']
        
        if os.path.exists(local_path):
            try:
                response = client.upload_file(
                    Bucket=bucket,
                    LocalFilePath=local_path,
                    Key=remote_path,
                    PartSize=1,
                    MAXThread=10
                )
                print(f"✅ 上传成功: {remote_path}")
                
                # 设置公共读权限
                client.put_object_acl(
                    Bucket=bucket,
                    Key=remote_path,
                    ACL='public-read'
                )
                
            except Exception as e:
                print(f"❌ 上传失败 {remote_path}: {str(e)}")
        else:
            print(f"⚠️ 文件不存在: {local_path}")
    
    # 输出访问URL
    base_url = f"https://{bucket}.cos.{region}.myqcloud.com"
    print(f"\n📍 数据访问地址:")
    print(f"最新数据: {base_url}/data/risk-matrix/latest.json")
    print(f"今日数据: {base_url}/data/risk-matrix/{today}.json")

if __name__ == "__main__":
    upload_to_cos()
