import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import yfinance as yf

def calculate_risk_matrix():
    """
    计算风险矩阵数据
    """
    print("🔄 开始计算Risk Matrix数据...")
    
    # 示例：获取主要市场指数数据
    symbols = {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^DJI': 'Dow Jones',
        '000001.SS': 'Shanghai Composite',
        '^HSI': 'Hang Seng'
    }
    
    risk_data = {
        "update_time": datetime.now().isoformat(),
        "markets": []
    }
    
    for symbol, name in symbols.items():
        try:
            # 获取最近30天数据
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            
            if not hist.empty:
                # 计算风险指标
                returns = hist['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)  # 年化波动率
                current_price = hist['Close'].iloc[-1]
                
                # VaR计算（简化版）
                var_95 = np.percentile(returns, 5)
                var_99 = np.percentile(returns, 1)
                
                market_data = {
                    "symbol": symbol,
                    "name": name,
                    "current_price": round(float(current_price), 2),
                    "volatility": round(volatility * 100, 2),
                    "var_95": round(var_95 * 100, 2),
                    "var_99": round(var_99 * 100, 2),
                    "risk_level": "High" if volatility > 0.25 else "Medium" if volatility > 0.15 else "Low"
                }
                
                risk_data["markets"].append(market_data)
                print(f"✅ {name}: Volatility {volatility:.2%}")
                
        except Exception as e:
            print(f"❌ 获取{name}数据失败: {str(e)}")
    
    return risk_data

def generate_sample_data():
    """
    生成示例数据用于测试
    """
    sample_data = {
        "update_time": datetime.now().isoformat(),
        "markets": [
            {
                "symbol": "^GSPC",
                "name": "S&P 500",
                "current_price": 4350.65,
                "volatility": 18.5,
                "var_95": -2.3,
                "var_99": -3.8,
                "risk_level": "Medium"
            },
            {
                "symbol": "^IXIC", 
                "name": "NASDAQ",
                "current_price": 13500.33,
                "volatility": 22.1,
                "var_95": -2.8,
                "var_99": -4.2,
                "risk_level": "Medium"
            }
        ],
        "risk_summary": {
            "overall_risk": "Medium",
            "high_risk_count": 0,
            "medium_risk_count": 2,
            "low_risk_count": 0
        }
    }
    return sample_data

if __name__ == "__main__":
    # 可以选择使用真实数据或示例数据
    try:
        data = calculate_risk_matrix()
    except:
        print("⚠️ 使用示例数据")
        data = generate_sample_data()
    
    # 保存到本地文件
    today = datetime.now().strftime("%Y-%m-%d")
    with open(f"data/risk-matrix-{today}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 同时保存为latest.json
    with open("data/risk-matrix-latest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已保存到 risk-matrix-{today}.json")
