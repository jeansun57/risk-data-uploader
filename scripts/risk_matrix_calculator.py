import pandas as pd
import numpy as np
import yfinance as yf
import fredapi
import time
from datetime import datetime, timedelta
import warnings
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
warnings.filterwarnings('ignore')




# 完整的数据指标字典
DATA_CATEGORIES = {
    "全球风险情绪": {
        "description": "全球市场风险情绪相关指标",
        "indicators": {
            # FRED数据
            "RRPONTSYD": {"name": "美联储逆回购余额", "source": "fred", "freq": "daily"},
            "WALCL": {"name": "美联储资产负债表", "source": "fred", "freq": "weekly"},
            "WTREGEN": {"name": "美联储国债持有", "source": "fred", "freq": "weekly"},
            "VIXCLS": {"name": "VIX波动率指数", "source": "fred", "freq": "daily"},
            # Yahoo Finance数据
            
            "^MOVE": {"name": "MOVE美债波动率", "source": "yahoo", "freq": "daily"},
            "^SKEW": {"name": "SKEW偏度指数", "source": "yahoo", "freq": "daily"},
            "DX-Y.NYB": {"name": "美元指数DXY", "source": "yahoo", "freq": "daily"},
            "VWO": {"name": "新兴市场ETF", "source": "yahoo", "freq": "daily"},
            "URTH": {"name": "发达市场ETF", "source": "yahoo", "freq": "daily"}
        }
    },
    
    "信用与流动性": {
        "description": "信用市场和流动性指标",
        "indicators": {
            # FRED数据
            "DGS10": {"name": "美国10年期国债", "source": "fred", "freq": "daily"},
            "DGS2": {"name": "美国2年期国债", "source": "fred", "freq": "daily"},
            "T10Y2Y": {"name": "10Y-2Y利差", "source": "fred", "freq": "daily"},
            "IRLTLT01JPM156N": {"name": "日本10年期国债", "source": "fred", "freq": "monthly"},
            "IRLTLT01DEM156N": {"name": "德国10年期国债", "source": "fred", "freq": "monthly"},
            "BAMLH0A0HYM2": {"name": "高收益债利差", "source": "fred", "freq": "daily"},
            "BAMLC0A0CM": {"name": "投资级债利差", "source": "fred", "freq": "daily"},
            "SOFR": {"name": "SOFR利率", "source": "fred", "freq": "daily"},
            "EFFR": {"name": "联邦基金利率", "source": "fred", "freq": "daily"},
            "IORB": {"name": "隔夜逆回购利率", "source": "fred", "freq": "daily"},
            "NFCI": {"name": "国家金融状况指数", "source": "fred", "freq": "weekly"},
            # Yahoo Finance数据
            "HYG": {"name": "高收益债ETF", "source": "yahoo", "freq": "daily"},
            "JNK": {"name": "垃圾债ETF", "source": "yahoo", "freq": "daily"}
        }
    },
    
    "汇率风险": {
        "description": "主要货币和数字货币汇率",
        "indicators": {
            "JPY=X": {"name": "日元/USD", "source": "yahoo", "freq": "daily"},
            "EUR=X": {"name": "欧元/USD", "source": "yahoo", "freq": "daily"},
            "CNY=X": {"name": "人民币/USD", "source": "yahoo", "freq": "daily"},
            "GBP=X": {"name": "英镑/USD", "source": "yahoo", "freq": "daily"},
            "BTC-USD": {"name": "比特币/USD", "source": "yahoo", "freq": "daily"},
            "ETH-USD": {"name": "以太坊/USD", "source": "yahoo", "freq": "daily"},
            "SOL-USD": {"name": "Solana/USD", "source": "yahoo", "freq": "daily"}
        }
    },
    
    "大宗商品": {
        "description": "大宗商品价格指标",
        "indicators": {
            "CL=F": {"name": "WTI原油期货", "source": "yahoo", "freq": "daily"},
            "BZ=F": {"name": "布伦特原油期货", "source": "yahoo", "freq": "daily"},
            "NG=F": {"name": "天然气期货", "source": "yahoo", "freq": "daily"},
            "GC=F": {"name": "黄金期货", "source": "yahoo", "freq": "daily"},
            "HG=F": {"name": "铜期货", "source": "yahoo", "freq": "daily"},
            "ZS=F": {"name": "大豆期货", "source": "yahoo", "freq": "daily"},
            "ZC=F": {"name": "玉米期货", "source": "yahoo", "freq": "daily"},
            "ZW=F": {"name": "小麦期货", "source": "yahoo", "freq": "daily"},
            "DBC": {"name": "大宗商品指数ETF", "source": "yahoo", "freq": "daily"}
        }
    },
    
    "经济政策不确定性": {
        "description": "经济政策不确定性相关指标",
        "indicators": {
            "WLEMUINDXD": {"name": "世界经济政策不确定性指数", "source": "fred", "freq": "daily"},
            "USEPUINDXD": {"name": "美国经济政策不确定性指数", "source": "fred", "freq": "daily"},
            "MTSDS133FMS" :{"name": "美国月度财政余额", "source": "fred", "freq": "daily"},
            "UMCSENT": {"name": "密歇根消费者信心指数", "source": "fred", "freq": "monthly"},
            "T5YIE":   {"name": "5年期通胀预期", "source": "fred", "freq": "daily"}
    
            
        }
    },
    
    "宏观经济数据": {
        "description": "主要宏观经济指标",
        "indicators": {
            # 美国数据
            "CPILFESL": {"name": "核心美国CPI", "source": "fred", "freq": "monthly"},
            "UNRATE": {"name": "美国失业率", "source": "fred", "freq": "monthly"},
            "CIVPART": {"name": "劳动参与率", "source": "fred", "freq": "monthly"},
            "PAYEMS": {"name": "非农就业", "source": "fred", "freq": "monthly"},
            "GDP": {"name": "GDP", "source": "fred", "freq": "quarterly"},
            "MORTGAGE30US": {"name": "30年抵押贷款利率", "source": "fred", "freq": "weekly"},
            "BOPGSTB": {"name": "美国贸易差额", "source": "fred", "freq": "monthly"},
            "DTP10J28": {"name": "10年期TIPS", "source": "fred", "freq": "daily"},
            # 中国数据
            "EXPCH": {"name": "中国出口", "source": "fred", "freq": "monthly"},
            "IMPCH": {"name": "中国进口", "source": "fred", "freq": "monthly"}
        }
    }
}


# 数据管理基类 - 增强版
class DataManager:
    def __init__(self, fred_api_key, alpha_vantage_key=None):
        self.fred_api_key = fred_api_key
        self.alpha_key = alpha_vantage_key
        self.last_request_time = {}
        
        # 初始化FRED API
        self.fred_available = False
        if fred_api_key:
            try:
                self.fred = fredapi.Fred(api_key=fred_api_key)
                # 测试API key是否有效
                test = self.fred.get_series('GDP', limit=1)
                self.fred_available = True
                print(f"✅ FRED API连接成功 (Key: {fred_api_key[:8]}...{fred_api_key[-4:]})")
            except Exception as e:
                self.fred_available = False
                print(f"❌ FRED API连接失败: {str(e)}")
                if "api_key" in str(e).lower():
                    print("   请检查API Key是否正确")
                if "registered" in str(e).lower():
                    print("   请确保API Key已激活")
        else:
            print("⚠️  未提供FRED API Key，将跳过FRED数据")
    def create_yahoo_session(self):
        """创建带代理的Yahoo Finance会话"""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        
        # 检查是否需要使用代理
        if os.environ.get('USE_PROXY') == 'true':
            proxy_host = os.environ.get('PROXY_HOST', '127.0.0.1')
            proxy_port = os.environ.get('PROXY_PORT', '1080')
            
            proxies = {
                'http': f'socks5://{proxy_host}:{proxy_port}',
                'https': f'socks5://{proxy_host}:{proxy_port}'
            }
            session.proxies = proxies
            print(f"🌐 Yahoo Finance使用代理: {proxy_host}:{proxy_port}")
        else:
            print("🌐 Yahoo Finance使用直连")
        
        # 设置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        return session
        
    def rate_limit(self, source, min_interval=0.5):
        """增强的频次控制"""
        intervals = {
            'fred': 0.6,
            'yahoo': 0.2,
            'alpha_vantage': 12.0
        }
        
        interval = intervals.get(source, min_interval)
        now = time.time()
        
        if source in self.last_request_time:
            elapsed = now - self.last_request_time[source]
            if elapsed < interval:
                time.sleep(interval - elapsed)
        
        self.last_request_time[source] = time.time()

# 主数据下载类 - 完善版
class GlobalMacroDataLoader(DataManager):
    def __init__(self, fred_api_key=None, alpha_vantage_key=None):
        super().__init__(fred_api_key, alpha_vantage_key)
        self.data_cache = {}
        self.config_file = "data_config.json"
        self.load_or_create_config()
        
    def load_or_create_config(self):
        """加载或创建配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                # 合并保存的配置和默认配置
                for category, info in saved_config.items():
                    if category in DATA_CATEGORIES:
                        DATA_CATEGORIES[category]['indicators'].update(info.get('indicators', {}))
                    else:
                        DATA_CATEGORIES[category] = info
                print(f"✅ 已加载配置文件: {self.config_file}")
            except Exception as e:
                print(f"⚠️  配置文件加载失败: {e}")
        
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(DATA_CATEGORIES, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  配置保存失败: {e}")
    
    def add_category(self, category_name, description=""):
        """添加新分类"""
        if category_name not in DATA_CATEGORIES:
            DATA_CATEGORIES[category_name] = {
                "description": description,
                "indicators": {}
            }
            self.save_config()
            print(f"✅ 已添加分类: {category_name}")
        else:
            print(f"⚠️  分类 {category_name} 已存在")
    
    def add_indicator(self, category, symbol, name, source, freq="daily", price_type="Close"):
        """添加新指标到指定分类"""
        if category not in DATA_CATEGORIES:
            self.add_category(category)
        
        DATA_CATEGORIES[category]["indicators"][symbol] = {
            "name": name,
            "source": source.lower(),
            "freq": freq,
            "price_type": price_type
        }
        self.save_config()
        print(f"✅ 已添加指标: {name} ({symbol}) 到分类 {category}")
    
    def remove_indicator(self, category, symbol):
        """从分类中删除指标"""
        if (category in DATA_CATEGORIES and 
            symbol in DATA_CATEGORIES[category]["indicators"]):
            del DATA_CATEGORIES[category]["indicators"][symbol]
            self.save_config()
            print(f"✅ 已删除指标: {symbol}")
        else:
            print(f"⚠️  指标 {symbol} 不存在于分类 {category}")
    
    def list_categories(self):
        """列出所有分类"""
        print("\n📁 可用分类:")
        for category, info in DATA_CATEGORIES.items():
            indicator_count = len(info.get("indicators", {}))
            description = info.get("description", "")
            print(f"   {category}: {indicator_count} 个指标 - {description}")
    
    def list_indicators(self, category=None):
        """列出指标"""
        if category and category in DATA_CATEGORIES:
            categories = {category: DATA_CATEGORIES[category]}
        else:
            categories = DATA_CATEGORIES
        
        for cat_name, cat_info in categories.items():
            print(f"\n📊 {cat_name}:")
            for symbol, info in cat_info.get("indicators", {}).items():
                print(f"   {symbol:15} - {info['name']} ({info['source']})")
    
    def normalize_series_timezone(self, series, symbol):
        """统一时区处理"""
        if series.empty:
            return series
            
        # 确保索引是DatetimeIndex
        if not isinstance(series.index, pd.DatetimeIndex):
            series.index = pd.to_datetime(series.index)
        
        # 处理时区 - 转换为本地时间
        if series.index.tz is not None:
            series.index = series.index.tz_localize(None)
        
        # 确保索引名称统一
        series.index.name = 'date'
        series.name = symbol
        
        return series
        
    def download_fred_data(self, symbols, start_date, end_date):
        """下载FRED数据"""
        results = {}
        
        if not self.fred_available:
            print("⚠️  FRED API不可用，跳过FRED数据")
            for symbol in symbols:
                results[symbol] = pd.Series(name=symbol)
            return results
            
        print(f"📊 正在从FRED下载 {len(symbols)} 个指标...")
        success_count = 0
        
        for symbol in symbols:
            try:
                self.rate_limit('fred')
                data = self.fred.get_series(symbol, start=start_date, end=end_date)
                data = self.normalize_series_timezone(data, symbol)
                results[symbol] = data
                success_count += 1
                print(f"  ✅ {symbol}: {len(data)} 数据点")
            except Exception as e:
                print(f"  ❌ {symbol}: {str(e)}")
                results[symbol] = pd.Series(name=symbol)
        
        print(f"FRED数据下载完成: {success_count}/{len(symbols)} 成功")
        return results
    
    def download_yahoo_data(self, symbols, start_date, end_date, price_type="Close"):
        """下载Yahoo Finance数据"""
        results = {}
        
        # 扩展的符号修正映射
        symbol_corrections = {
            "DX-Y.NYB": "DX=F",
           # "^MOVE": "^TNX",
          #  "^SKEW": "^VIX",  # 如果SKEW不可用，用VIX代替
        }
        
        corrected_symbols = []
        symbol_map = {}
        
        for symbol in symbols:
            if symbol in symbol_corrections:
                corrected_symbol = symbol_corrections[symbol]
                corrected_symbols.append(corrected_symbol)
                symbol_map[corrected_symbol] = symbol
                print(f"  📝 符号修正: {symbol} -> {corrected_symbol}")
            else:
                corrected_symbols.append(symbol)
                symbol_map[symbol] = symbol
        
        print(f"📈 正在从Yahoo Finance下载 {len(corrected_symbols)} 个指标...")
        success_count = 0
        
        for symbol in corrected_symbols:
            try:
                self.rate_limit('yahoo')
                ticker = yf.Ticker(symbol,session=self.yahoo_session)
                
                # 多种数据获取方式
                data = None
                methods = [
                    lambda: ticker.history(
                        start=start_date, 
                        end=end_date,
                        auto_adjust=True,
                        prepost=False,
                        actions=False
                    )[price_type],
                    lambda: yf.download(
                        symbol, 
                        start=start_date, 
                        end=end_date,
                        progress=False
                    )[price_type],
                    lambda: ticker.history(period="5y")[price_type].loc[start_date:end_date]
                ]
                
                for method in methods:
                    try:
                        data = method()
                        if not data.empty:
                            break
                    except:
                        continue
                
                if data is not None and not data.empty:
                    original_symbol = symbol_map[symbol]
                    data = self.normalize_series_timezone(data, original_symbol)
                    results[original_symbol] = data
                    success_count += 1
                    print(f"  ✅ {original_symbol}: {len(data)} 数据点")
                else:
                    print(f"  ❌ {symbol_map[symbol]}: 无数据")
                    results[symbol_map[symbol]] = pd.Series(name=symbol_map[symbol])
                    
            except Exception as e:
                print(f"  ❌ {symbol_map[symbol]}: {str(e)}")
                results[symbol_map[symbol]] = pd.Series(name=symbol_map[symbol])
        
        print(f"Yahoo数据下载完成: {success_count}/{len(corrected_symbols)} 成功")
        return results
    
    def calculate_derived_indicators(self, data_dict):
        """计算衍生指标"""
        derived = {}
        print("📊 正在计算衍生指标...")
        
        try:
            # 利差计算
            if 'DGS10' in data_dict and 'DGS2' in data_dict:
                dgs10 = data_dict['DGS10'].dropna()
                dgs2 = data_dict['DGS2'].dropna()
                if not dgs10.empty and not dgs2.empty:
                    aligned_data = pd.DataFrame({'DGS10': dgs10, 'DGS2': dgs2}).dropna()
                    if not aligned_data.empty:
                        derived['T10Y2Y_CALC'] = (aligned_data['DGS10'] - aligned_data['DGS2'])
                        derived['T10Y2Y_CALC'].name = 'T10Y2Y_CALC'
                        print("  ✅ 计算10Y-2Y利差")
            
            # 高收益债与投资级债利差
            if 'BAMLH0A0HYM2' in data_dict and 'BAMLC0A0CM' in data_dict:
                hy = data_dict['BAMLH0A0HYM2'].dropna()
                ig = data_dict['BAMLC0A0CM'].dropna()
                if not hy.empty and not ig.empty:
                    aligned_data = pd.DataFrame({'HY': hy, 'IG': ig}).dropna()
                    if not aligned_data.empty:
                        derived['HY_IG_SPREAD'] = (aligned_data['HY'] - aligned_data['IG'])
                        derived['HY_IG_SPREAD'].name = 'HY_IG_SPREAD'
                        print("  ✅ 计算HY-IG利差")
            
            # 原油价差
            if 'BZ=F' in data_dict and 'CL=F' in data_dict:
                brent = data_dict['BZ=F'].dropna()
                wti = data_dict['CL=F'].dropna()
                if not brent.empty and not wti.empty:
                    aligned_data = pd.DataFrame({'BRENT': brent, 'WTI': wti}).dropna()
                    if not aligned_data.empty:
                        derived['BRENT_WTI_SPREAD'] = (aligned_data['BRENT'] - aligned_data['WTI'])
                        derived['BRENT_WTI_SPREAD'].name = 'BRENT_WTI_SPREAD'
                        print("  ✅ 计算Brent-WTI价差")
            
            # VIX相对位置指标
            if 'VIXCLS' in data_dict:
                vix = data_dict['VIXCLS'].dropna()
                if len(vix) > 252:  # 至少一年的数据
                    derived['VIX_PERCENTILE_1Y'] = vix.rolling(252).rank(pct=True) * 100
                    derived['VIX_PERCENTILE_1Y'].name = 'VIX_PERCENTILE_1Y'
                    print("  ✅ 计算VIX一年百分位数")
            
            # 美元强弱指数 (如果有多个汇率)
            fx_pairs = ['EUR=X', 'JPY=X', 'GBP=X', 'CNY=X']
            available_fx = [pair for pair in fx_pairs if pair in data_dict and not data_dict[pair].empty]
            if len(available_fx) >= 2:
                fx_data = pd.DataFrame({pair: data_dict[pair] for pair in available_fx}).dropna()
                if not fx_data.empty:
                    # 简单的美元强弱指数 (汇率倒数的几何平均)
                    usd_strength = np.exp(np.log(1/fx_data).mean(axis=1))
                    derived['USD_STRENGTH_INDEX'] = usd_strength
                    derived['USD_STRENGTH_INDEX'].name = 'USD_STRENGTH_INDEX'
                    print(f"  ✅ 计算美元强弱指数 (基于{len(available_fx)}个货币对)")
                        
        except Exception as e:
            print(f"❌ 计算衍生指标时出错: {str(e)}")
        
        print(f"衍生指标计算完成: {len(derived)} 个指标")
        return derived
    
    def create_analysis_dataframe(self, data_dict):
        """创建分析用的数据框"""
        print("\n🔄 正在合并数据...")
        
        # 收集所有有效的序列
        all_series = {}
        data_info = []
        
        for category, cat_data in data_dict.items():
            for symbol, series in cat_data.items():
                if not series.empty and len(series) > 0:
                    series = self.normalize_series_timezone(series, symbol)
                    all_series[symbol] = series
                    data_info.append({
                        'Symbol': symbol,
                        'Category': category,
                        'Length': len(series),
                        'Start': series.index.min().strftime('%Y-%m-%d'),
                        'End': series.index.max().strftime('%Y-%m-%d'),
                        'Missing_Pct': (series.isnull().sum() / len(series) * 100)
                    })
        
        if not all_series:
            print("❌ 没有有效数据")
            return pd.DataFrame()
        
        print(f"📊 找到 {len(all_series)} 个有效序列，正在合并...")
        
        # 创建DataFrame
        df = pd.DataFrame(all_series)
        
        # 统一处理索引
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df = df.sort_index()
        
        # 添加元数据
        df.attrs = {
            'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_indicators': len(df.columns),
            'date_range': f"{df.index.min()} to {df.index.max()}",
            'categories': list(DATA_CATEGORIES.keys())
        }
        
        # 打印数据质量信息
        info_df = pd.DataFrame(data_info)
        print("\n📈 数据质量概览:")
        if not info_df.empty:
            quality_summary = info_df.groupby('Category').agg({
                'Length': ['count', 'mean', 'min', 'max'],
                'Missing_Pct': 'mean'
            }).round(2)
            print(quality_summary)
        
        print(f"✅ 数据合并完成! ({df.shape[0]} 行 × {df.shape[1]} 列)")
        return df
    
    def download_category_data(self, category, start_date, end_date):
        """按分类下载数据"""
        if category not in DATA_CATEGORIES:
            raise ValueError(f"未知分类: {category}. 可用分类: {list(DATA_CATEGORIES.keys())}")
        
        cat_info = DATA_CATEGORIES[category]
        indicators = cat_info['indicators']
        
        print(f"\n{'='*60}")
        print(f"📡 下载 {category} 数据")
        print(f"{'='*60}")
        
        # 按数据源分组
        fred_symbols = []
        yahoo_symbols = []
        
        for symbol, info in indicators.items():
            source = info.get('source', 'yahoo').lower()
            if source == 'fred':
                fred_symbols.append(symbol)
            else:  # yahoo 或其他
                yahoo_symbols.append(symbol)
        
        results = {}
        
        # 下载FRED数据
        if fred_symbols:
            fred_data = self.download_fred_data(fred_symbols, start_date, end_date)
            results.update(fred_data)
        
        # 下载Yahoo数据
        if yahoo_symbols:
            yahoo_data = self.download_yahoo_data(yahoo_symbols, start_date, end_date)
            results.update(yahoo_data)
        
        return results
    
    def download_all_data(self, start_date='2018-01-01', end_date=None, categories=None):
        """下载所有或指定分类的数据"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if categories is None:
            categories = list(DATA_CATEGORIES.keys())
        elif isinstance(categories, str):
            categories = [categories]
        
        print(f"📅 数据时间范围: {start_date} 至 {end_date}")
        print(f"📁 下载分类: {categories}")
        
        all_data = {}
        
        for category in categories:
            if category not in DATA_CATEGORIES:
                print(f"⚠️  跳过未知分类: {category}")
                continue
                
            try:
                category_data = self.download_category_data(category, start_date, end_date)
                all_data[category] = category_data
                time.sleep(1)  # API限制缓冲
            except Exception as e:
                print(f"❌ 下载 {category} 时出错: {str(e)}")
        
        # 计算衍生指标
        flat_data = {}
        for cat_data in all_data.values():
            flat_data.update(cat_data)
        
        if flat_data:  # 只有在有数据时才计算衍生指标
            derived = self.calculate_derived_indicators(flat_data)
            if derived:
                all_data['衍生指标'] = derived
        
        return all_data

def get_fred_api_key():
    """智能获取FRED API Key"""
    # 方法1: 从环境变量获取
    api_key = os.environ.get('FRED_API_KEY')
    if api_key:
        print(f"✅ 从环境变量获取API Key: {api_key[:8]}...{api_key[-4:]}")
        return api_key
    
    # 方法2: 从用户输入获取
    print("🔑 请输入您的FRED API Key:")
    print("   (如果没有，请访问: https://fred.stlouisfed.org/docs/api/api_key.html)")
    api_key = input("API Key: ").strip()
    
    return api_key if api_key else None

# 增强的使用函数
def main():
    print("🚀 全球宏观数据下载系统启动")
    print("="*60)
    
    # 智能获取API Key
    FRED_API_KEY = "b847c3439da156aed56440cd5685d03a"  # 直接设置您的API Key
    
    if not FRED_API_KEY or FRED_API_KEY == "your_api_key_here":
        FRED_API_KEY = get_fred_api_key()
    
    loader = GlobalMacroDataLoader(FRED_API_KEY)
    
    # 显示可用分类和指标
    loader.list_categories()
    
    # 下载数据
    start_date = '2018-01-01'  # 缩短时间范围以提高下载成功率
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 可以选择特定分类下载
    # categories = ['全球风险情绪', '信用与流动性']  # 指定分类
    categories = None  # 下载所有分类
    
    all_data = loader.download_all_data(start_date, end_date, categories)
    
    # 创建分析DataFrame
    df = loader.create_analysis_dataframe(all_data)
    
    if df.empty:
        print("❌ 创建DataFrame失败")
        return None, all_data
    
    # 数据质量报告
    print("\n" + "="*60)
    print("📊 数据质量报告")
    print("="*60)
    
    # 缺失值分析
    missing_summary = df.isnull().sum().sort_values(ascending=False)
    print("缺失值情况（前10）:")
    for col, missing in missing_summary.head(10).items():
        missing_pct = missing / len(df) * 100 if len(df) > 0 else 0
        print(f"   {col:25}: {missing:5,} ({missing_pct:5.1f}%)")
    
    print(f"\n📈 数据概况:")
    print(f"   时间范围: {df.index.min().strftime('%Y-%m-%d')} 至 {df.index.max().strftime('%Y-%m-%d')}")
    print(f"   指标数量: {len(df.columns)}")
    print(f"   观察值: {df.shape[0]:,} 行 × {df.shape[1]} 列")
    print(f"   数据密度: {(1 - df.isnull().sum().sum() / df.size) * 100:.1f}%")
    
    # 保存数据
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'global_macro_data_{timestamp}.csv'
        excel_filename = f'global_macro_data_{timestamp}.xlsx'
        
        df.to_csv(csv_filename)
        print(f"✅ CSV数据已保存: {csv_filename}")
        
        # Excel格式，包含指标说明
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data')
            
            # 指标说明
            indicator_info = []
            for category, cat_info in DATA_CATEGORIES.items():
                for symbol, info in cat_info['indicators'].items():
                    indicator_info.append({
                        'Symbol': symbol,
                        'Name': info['name'],
                        'Category': category,
                        'Source': info.get('source', 'unknown'),
                        'Frequency': info.get('freq', 'unknown'),
                        'Available': symbol in df.columns,
                        'Data_Points': len(df[symbol].dropna()) if symbol in df.columns else 0
                    })
            
            pd.DataFrame(indicator_info).to_excel(writer, sheet_name='Indicators', index=False)
            
            # 数据质量汇总
            quality_df = pd.DataFrame({
                'Indicator': df.columns,
                'Data_Points': df.count(),
                'Missing_Count': df.isnull().sum(),
                'Missing_Pct': (df.isnull().sum() / len(df) * 100).round(2),
                'First_Date': [df[col].dropna().index.min().strftime('%Y-%m-%d') 
                              if not df[col].dropna().empty else 'N/A' for col in df.columns],
                'Last_Date': [df[col].dropna().index.max().strftime('%Y-%m-%d') 
                             if not df[col].dropna().empty else 'N/A' for col in df.columns]
            })
            quality_df.to_excel(writer, sheet_name='Data_Quality', index=False)
        
        print(f"✅ Excel数据已保存: {excel_filename}")
        
    except Exception as e:
        print(f"❌ 保存文件时出错: {str(e)}")
    
    return df, all_data, loader





# 运行代码
if __name__ == "__main__":
    df, raw_data, loader = main()
    if df is not None:
        show_analysis_summary(df)
        
    # 显示使用示例
    print("\n💡 要查看使用示例，请运行: example_usage()")





# 第三框架：全球风险情绪指标专业解读（JSON版本）
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

class RiskSentimentAnalyzer:
    """全球风险情绪指标分析器"""
    
    def __init__(self):
        # 直接使用已下载的数据
        self.data = df  # 第一框架的数据
        self.config = DATA_CATEGORIES  # 第一框架的配置
        print(f"📊 风险情绪分析器启动 - 数据截至: {self.data.index.max().strftime('%Y-%m-%d')}")
    
    def _calculate_change(self, series, periods):
        """计算变化率的辅助方法"""
        if len(series) < abs(periods):
            return 0
        try:
            current = series.iloc[-1]
            past = series.iloc[periods]
            return ((current - past) / past * 100) if past != 0 else 0
        except:
            return 0
    
    def _detect_frequency(self, series):
        """检测数据频率的辅助方法"""
        try:
            # 简单的频率检测逻辑
            if len(series) < 2:
                return 'daily'
            
            # 计算时间间隔
            intervals = pd.Series(series.index).diff().dropna()
            median_interval = intervals.median()
            
            if median_interval <= pd.Timedelta(days=1):
                return 'daily'
            elif median_interval <= pd.Timedelta(days=7):
                return 'weekly'
            elif median_interval <= pd.Timedelta(days=31):
                return 'monthly'
            else:
                return 'daily'
        except:
            return 'daily'
        
    def analyze_vix(self):
        """分析VIX恐慌指数"""
        if 'VIXCLS' not in self.data.columns:
            return {"status": "unavailable", "message": "VIX数据不可用"}
        
        series = self.data['VIXCLS'].dropna()
        if len(series) == 0:
            return {"status": "no_data"}
            
        current = series.iloc[-1]
        
        # 统计分析
        percentile_1y = (series.tail(252) <= current).mean() * 100 if len(series) >= 252 else 50
        change_1w = ((current - series.iloc[-6]) / series.iloc[-6] * 100) if len(series) > 5 else 0
        change_1m = ((current - series.iloc[-21]) / series.iloc[-21] * 100) if len(series) > 20 else 0
        
        # VIX制度分析
        if current < 15:
            regime = "低波动制度"
            risk_assessment = "投资者风险偏好极高，但尾部风险积累"
            market_implication = "流动性充裕环境下的风险积累期，警惕均值回归"
        elif current < 25:
            regime = "正常波动制度" 
            risk_assessment = "市场风险定价功能正常"
            market_implication = "投资者情绪相对均衡，市场结构稳定"
        elif current < 40:
            regime = "压力波动制度"
            risk_assessment = "系统性压力显现，风险厌恶情绪升温"
            market_implication = "市场结构调整期，资产重新定价"
        else:
            regime = "恐慌波动制度"
            risk_assessment = "流动性危机概率显著上升"
            market_implication = "强制去杠杆环境，资本配置效率急剧下降"
        
        return {
            "indicator": "VIX波动率指数",
            "current_value": round(float(current), 2),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1w": round(change_1w, 1),
                "change_1m": round(change_1m, 1),
                "long_term_average": 19.2
            },
            "regime": regime,
            "risk_assessment": risk_assessment,
            "market_implication": market_implication,
            "thresholds": {
                "low_volatility": 15,
                "normal": 25,
                "stress": 40
            }
        }

    def analyze_fed_rrp(self):
        """分析美联储逆回购"""
        if 'RRPONTSYD' not in self.data.columns:
            return {"status": "unavailable", "message": "美联储逆回购数据不可用"}
        
        series = self.data['RRPONTSYD'].dropna()
        if len(series) == 0:
            return {"status": "no_data"}
            
        current = series.iloc[-1]
        current_trillion = current / 1000  # 转换为万亿美元
        
        # 变动分析
        change_1m = ((current - series.iloc[-21]) / series.iloc[-21] * 100) if len(series) > 20 else 0
        
        # 制度分析
        if current_trillion < 0.5:
            regime = "正常流动性传导"
            policy_signal = "货币政策传导机制有效，银行风险偏好正常"
            systemic_risk = "低"
        elif current_trillion < 1.5:
            regime = "适度流动性堆积"
            policy_signal = "银行体系谨慎但功能正常"
            systemic_risk = "中低"
        elif current_trillion < 2.5:
            regime = "显著流动性回流"
            policy_signal = "货币政策传导受阻，银行风险偏好收缩"
            systemic_risk = "中等"
        else:
            regime = "极端流动性淤积"
            policy_signal = "货币政策几乎失效，银行体系功能障碍"
            systemic_risk = "高"
        
        return {
            "indicator": "美联储逆回购余额",
            "current_value": round(float(current_trillion), 2),
            "unit": "万亿美元",
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "change_1m": round(change_1m, 1),
                "systemic_risk": systemic_risk
            },
            "regime": regime,
            "policy_signal": policy_signal,
            "thresholds": {
                "normal": 0.5,
                "moderate": 1.5,
                "significant": 2.5
            }
        }

    def analyze_dollar_index(self):
        """分析美元指数"""
        if 'DX-Y.NYB' not in self.data.columns:
            return {"status": "unavailable", "message": "美元指数数据不可用"}
        
        series = self.data['DX-Y.NYB'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_date = series.index[-1]
        
        # 基于日期索引的统计分析
        one_year_ago = current_date - pd.DateOffset(years=1)
        data_in_last_year = series[series.index >= one_year_ago]
        percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
        
        # 计算变化率
        change_1w = self._calculate_change(series, -5)   # 约1周
        change_1m = self._calculate_change(series, -21)  # 约1个月
        change_1y = self._calculate_change(series, -252) # 约1年
        
        # 趋势分析
        ma_20 = series.rolling(20).mean().iloc[-1] if len(series) >= 20 else current
        trend_direction = "上升" if current > ma_20 else "下降"
       
        # 美元指数全球金融条件分析
        # 美元指数全球金融条件分析（专业版）
        if current < 90:
            regime = "深度弱势区间"
            risk_assessment = "反映美国相对增长疲软或极度宽松货币政策"
            market_implication = "利好新兴市场资本流入，大宗商品计价优势，但可能隐含美国经济结构性担忧"
        elif current < 95:
            regime = "温和弱势区间" 
            risk_assessment = "全球风险偏好回升，利差交易活跃"
            market_implication = "支持风险资产表现，新兴市场融资条件改善，企业海外收入折算压力"
        elif current < 100:
            regime = "中性偏低区间"
            risk_assessment = "反映相对均衡的全球增长预期"
            market_implication = "跨境资本流动相对稳定，汇率波动率处于正常范围"
        elif current < 105:
            regime = "中性偏强区间"
            risk_assessment = "美国经济增长相对稳健，利率优势显现"
            market_implication = "美元资产吸引力提升，但新兴市场面临温和资本流出压力"
        elif current < 110:
            regime = "强势区间"
            risk_assessment = "美国经济相对优势明显，避险需求或政策分化驱动"
            market_implication = "全球美元流动性收紧，新兴市场债务偿付压力增大，大宗商品承压"
        elif current < 115:
            regime = "极端强势区间"
            risk_assessment = "通常伴随全球风险厌恶或主要央行政策严重分化"
            market_implication = "可能引发新兴市场汇率危机，全球贸易融资成本显著上升"
        else:
            regime = "历史异常高位"
            risk_assessment = "反映系统性危机或极度政策不确定性"
            market_implication = "全球美元荒风险，跨境资本流动停滞，亟需央行政策协调"
               
        # 趋势判断（基于月度变化）
        if change_1m > 8:
            trend = "快速升值"
            trend_implication = "美联储政策急剧收紧，全球避险需求激增"
        elif change_1m > 3:
            trend = "温和升值"
            trend_implication = "美国相对经济强势，资本回流美国"
        elif change_1m < -8:
            trend = "快速贬值"
            trend_implication = "美联储政策转向宽松，全球风险偏好回升"
        elif change_1m < -3:
            trend = "温和贬值"
            trend_implication = "美国经济相对疲弱，全球流动性改善"
        else:
            trend = "基本稳定"
            trend_implication = "汇率政策保持稳定，市场预期一致"
    
        # 政策含义分析
        if current > 115:
            policy_implication = "美联储可能面临政策两难，需要在抗通胀与维护金融稳定间平衡"
        elif current > 105:
            policy_implication = "美国货币政策相对收紧，需要关注新兴市场溢出效应"
        elif current < 95:
            policy_implication = "美国货币政策相对宽松，需要警惕输入性通胀风险"
        else:
            policy_implication = "货币政策立场中性，政策传导机制相对正常"
        
        return {
            "indicator": "美元指数(DXY)",
            "current_value": round(float(current), 2),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1w": round(change_1w, 1),
                "change_1m": round(change_1m, 1),
                "change_1y": round(change_1y, 1),
                "ma_20": round(float(ma_20), 2),
                "trend_direction": trend_direction,
                "long_term_average": 96.5
            },
            "regime": regime,
            "trend": trend,
            "risk_assessment": risk_assessment,
            "market_implication": market_implication,
            "trend_implication": trend_implication,
            "policy_implication": policy_implication,
            "thresholds": {
                "extreme_weak": 90,
                "weak": 95,
                "balanced": 105,
                "strong": 115,
                "extreme_strong": 125
            }
        }

    def analyze_walcl(self):  # 修正：添加 self 参数
        """分析美联储资产负债表规模(WALCL)"""
        if 'WALCL' not in self.data.columns:
            return {"status": "unavailable", "message": "WALCL数据不可用"}
        
        series = self.data['WALCL'].dropna()
        if len(series) < 2:  # 至少需要2个数据点才能计算变化
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_trillion = current / 1_000_000  # 转换为万亿美元
        current_date = series.index[-1]
        
        # 检测数据频率
        freq = self._detect_frequency(series)
        
        # 基于检测到的频率计算变化率
        if freq == 'weekly':
            # 周度数据：使用前1周、前4周、前52周
            change_1w = self._calculate_change(series, -1)  # 前1个周度点
            change_1m = self._calculate_change(series, -4)  # 前4个周度点 ≈ 1个月
            change_1y = self._calculate_change(series, -52) # 前52个周度点 ≈ 1年
        elif freq == 'monthly':
            # 月度数据：使用前1月、前3月、前12月
            change_1w = 0  # 周变化对月度数据无意义
            change_1m = self._calculate_change(series, -1)  # 前1个月度点
            change_1y = self._calculate_change(series, -12) # 前12个月度点
        else:
            # 默认按日度处理或其他频率
            change_1w = self._calculate_change(series, -5)  # 约1周
            change_1m = self._calculate_change(series, -21) # 约1个月
            change_1y = self._calculate_change(series, -252) # 约1年
        
        # 计算1年百分位（基于日期）
        one_year_ago = current_date - pd.DateOffset(years=1)
        data_in_last_year = series[series.index >= one_year_ago]
        percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
        
        # WALCL流动性制度分析
        if current_trillion > 8.0:
            regime = "极度宽松流动性"
            risk_assessment = "央行资产负债表极度扩张，潜在通胀压力"
            market_implication = "流动性驱动市场，资产价格可能脱离基本面"
        elif current_trillion > 6.5:
            regime = "宽松流动性"
            risk_assessment = "流动性环境充裕，支持风险资产表现"
            market_implication = "央行政策支持下的风险偏好环境"
        elif current_trillion > 4.0:
            regime = "正常流动性"
            risk_assessment = "资产负债表规模处于历史常态区间"
            market_implication = "市场流动性条件相对均衡"
        else:
            regime = "紧缩流动性"
            risk_assessment = "央行资产负债表收缩，流动性收紧"
            market_implication = "去杠杆环境，需要警惕流动性风险"
        
        # 趋势判断（基于1个月变化）
        if change_1m > 5.0:
            trend = "快速扩张"
            trend_implication = "央行正在积极投放流动性"
        elif change_1m > 1.0:
            trend = "温和扩张" 
            trend_implication = "流动性环境逐步改善"
        elif change_1m < -5.0:
            trend = "快速收缩"
            trend_implication = "量化紧缩正在进行中"
        elif change_1m < -1.0:
            trend = "温和收缩"
            trend_implication = "流动性环境逐步收紧"
        else:
            trend = "基本稳定"
            trend_implication = "资产负债表规模保持稳定"
        
        return {
            "indicator": "美联储资产负债表规模",
            "current_value": round(float(current), 2),
            "current_value_trillion": round(current_trillion, 3),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "data_frequency": freq,
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1w": round(change_1w, 1),
                "change_1m": round(change_1m, 1),
                "change_1y": round(change_1y, 1),
                "long_term_median": round(series.median() / 1_000_000, 2)
            },
            "regime": regime,
            "trend": trend,
            "risk_assessment": risk_assessment,
            "market_implication": market_implication,
            "trend_implication": trend_implication,
            "unit": "百万美元",
            "unit_trillion": "万亿美元"
        }

    def analyze_skew(self):  # 修正：添加 self 参数
        """分析SKEW偏度指数"""
        if '^SKEW' not in self.data.columns:
            return {"status": "unavailable", "message": "SKEW数据不可用"}
        
        series = self.data['^SKEW'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_date = series.index[-1]
        
        # 基于日期索引的统计分析
        one_year_ago = current_date - pd.DateOffset(years=1)
        data_in_last_year = series[series.index >= one_year_ago]
        percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
        
        # 计算变化率（日度数据）
        change_1w = self._calculate_change(series, -5)   # 约1周
        change_1m = self._calculate_change(series, -21)  # 约1个月
        change_1y = self._calculate_change(series, -252) # 约1年
        
        # SKEW市场情绪分析
        if current > 150:
            regime = "极端尾部风险预期"
            risk_assessment = "市场预期极端事件概率显著上升"
            market_implication = "投资者对冲需求强烈，恐慌情绪蔓延"
        elif current > 140:
            regime = "高尾部风险预期"
            risk_assessment = "市场对黑天鹅事件担忧加剧"
            market_implication = "风险偏好下降，避险情绪升温"
        elif current > 130:
            regime = "中性偏谨慎"
            risk_assessment = "市场对风险保持警惕"
            market_implication = "投资者情绪谨慎，波动可能增加"
        else:
            regime = "正常风险预期"
            risk_assessment = "市场风险预期处于正常范围"
            market_implication = "情绪相对稳定，市场运行正常"
        
        # 趋势判断
        if change_1m > 10:
            trend = "快速上升"
            trend_implication = "市场恐慌情绪迅速升温"
        elif change_1m > 3:
            trend = "温和上升"
            trend_implication = "风险担忧逐步增加"
        elif change_1m < -10:
            trend = "快速下降"
            trend_implication = "市场恐慌情绪缓解"
        elif change_1m < -3:
            trend = "温和下降"
            trend_implication = "风险担忧逐步减轻"
        else:
            trend = "基本稳定"
            trend_implication = "市场情绪保持稳定"
        
        return {
            "indicator": "SKEW偏度指数",
            "current_value": round(float(current), 2),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1w": round(change_1w, 1),
                "change_1m": round(change_1m, 1),
                "change_1y": round(change_1y, 1),
                "long_term_average": 135.0
            },
            "regime": regime,
            "trend": trend,
            "risk_assessment": risk_assessment,
            "market_implication": market_implication,
            "trend_implication": trend_implication,
            "thresholds": {
                "extreme_risk": 150,
                "high_risk": 140,
                "cautious": 130
            }
        }

    def analyze_move(self):
        """分析MOVE债券波动率指数"""
        if '^MOVE' not in self.data.columns:
            return {"status": "unavailable", "message": "MOVE数据不可用"}
        
        series = self.data['^MOVE'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_date = series.index[-1]
        
        # 基于日期索引的统计分析
        one_year_ago = current_date - pd.DateOffset(years=1)
        data_in_last_year = series[series.index >= one_year_ago]
        percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
        
        # 计算变化率
        change_1w = self._calculate_change(series, -5)   # 约1周
        change_1m = self._calculate_change(series, -21)  # 约1个月
        change_1y = self._calculate_change(series, -252) # 约1年
        
        # MOVE债券市场情绪分析
        if current > 140:
            regime = "极端债券波动制度"
            risk_assessment = "债券市场面临极端压力，流动性危机风险"
            market_implication = "利率环境高度不确定，债券投资组合面临重大损失风险"
        elif current > 120:
            regime = "高债券波动制度"
            risk_assessment = "债券市场波动剧烈，利率风险显著上升"
            market_implication = "货币政策预期分化，固收资产配置需谨慎"
        elif current > 100:
            regime = "中等债券波动制度"
            risk_assessment = "债券市场存在一定压力"
            market_implication = "利率环境存在不确定性，关注央行政策信号"
        elif current > 80:
            regime = "正常债券波动制度"
            risk_assessment = "债券市场波动处于正常范围"
            market_implication = "利率环境相对稳定，债券配置环境良好"
        else:
            regime = "低债券波动制度"
            risk_assessment = "债券市场异常平静，可能存在风险积累"
            market_implication = "利率环境过于稳定，警惕均值回归风险"
        
        # 趋势判断
        if change_1m > 15:
            trend = "快速上升"
            trend_implication = "债券市场恐慌情绪快速蔓延"
        elif change_1m > 5:
            trend = "温和上升"
            trend_implication = "债券市场风险担忧逐步增加"
        elif change_1m < -15:
            trend = "快速下降"
            trend_implication = "债券市场风险情绪快速缓解"
        elif change_1m < -5:
            trend = "温和下降"
            trend_implication = "债券市场恐慌情绪逐步减轻"
        else:
            trend = "基本稳定"
            trend_implication = "债券市场情绪保持稳定"
    
        return {
            "indicator": "MOVE债券波动率指数",
            "current_value": round(float(current), 2),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1w": round(change_1w, 1),
                "change_1m": round(change_1m, 1),
                "change_1y": round(change_1y, 1),
                "long_term_average": 95.0
            },
            "regime": regime,
            "trend": trend,
            "risk_assessment": risk_assessment,
            "market_implication": market_implication,
            "trend_implication": trend_implication,
            "thresholds": {
                "extreme_volatility": 140,
                "high_volatility": 120,
                "moderate_volatility": 100,
                "normal_volatility": 80
            }
        }
    def analyze_yield_curve_t10y2y(self):
        """分析T10Y2Y收益率曲线（10年期-2年期国债收益率利差）"""
        if 'T10Y2Y' not in self.data.columns:
            return {"status": "unavailable", "message": "T10Y2Y收益率利差数据不可用"}
        
        series = self.data['T10Y2Y'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_date = series.index[-1]
        
        # 基于日期索引的统计分析
        one_year_ago = current_date - pd.DateOffset(years=1)
        data_in_last_year = series[series.index >= one_year_ago]
        percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
        
        # 计算变化率（基点变化更有意义）
        change_1w_bp = (current - series.iloc[-5]) * 100 if len(series) > 5 else 0  # 转换为基点
        change_1m_bp = (current - series.iloc[-21]) * 100 if len(series) > 21 else 0
        change_1y_bp = (current - series.iloc[-252]) * 100 if len(series) > 252 else 0
    
        # 计算百分比变化（用于趋势判断）
        change_1w = self._calculate_change(series, -5)   # 约1周
        change_1m = self._calculate_change(series, -21)  # 约1个月
        change_1y = self._calculate_change(series, -252) # 约1年
    
        # 收益率曲线形态与货币政策传导效率分析
        if current < -1.0:
            regime = "深度倒挂制度"
            risk_assessment = "货币政策传导严重失效，经济衰退风险极高"
            market_implication = "银行净息差压缩至危险水平，信贷投放意愿极低"
            policy_transmission = "极度无效"
            recession_probability = "极高(>80%)"
        elif current < -0.5:
            regime = "倒挂制度"
            risk_assessment = "货币政策传导效率显著下降，衰退信号强烈"
            market_implication = "银行盈利能力受损，流动性传导受阻"
            policy_transmission = "严重受阻"
            recession_probability = "很高(60-80%)"
        elif current < 0:
            regime = "轻微倒挂制度"
            risk_assessment = "货币政策传导开始受阻，经济放缓信号"
            market_implication = "银行业务模式面临挑战，信贷增长放缓"
            policy_transmission = "受阻"
            recession_probability = "较高(30-60%)"
        elif current < 0.5:
            regime = "平坦化制度"
            risk_assessment = "货币政策传导效率偏低，增长动能不足"
            market_implication = "银行净息差收窄，风险偏好谨慎"
            policy_transmission = "低效"
            recession_probability = "中等(10-30%)"
        elif current < 1.5:
            regime = "正常陡峭制度"
            risk_assessment = "货币政策传导机制正常，经济增长预期健康"
            market_implication = "银行盈利模式可持续，流动性传导顺畅"
            policy_transmission = "有效"
            recession_probability = "较低(<10%)"
        elif current < 2.5:
            regime = "陡峭制度"
            risk_assessment = "货币政策传导效率较高，通胀预期可能上升"
            market_implication = "银行净息差扩大，信贷投放积极"
            policy_transmission = "高效"
            recession_probability = "很低(<5%)"
        else:
            regime = "过度陡峭制度"
            risk_assessment = "可能存在通胀失控风险或流动性过度宽松"
            market_implication = "金融条件过度宽松，资产泡沫风险上升"
            policy_transmission = "过度宽松"
            recession_probability = "极低但通胀风险高"
    
        # 趋势判断（基于基点变化）
        if change_1m_bp > 50:
            trend = "快速陡峭化"
            trend_implication = "通胀预期快速上升或货币政策转向宽松"
        elif change_1m_bp > 20:
            trend = "温和陡峭化"
            trend_implication = "经济预期改善，长端利率上升"
        elif change_1m_bp < -50:
            trend = "快速平坦化"
            trend_implication = "衰退预期强化或央行政策收紧预期"
        elif change_1m_bp < -20:
            trend = "温和平坦化"
            trend_implication = "增长担忧上升，避险需求增加"
        else:
            trend = "基本稳定"
            trend_implication = "市场对货币政策和经济前景预期稳定"
    
        # 系统性风险评估
        if current < -0.5:
            systemic_risk = "高"
            liquidity_risk = "信贷紧缩风险高，银行体系脆弱性上升"
        elif current < 0:
            systemic_risk = "中高"
            liquidity_risk = "流动性传导机制受损，需密切关注"
        elif current < 0.5:
            systemic_risk = "中等"
            liquidity_risk = "流动性传导效率偏低但可控"
        else:
            systemic_risk = "低"
            liquidity_risk = "流动性传导机制运行良好"
        
        # 政策含义
        if current < -0.5:
            policy_implication = "央行应考虑降息或量化宽松，避免经济硬着陆"
        elif current < 0:
            policy_implication = "央行政策空间有限，需要创新货币政策工具"
        elif current > 2.5:
            policy_implication = "央行可能需要收紧政策，防范通胀和资产泡沫"
        else:
            policy_implication = "货币政策立场相对合适，保持观察"
    
        return {
            "indicator": "T10Y2Y收益率利差",
            "current_value": round(float(current), 3),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1w_bp": round(change_1w_bp, 1),
                "change_1m_bp": round(change_1m_bp, 1),
                "change_1y_bp": round(change_1y_bp, 1),
                "change_1w": round(change_1w, 1),
                "change_1m": round(change_1m, 1),
                "change_1y": round(change_1y, 1),
                "long_term_average": 1.2
            },
            "regime": regime,
            "trend": trend,
            "risk_assessment": risk_assessment,
            "market_implication": market_implication,
            "trend_implication": trend_implication,
            "policy_implication": policy_implication,
            "policy_transmission": policy_transmission,
            "recession_probability": recession_probability,
            "systemic_risk": systemic_risk,
            "liquidity_risk": liquidity_risk,
            "thresholds": {
                "deep_inversion": -1.0,
                "inversion": -0.5,
                "slight_inversion": 0,
                "flat": 0.5,
                "normal_steep": 1.5,
                "steep": 2.5
            }
        }

    def analyze_hy_credit_spread(self):
        """分析美国高收益债信用利差(BAMLH0A0HYM2)"""
        if 'BAMLH0A0HYM2' not in self.data.columns:
            return {"status": "unavailable", "message": "高收益债信用利差数据不可用"}
        
        series = self.data['BAMLH0A0HYM2'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_date = series.index[-1]
        
        # 统计分析
        one_year_ago = current_date - pd.DateOffset(years=1)
        data_in_last_year = series[series.index >= one_year_ago]
        percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
        
        # 变化率计算（基点）
        change_1w_bp = (current - series.iloc[-5]) * 100 if len(series) > 5 else 0
        change_1m_bp = (current - series.iloc[-21]) * 100 if len(series) > 21 else 0
        change_1m = self._calculate_change(series, -21)
        
        # 信用风险制度分析
        if current > 10.0:
            regime = "信用危机制度"
            risk_assessment = "系统性信用风险爆发，经济衰退概率极高"
            market_implication = "高收益债大面积违约，流动性枯竭"
        elif current > 7.0:
            regime = "高信用压力制度"
            risk_assessment = "信用环境严重恶化，违约率快速上升"
            market_implication = "信用收缩加剧，融资成本飙升"
        elif current > 5.0:
            regime = "信用收紧制度"
            risk_assessment = "信用风险溢价上升，市场风险偏好下降"
            market_implication = "企业融资难度增加，投资活动放缓"
        elif current > 3.0:
            regime = "正常信用制度"
            risk_assessment = "信用环境基本健康，风险可控"
            market_implication = "企业融资环境正常，经济增长稳定"
        else:
            regime = "宽松信用制度"
            risk_assessment = "信用环境过度宽松，可能积累风险"
            market_implication = "资本追逐收益，资产泡沫风险上升"
    
        # 趋势判断
        if change_1m_bp > 100:
            trend = "快速扩大"
            trend_implication = "信用风险快速恶化，市场恐慌蔓延"
        elif change_1m_bp > 50:
            trend = "温和扩大"
            trend_implication = "信用担忧上升，风险溢价增加"
        elif change_1m_bp < -100:
            trend = "快速收窄"
            trend_implication = "信用环境快速改善，风险偏好回升"
        elif change_1m_bp < -50:
            trend = "温和收窄"
            trend_implication = "信用条件逐步改善，市场信心恢复"
        else:
            trend = "基本稳定"
            trend_implication = "信用环境保持稳定"
    
        return {
            "indicator": "美国高收益债信用利差",
            "current_value": round(float(current), 2),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1w_bp": round(change_1w_bp, 1),
                "change_1m_bp": round(change_1m_bp, 1),
                "change_1m": round(change_1m, 1),
                "long_term_average": 4.5
            },
            "regime": regime,
            "trend": trend,
            "risk_assessment": risk_assessment,
            "market_implication": market_implication,
            "trend_implication": trend_implication,
            "thresholds": {
                "crisis": 10.0,
                "high_stress": 7.0,
                "tightening": 5.0,
                "normal": 3.0
            }
        }

    def analyze_nfci(self):
         """分析芝加哥联储国家金融状况指数(NFCI)"""
         if 'NFCI' not in self.data.columns:
             return {"status": "unavailable", "message": "NFCI数据不可用"}
         
         series = self.data['NFCI'].dropna()
         if len(series) < 2:
             return {"status": "insufficient_data"}
             
         current = series.iloc[-1]
         current_date = series.index[-1]
         
         # 统计分析
         one_year_ago = current_date - pd.DateOffset(years=1)
         data_in_last_year = series[series.index >= one_year_ago]
         percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
         
         # 变化率计算
         change_1w = self._calculate_change(series, -5)
         change_1m = self._calculate_change(series, -21)
         change_3m = self._calculate_change(series, -63)
         
         # 金融条件制度分析
         if current > 1.0:
             regime = "严重紧缩制度"
             financial_condition = "极度紧缩"
             risk_assessment = "系统性金融风险显著，经济衰退概率极高"
             policy_transmission = "过度收紧，传导机制可能失效"
         elif current > 0.5:
             regime = "紧缩制度"
             financial_condition = "明显紧缩"
             risk_assessment = "金融摩擦增强，经济下行压力加大"
             policy_transmission = "收紧有效，但需防范过度收缩"
         elif current > 0:
             regime = "轻度紧缩制度"
             financial_condition = "轻度紧缩"
             risk_assessment = "金融条件略偏紧，经济增长面临温和阻力"
             policy_transmission = "政策收紧效果显现"
         elif current > -0.5:
             regime = "接近均衡制度"
             financial_condition = "基本均衡"
             risk_assessment = "金融条件接近历史平均，经济运行稳定"
             policy_transmission = "传导机制运行正常"
         elif current > -1.0:
             regime = "宽松制度"
             financial_condition = "明显宽松"
             risk_assessment = "金融条件支撑增长，但需警惕风险积累"
             policy_transmission = "宽松政策传导有效"
         else:
             regime = "极度宽松制度"
             financial_condition = "极度宽松"
             risk_assessment = "金融条件异常宽松，资产泡沫风险上升"
             policy_transmission = "可能存在过度刺激"
    
         # 趋势判断
         if change_3m > 50:
             trend = "快速恶化"
             macro_outlook = "经济前景显著恶化，衰退风险上升"
         elif change_3m > 20:
             trend = "温和恶化"
             macro_outlook = "经济增长动能减弱"
         elif change_3m < -50:
             trend = "快速改善"
             macro_outlook = "金融支持力度增强，经济复苏加速"
         elif change_3m < -20:
             trend = "温和改善"
             macro_outlook = "经济环境逐步好转"
         else:
             trend = "基本稳定"
             macro_outlook = "金融条件保持稳定"
         
         # 宏观经济领先指标
         gdp_signal = "负面" if current > 0.3 else "正面" if current < -0.3 else "中性"
         employment_signal = "就业压力" if current > 0.2 else "就业支撑" if current < -0.2 else "就业稳定"
         inflation_signal = "通缩风险" if current > 0.8 else "通胀压力" if current < -0.8 else "价格稳定"
         
         return {
             "indicator": "芝加哥联储国家金融状况指数",
             "current_value": round(float(current), 3),
             "date": series.index[-1].strftime('%Y-%m-%d'),
             "statistics": {
                 "percentile_1y": round(percentile_1y, 1),
                 "change_1w": round(change_1w, 1),
                 "change_1m": round(change_1m, 1),
                 "change_3m": round(change_3m, 1),
                 "historical_mean": 0.0
             },
             "regime": regime,
             "financial_condition": financial_condition,
             "trend": trend,
             "risk_assessment": risk_assessment,
             "policy_transmission": policy_transmission,
             "macro_outlook": macro_outlook,
             "leading_indicators": {
                 "gdp_signal": gdp_signal,
                 "employment_signal": employment_signal,
                 "inflation_signal": inflation_signal
             },
             "thresholds": {
                 "severe_tightening": 1.0,
                 "tightening": 0.5,
                 "mild_tightening": 0,
                 "accommodative": -0.5,
                 "very_accommodative": -1.0
             }
         }
#计算框架
    def analyze_sofr(self):
        """分析SOFR有担保隔夜融资利率"""
        if 'SOFR' not in self.data.columns:
            return {"status": "unavailable", "message": "SOFR数据不可用"}
        
        series = self.data['SOFR'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_date = series.index[-1]
        
        # 直接使用主数据中的IORB进行利差分析
        sofr_iorb_spread = None
        if 'IORB' in self.data.columns:
             iorb_series = self.data['IORB'].dropna()
             if len(iorb_series) > 0:
                 iorb_current = iorb_series.iloc[-1]
                 sofr_iorb_spread = (current - iorb_current) * 100  # 转换为基点
        
        # 统计分析（修正：使用绝对数值变化而非百分比变化）
        change_1d_bp = (current - series.iloc[-2]) * 100 if len(series) > 1 else 0  # 基点变化
        change_1w_bp = (current - series.iloc[-5]) * 100 if len(series) > 5 else 0  # 基点变化
        change_1m_bp = (current - series.iloc[-21]) * 100 if len(series) > 21 else 0  # 基点变化
        # SOFR波动性分析（5日滚动标准差）
        volatility_5d = (series.diff().tail(5).std() * 100) if len(series) > 5 else 0  # 基点
        # SOFR水平制度分析
        if current > 6.0:
            regime = "极度紧缩制度"
            liquidity_assessment = "银行系统流动性极度紧张，融资成本异常高企"
            market_implication = "货币市场功能严重受损，系统性风险显著"
            policy_signal = "央行可能需要紧急干预"
        elif current > 4.5:
            regime = "紧缩制度"
            liquidity_assessment = "银行短期融资成本明显上升，流动性偏紧"
            market_implication = "货币政策收紧效果显现，银行放贷意愿收缩"
            policy_signal = "紧缩政策传导有效"
        elif current > 2.0:
            regime = "中性偏紧制度"
            liquidity_assessment = "银行融资成本处于中性偏高水平"
            market_implication = "货币市场运行正常，政策立场中性偏紧"
            policy_signal = "政策传导机制运行良好"
        elif current > 0.5:
            regime = "宽松制度"
            liquidity_assessment = "银行系统流动性充裕，融资成本较低"
            market_implication = "宽松货币政策环境，支持信贷投放"
            policy_signal = "宽松政策有效传导至银行体系"
        else:
            regime = "极度宽松制度"
            liquidity_assessment = "银行融资成本接近零，流动性极度充裕"
            market_implication = "零利率政策环境，货币政策空间有限"
            policy_signal = "接近货币政策下限"
      
        # SOFR-IORB利差分析
        spread_analysis = "不可用"
        transmission_efficiency = "无法评估"
        if sofr_iorb_spread is not None:
            if abs(sofr_iorb_spread) < 5:
                spread_analysis = f"利差{sofr_iorb_spread:+.1f}bp，政策传导高效"
                transmission_efficiency = "高效"
            elif abs(sofr_iorb_spread) < 15:
                spread_analysis = f"利差{sofr_iorb_spread:+.1f}bp，传导效率正常"
                transmission_efficiency = "正常"
            else:
                spread_analysis = f"利差{sofr_iorb_spread:+.1f}bp，传导可能受阻"
                transmission_efficiency = "受阻"
        
         # 波动性分析
        if volatility_5d > 20:
             volatility_regime = "高波动"
             stability_assessment = "货币市场压力显著，流动性分布不均"
        elif volatility_5d > 10:
             volatility_regime = "中等波动"
             stability_assessment = "市场存在一定波动，需要关注流动性状况"
        elif volatility_5d > 5:
             volatility_regime = "低波动"
             stability_assessment = "市场运行相对稳定"
        else:
             volatility_regime = "极低波动"
             stability_assessment = "市场流动性分布均匀，运行平稳"
    
        # 趋势判断（基于基点变化）
        if change_1w_bp > 25:
            trend = "快速上升"
            trend_implication = "银行融资成本快速上升，流动性收紧"
        elif change_1w_bp > 10:
            trend = "温和上升"
            trend_implication = "融资成本逐步上升"
        elif change_1w_bp < -25:
            trend = "快速下降"
            trend_implication = "银行融资成本快速下降，流动性改善"
        elif change_1w_bp < -10:
            trend = "温和下降"
            trend_implication = "融资成本逐步下降"
        else:
            trend = "基本稳定"
            trend_implication = "融资成本保持稳定"
       
        return {
             "indicator": "SOFR有担保隔夜融资利率",
             "current_value": round(float(current), 3),
             "date": series.index[-1].strftime('%Y-%m-%d'),
             "statistics": {
                 "change_1d_bp": round(change_1d_bp, 1),
                 "change_1w_bp": round(change_1w_bp, 1),
                 "change_1m_bp": round(change_1m_bp, 1),
                 "volatility_5d_bp": round(volatility_5d, 1),
                 "sofr_iorb_spread_bp": round(sofr_iorb_spread, 1) if sofr_iorb_spread is not None else "N/A"
             },
             "regime": regime,
             "trend": trend,
             "liquidity_assessment": liquidity_assessment,
             "market_implication": market_implication,
             "trend_implication": trend_implication,
             "policy_signal": policy_signal,
             "transmission_efficiency": transmission_efficiency,
             "spread_analysis": spread_analysis,
             "volatility_regime": volatility_regime,
             "stability_assessment": stability_assessment,
             "thresholds": {
                 "extreme_tight": 6.0,
                 "tight": 4.5,
                 "neutral_tight": 2.0,
                 "accommodative": 0.5
             }
         }


    def analyze_wti_crude(self):
        """分析WTI原油期货价格"""
        if 'CL=F' not in self.data.columns:
            return {"status": "unavailable", "message": "WTI原油数据不可用"}
        
        series = self.data['CL=F'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        
        # 变化率计算
        change_1w = self._calculate_change(series, -5)
        change_1m = self._calculate_change(series, -21)
        
        # 价格制度分析
        if current > 100:
            regime = "危机价格制度"
            inflation_impact = "通胀压力极大，央行面临政策两难"
            growth_impact = "石油净进口国经济增长显著承压"
        elif current > 80:
            regime = "高油价制度"
            inflation_impact = "通胀预期上升，货币政策收紧压力"
            growth_impact = "能源成本上升抑制消费和投资"
        elif current >= 60:
            regime = "均衡价格制度"
            inflation_impact = "对通胀影响相对中性"
            growth_impact = "经济增长环境基本健康"
        else:
            regime = "低油价制度"
            inflation_impact = "通缩风险上升，支持宽松货币政策"
            growth_impact = "降低生产成本，刺激消费需求"
    
        # 趋势判断
        if change_1m > 15:
            trend = "强势上涨"
            policy_pressure = "央行通胀担忧加剧"
        elif change_1m > 5:
            trend = "温和上涨"
            policy_pressure = "通胀预期温和上升"
        elif change_1m < -15:
            trend = "大幅下跌"
            policy_pressure = "通缩风险需要关注"
        elif change_1m < -5:
            trend = "温和下跌"
            policy_pressure = "通胀压力有所缓解"
        else:
            trend = "区间波动"
            policy_pressure = "价格影响相对中性"
    
        return {
            "indicator": "WTI原油期货",
            "current_value": round(float(current), 2),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "change_1w": round(change_1w, 1),
                "change_1m": round(change_1m, 1)
            },
            "regime": regime,
            "trend": trend,
            "inflation_impact": inflation_impact,
            "growth_impact": growth_impact,
            "policy_pressure": policy_pressure,
            "thresholds": {
                "crisis": 100,
                "high": 80,
                "equilibrium": 60
            }
        }
       
#黄金价格
    def analyze_gold_futures(self):
        """分析黄金期货(GC=F)"""
        if 'GC=F' not in self.data.columns:
            return {"status": "unavailable", "message": "黄金期货数据不可用"}
        
        series = self.data['GC=F'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_date = series.index[-1]
        
        # 统计分析
        one_year_ago = current_date - pd.DateOffset(years=1)
        data_in_last_year = series[series.index >= one_year_ago]
        percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
        
        # 变化率计算
        change_1w = self._calculate_change(series, -5)
        change_1m = self._calculate_change(series, -21)
        change_3m = self._calculate_change(series, -63)
        
        # 黄金价格制度分析
        if current > 2400:
            regime = "历史高位制度"
            market_sentiment = "极度避险"
            macro_signal = "系统性风险担忧或通胀失控预期"
        elif current > 2000:
            regime = "高位制度"
            market_sentiment = "强避险需求"
            macro_signal = "地缘政治紧张或货币政策不确定性"
        elif current > 1800:
            regime = "中高位制度"
            market_sentiment = "温和避险"
            macro_signal = "通胀预期上升或美元疲软"
        elif current > 1500:
            regime = "中性制度"
            market_sentiment = "平衡配置"
            macro_signal = "宏观环境相对稳定"
        else:
            regime = "低位制度"
            market_sentiment = "风险偏好"
            macro_signal = "经济增长强劲或美元强势"
    
        # 避险功能评估
        if change_1m > 10:
            hedge_function = "强避险"
            risk_implication = "市场风险事件频发，资金大量流入避险资产"
        elif change_1m > 5:
            hedge_function = "温和避险"
            risk_implication = "市场存在不确定性，黄金发挥保值功能"
        elif change_1m < -10:
            hedge_function = "风险偏好"
            risk_implication = "市场风险偏好回升，资金流出避险资产"
        elif change_1m < -5:
            hedge_function = "温和回调"
            risk_implication = "风险情绪改善，黄金避险需求下降"
        else:
            hedge_function = "中性"
            risk_implication = "避险需求与风险偏好基本平衡"
    
        # 通胀对冲评估
        if change_3m > 15:
            inflation_hedge = "强通胀对冲"
            monetary_implication = "通胀预期显著上升或货币政策过度宽松"
        elif change_3m > 8:
            inflation_hedge = "通胀对冲"
            monetary_implication = "通胀担忧推升黄金配置需求"
        elif change_3m < -15:
            inflation_hedge = "通缩预期"
            monetary_implication = "通胀预期回落或货币政策收紧"
        else:
            inflation_hedge = "中性"
            monetary_implication = "通胀预期相对稳定"
    
        # 趋势判断
        if change_1w > 3:
            trend = "强势上涨"
            trend_driver = "避险情绪急剧升温或突发事件冲击"
        elif change_1w > 1:
            trend = "温和上涨"
            trend_driver = "支撑因素增强"
        elif change_1w < -3:
            trend = "快速下跌"
            trend_driver = "风险偏好回升或美元走强"
        elif change_1w < -1:
            trend = "温和下跌"
            trend_driver = "避险需求减弱"
        else:
            trend = "区间震荡"
            trend_driver = "多空因素相对平衡"
    
        return {
            "indicator": "黄金期货",
            "current_value": round(float(current), 2),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1w": round(change_1w, 1),
                "change_1m": round(change_1m, 1),
                "change_3m": round(change_3m, 1)
            },
            "regime": regime,
            "trend": trend,
            "market_sentiment": market_sentiment,
            "macro_signal": macro_signal,
            "hedge_function": hedge_function,
            "inflation_hedge": inflation_hedge,
            "risk_implication": risk_implication,
            "monetary_implication": monetary_implication,
            "trend_driver": trend_driver,
            "thresholds": {
                "historical_high": 2400,
                "high": 2000,
                "medium_high": 1800,
                "neutral": 1500
            }
        }
#铜价
    def analyze_copper_futures(self):
        """分析铜期货(HG=F) - 工业金属之王"""
        if 'HG=F' not in self.data.columns:
            return {"status": "unavailable", "message": "铜期货数据不可用"}
        
        series = self.data['HG=F'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_date = series.index[-1]
        
        # 统计分析
        one_year_ago = current_date - pd.DateOffset(years=1)
        data_in_last_year = series[series.index >= one_year_ago]
        percentile_1y = (data_in_last_year <= current).mean() * 100 if len(data_in_last_year) > 0 else 50
        
        # 变化率计算
        change_1m = self._calculate_change(series, -21)
        change_3m = self._calculate_change(series, -63)
        
        # 铜价制度分析（铜博士的经济周期指示）
        if current > 4.5:
            regime = "繁荣制度"
            economic_signal = "经济强劲扩张"
            cycle_phase = "繁荣期"
            demand_outlook = "工业需求旺盛，基建投资活跃"
        elif current > 3.8:
            regime = "温和扩张制度"
            economic_signal = "经济稳健增长"
            cycle_phase = "扩张期"
            demand_outlook = "制造业需求稳定，经济活动正常"
        elif current > 3.0:
            regime = "中性制度"
            economic_signal = "经济增长温和"
            cycle_phase = "平稳期"
            demand_outlook = "工业需求平衡，经济动能适中"
        elif current > 2.5:
            regime = "收缩制度"
            economic_signal = "经济增长放缓"
            cycle_phase = "下行期"
            demand_outlook = "制造业需求疲软，投资活动减少"
        else:
            regime = "衰退制度"
            economic_signal = "经济深度收缩"
            cycle_phase = "衰退期"
            demand_outlook = "工业需求萎缩，产能大量闲置"
    
        # 供需平衡分析
        if change_1m > 8:
            supply_demand = "需求激增"
            market_tension = "供应紧张，价格快速上涨"
        elif change_1m > 3:
            supply_demand = "需求偏强"
            market_tension = "供需偏紧，价格上涨压力"
        elif change_1m < -8:
            supply_demand = "需求萎缩"
            market_tension = "供应过剩，价格下跌压力"
        elif change_1m < -3:
            supply_demand = "需求偏弱"
            market_tension = "供需偏松，价格承压"
        else:
            supply_demand = "供需平衡"
            market_tension = "市场相对均衡"
        
        # 通胀/增长预期
        if change_3m > 15:
            inflation_growth = "强通胀+强增长"
            policy_implication = "经济过热风险，央行可能收紧政策"
        elif change_3m > 5:
            inflation_growth = "温和通胀+稳增长"
            policy_implication = "经济健康扩张，政策保持稳定"
        elif change_3m < -15:
            inflation_growth = "通缩+衰退风险"
            policy_implication = "经济衰退担忧，需要政策刺激"
        elif change_3m < -5:
            inflation_growth = "增长放缓"
            policy_implication = "经济下行压力，政策转向宽松"
        else:
            inflation_growth = "稳定预期"
            policy_implication = "经济运行平稳"
    
        return {
            "indicator": "铜期货(工业金属之王)",
            "current_value": round(float(current), 3),
            "date": series.index[-1].strftime('%Y-%m-%d'),
            "statistics": {
                "percentile_1y": round(percentile_1y, 1),
                "change_1m": round(change_1m, 1),
                "change_3m": round(change_3m, 1)
            },
            "regime": regime,
            "economic_signal": economic_signal,
            "cycle_phase": cycle_phase,
            "demand_outlook": demand_outlook,
            "supply_demand": supply_demand,
            "market_tension": market_tension,
            "inflation_growth": inflation_growth,
            "policy_implication": policy_implication,
            "thresholds": {
                "boom": 4.5,
                "expansion": 3.8,
                "neutral": 3.0,
                "contraction": 2.5
            }
        }

#大宗商品指数
    def analyze_dbc_etf(self):
        """分析大宗商品指数ETF(DBC) - 综合商品景气度"""
        if 'DBC' not in self.data.columns:
            return {"status": "unavailable", "message": "DBC ETF数据不可用"}
        
        series = self.data['DBC'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1m = self._calculate_change(series, -21)
        change_3m = self._calculate_change(series, -63)
        
        # DBC价格制度分析
        if current > 25:
            regime = "商品超级周期"
            macro_signal = "全球通胀+增长强劲"
            investment_implication = "商品配置价值显著"
        elif current > 20:
            regime = "商品牛市"
            macro_signal = "通胀预期+需求旺盛"
            investment_implication = "商品投资机会良好"
        elif current > 15:
            regime = "商品中性"
            macro_signal = "宏观环境平稳"
            investment_implication = "商品配置适中"
        else:
            regime = "商品熊市"
            macro_signal = "通缩风险+需求疲软"
            investment_implication = "商品投资谨慎"
        
        return {
            "indicator": "大宗商品指数ETF",
            "current_value": round(float(current), 2),
            "statistics": {"change_1m": round(change_1m, 1), "change_3m": round(change_3m, 1)},
            "regime": regime,
            "macro_signal": macro_signal,
            "investment_implication": investment_implication
        }
#小麦期货
    def analyze_wheat(self):
         """分析小麦期货(ZW=F) - 粮食安全指标"""
         if 'ZW=F' not in self.data.columns:
             return {"status": "unavailable", "message": "小麦期货数据不可用"}
         
         series = self.data['ZW=F'].dropna()
         if len(series) < 2:
             return {"status": "insufficient_data"}
             
         current = series.iloc[-1]
         change_1m = self._calculate_change(series, -21)
         change_3m = self._calculate_change(series, -63)
         
         # 小麦价格制度分析（美分/蒲式耳）
         if current > 900:
             regime = "粮食危机制度"
             food_security = "全球粮食安全风险"
             geopolitical = "地缘政治或气候冲击"
         elif current > 700:
             regime = "高价制度"
             food_security = "粮食价格压力"
             geopolitical = "供应链受扰"
         elif current > 500:
             regime = "正常制度"
             food_security = "粮食供应稳定"
             geopolitical = "市场运行正常"
         else:
             regime = "低价制度"
             food_security = "供应充裕"
             geopolitical = "丰收或需求疲软"
         
         return {
             "indicator": "小麦期货",
             "current_value": round(float(current), 2),
             "statistics": {"change_1m": round(change_1m, 1), "change_3m": round(change_3m, 1)},
             "regime": regime,
             "food_security": food_security,
             "geopolitical": geopolitical
         }

    def analyze_corn(self):
         """分析玉米期货(ZC=F) - 饲料与燃料双重需求"""
         if 'ZC=F' not in self.data.columns:
             return {"status": "unavailable", "message": "玉米期货数据不可用"}
         
         series = self.data['ZC=F'].dropna()
         if len(series) < 2:
             return {"status": "insufficient_data"}
             
         current = series.iloc[-1]
         change_1m = self._calculate_change(series, -21)
         change_3m = self._calculate_change(series, -63)
         
         # 玉米价格制度分析（美分/蒲式耳）
         if current > 700:
             regime = "供应紧张制度"
             dual_demand = "饲料+燃料需求激增"
             inflation_risk = "食品和能源通胀双重压力"
         elif current > 550:
             regime = "偏紧制度"
             dual_demand = "需求偏强"
             inflation_risk = "通胀压力温和上升"
         elif current > 400:
             regime = "均衡制度"
             dual_demand = "供需基本平衡"
             inflation_risk = "价格稳定"
         else:
             regime = "供应充裕制度"
             dual_demand = "需求疲软"
             inflation_risk = "通缩压力"
         
         return {
             "indicator": "玉米期货",
             "current_value": round(float(current), 2),
             "statistics": {"change_1m": round(change_1m, 1), "change_3m": round(change_3m, 1)},
             "regime": regime,
             "dual_demand": dual_demand,
             "inflation_risk": inflation_risk
         }

    def analyze_soybean(self):
         """分析大豆期货(ZS=F) - 农业通胀先行指标"""
         if 'ZS=F' not in self.data.columns:
             return {"status": "unavailable", "message": "大豆期货数据不可用"}
         
         series = self.data['ZS=F'].dropna()
         if len(series) < 2:
             return {"status": "insufficient_data"}
             
         current = series.iloc[-1]
         change_1m = self._calculate_change(series, -21)
         change_3m = self._calculate_change(series, -63)
         
         # 大豆价格制度分析（美分/蒲式耳）
         if current > 1600:
             regime = "历史高位制度"
             food_inflation = "食品通胀压力极大"
             trade_impact = "贸易成本飙升，消费者负担沉重"
         elif current > 1300:
             regime = "高价制度"
             food_inflation = "食品通胀压力显著"
             trade_impact = "农产品成本上升，贸易活跃"
         elif current > 1000:
             regime = "正常制度"
             food_inflation = "食品价格稳定"
             trade_impact = "农业贸易正常，供需平衡"
         else:
             regime = "低价制度"
             food_inflation = "食品通缩压力"
             trade_impact = "农民收入承压，产能可能调整"
         
         return {
             "indicator": "大豆期货",
             "current_value": round(float(current), 2),
             "statistics": {"change_1m": round(change_1m, 1), "change_3m": round(change_3m, 1)},
             "regime": regime,
             "food_inflation": food_inflation,
             "trade_impact": trade_impact
         }
         
    def analyze_natural_gas(self):
          """分析天然气期货(NG=F) - 清洁能源转型指标"""
          if 'NG=F' not in self.data.columns:
              return {"status": "unavailable", "message": "天然气期货数据不可用"}
          
          series = self.data['NG=F'].dropna()
          if len(series) < 2:
              return {"status": "insufficient_data"}
              
          current = series.iloc[-1]
          change_1m = self._calculate_change(series, -21)
          change_3m = self._calculate_change(series, -63)
          
          # 天然气价格制度分析
          if current > 6.0:
              regime = "供应危机制度"
              energy_signal = "能源安全风险"
              economic_impact = "通胀压力显著，消费者负担加重"
          elif current > 4.0:
              regime = "高价制度"
              energy_signal = "供需偏紧"
              economic_impact = "能源成本上升，制造业承压"
          elif current > 2.5:
              regime = "正常制度"
              energy_signal = "供需平衡"
              economic_impact = "能源成本适中，经济运行稳定"
          else:
              regime = "低价制度"
              energy_signal = "供应充裕"
              economic_impact = "能源成本优势，支撑经济增长"
          
          # 季节性和地缘分析
          if change_1m > 15:
              market_driver = "供应中断或极端天气"
          elif change_1m < -15:
              market_driver = "供应增加或需求疲软"
          else:
              market_driver = "基本面稳定"
          
          return {
              "indicator": "天然气期货",
              "current_value": round(float(current), 3),
              "statistics": {"change_1m": round(change_1m, 1), "change_3m": round(change_3m, 1)},
              "regime": regime,
              "energy_signal": energy_signal,
              "economic_impact": economic_impact,
              "market_driver": market_driver
          }

    def analyze_jpy_usd(self):
        """分析日元/美元汇率 - 全球避险货币"""
        if 'JPY=X' not in self.data.columns:
            return {"status": "unavailable", "message": "日元汇率数据不可用"}
        
        series = self.data['JPY=X'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1w = self._calculate_change(series, -5)
        change_1m = self._calculate_change(series, -21)
        
        # 注意：JPY=X表示1美元兑多少日元，数值越高表示日元越弱
        if current > 155:
            regime = "日元极度疲软"
            monetary_policy = "BoJ可能干预汇市"
            global_impact = "日本通胀压力加剧，全球贸易成本上升"
        elif current > 145:
            regime = "日元疲软"
            monetary_policy = "货币政策分化显著"
            global_impact = "日本出口竞争力增强，进口通胀压力"
        elif current > 130:
            regime = "日元中性偏弱"
            monetary_policy = "政策立场相对宽松"
            global_impact = "汇率波动温和"
        elif current > 110:
            regime = "日元中性"
            monetary_policy = "货币政策基本均衡"
            global_impact = "双边贸易相对均衡"
        else:
            regime = "日元强势"
            monetary_policy = "避险需求推升日元"
            global_impact = "全球风险偏好下降，避险情绪升温"
        
        # 避险功能分析
        if change_1w < -2:  # 日元快速升值
            safe_haven = "强避险需求"
            risk_sentiment = "全球风险情绪恶化"
        elif change_1w < -1:
            safe_haven = "温和避险"
            risk_sentiment = "市场不确定性增加"
        elif change_1w > 2:  # 日元快速贬值
            safe_haven = "风险偏好回升"
            risk_sentiment = "全球风险情绪改善"
        else:
            safe_haven = "避险需求平衡"
            risk_sentiment = "市场情绪相对稳定"
        
        return {
            "indicator": "日元/美元",
            "current_value": round(float(current), 2),
            "statistics": {"change_1w": round(change_1w, 1), "change_1m": round(change_1m, 1)},
            "regime": regime,
            "monetary_policy": monetary_policy,
            "global_impact": global_impact,
            "safe_haven": safe_haven,
            "risk_sentiment": risk_sentiment
        }


    def analyze_eur_usd(self):
        """分析欧元/美元汇率 - 全球第二储备货币"""
        if 'EUR=X' not in self.data.columns:
            return {"status": "unavailable", "message": "欧元汇率数据不可用"}
        
        series = self.data['EUR=X'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1w = self._calculate_change(series, -5)
        change_1m = self._calculate_change(series, -21)
        
        # EUR=X表示1欧元兑多少美元
        if current > 1.15:
            regime = "欧元强势"
            ecb_policy = "货币政策收紧预期"
            eu_economy = "欧洲经济增长强劲"
        elif current > 1.05:
            regime = "欧元中性偏强"
            ecb_policy = "政策立场相对中性"
            eu_economy = "欧洲经济稳健增长"
        elif current > 0.95:
            regime = "欧元中性偏弱"
            ecb_policy = "货币政策相对宽松"
            eu_economy = "欧洲经济增长温和"
        else:
            regime = "欧元疲软"
            ecb_policy = "极度宽松货币政策"
            eu_economy = "欧洲经济面临压力"
        
        # 政策分化分析
        if change_1m > 3:
            policy_divergence = "欧美政策分化缩小"
            trade_impact = "欧洲出口竞争力下降"
        elif change_1m < -3:
            policy_divergence = "欧美政策分化加大"
            trade_impact = "欧洲出口竞争力增强"
        else:
            policy_divergence = "政策分化相对稳定"
            trade_impact = "贸易影响中性"
        
        return {
            "indicator": "欧元/美元",
            "current_value": round(float(current), 4),
            "statistics": {"change_1w": round(change_1w, 1), "change_1m": round(change_1m, 1)},
            "regime": regime,
            "ecb_policy": ecb_policy,
            "eu_economy": eu_economy,
            "policy_divergence": policy_divergence,
            "trade_impact": trade_impact
        }

    def analyze_cny_usd(self):
        """分析人民币/美元汇率 - 新兴市场领头羊"""
        if 'CNY=X' not in self.data.columns:
            return {"status": "unavailable", "message": "人民币汇率数据不可用"}
        
        series = self.data['CNY=X'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1w = self._calculate_change(series, -5)
        change_1m = self._calculate_change(series, -21)
        
        # CNY=X表示1美元兑多少人民币，数值越高表示人民币越弱
        if current > 7.3:
            regime = "人民币显著承压"
            pboc_policy = "央行可能加强汇率管理"
            china_economy = "经济增长面临挑战"
        elif current > 7.0:
            regime = "人民币中性偏弱"
            pboc_policy = "汇率政策保持灵活"
            china_economy = "经济增长稳中有忧"
        elif current > 6.5:
            regime = "人民币基本稳定"
            pboc_policy = "政策工具充足"
            china_economy = "经济运行在合理区间"
        else:
            regime = "人民币相对强势"
            pboc_policy = "汇率升值压力管理"
            china_economy = "经济增长动能强劲"
        
        # 贸易与资本流动影响
        if change_1m > 2:
            capital_flow = "资本流出压力加大"
            trade_competitiveness = "出口竞争力增强"
        elif change_1m < -2:
            capital_flow = "资本流入增加"
            trade_competitiveness = "进口成本下降"
        else:
            capital_flow = "资本流动相对平衡"
            trade_competitiveness = "贸易影响中性"
    
        return {
            "indicator": "人民币/美元",
            "current_value": round(float(current), 4),
            "statistics": {"change_1w": round(change_1w, 1), "change_1m": round(change_1m, 1)},
            "regime": regime,
            "pboc_policy": pboc_policy,
            "china_economy": china_economy,
            "capital_flow": capital_flow,
            "trade_competitiveness": trade_competitiveness
        }

    def analyze_btc_usd(self):
        """分析比特币/美元 - 数字黄金"""
        if 'BTC-USD' not in self.data.columns:
            return {"status": "unavailable", "message": "比特币数据不可用"}
        
        series = self.data['BTC-USD'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1w = self._calculate_change(series, -5)
        change_1m = self._calculate_change(series, -21)
        
        # 比特币价格制度分析
        if current > 80000:
            regime = "历史新高区域"
            adoption_signal = "主流机构大规模采纳"
            risk_appetite = "极度投机情绪"
        elif current > 60000:
            regime = "牛市高位"
            adoption_signal = "机构采纳加速"
            risk_appetite = "强风险偏好"
        elif current > 40000:
            regime = "中高位震荡"
            adoption_signal = "采纳稳步推进"
            risk_appetite = "温和风险偏好"
        elif current > 20000:
            regime = "中性区间"
            adoption_signal = "基础建设发展"
            risk_appetite = "谨慎乐观"
        else:
            regime = "熊市低位"
            adoption_signal = "监管担忧或技术问题"
            risk_appetite = "风险厌恶"
    
        # 波动性分析
        abs_change = abs(change_1w)
        if abs_change > 20:
            volatility = "极高波动"
            market_maturity = "市场投机性极强"
        elif abs_change > 10:
            volatility = "高波动"
            market_maturity = "市场仍不成熟"
        elif abs_change > 5:
            volatility = "中等波动"
            market_maturity = "市场逐步成熟"
        else:
            volatility = "相对稳定"
            market_maturity = "市场趋于成熟"
        
        return {
            "indicator": "比特币",
            "current_value": f"${current:,.0f}",
            "statistics": {"change_1w": round(change_1w, 1), "change_1m": round(change_1m, 1)},
            "regime": regime,
            "adoption_signal": adoption_signal,
            "risk_appetite": risk_appetite,
            "volatility": volatility,
            "market_maturity": market_maturity
        }

    def analyze_eth_usd(self):
        """分析以太坊/美元 - 智能合约平台"""
        if 'ETH-USD' not in self.data.columns:
            return {"status": "unavailable", "message": "以太坊数据不可用"}
        
        series = self.data['ETH-USD'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1w = self._calculate_change(series, -5)
        change_1m = self._calculate_change(series, -21)
        
        if current > 5000:
            regime = "历史高位"
            defi_signal = "DeFi生态爆发式增长"
        elif current > 3000:
            regime = "牛市区间"
            defi_signal = "智能合约采纳加速"
        elif current > 2000:
            regime = "中高位"
            defi_signal = "生态稳步发展"
        elif current > 1000:
            regime = "中性区间"
            defi_signal = "基础设施建设期"
        else:
            regime = "熊市区间"
            defi_signal = "生态发展遇阻"
        
        return {
            "indicator": "以太坊",
            "current_value": f"${current:,.0f}",
            "statistics": {"change_1w": round(change_1w, 1), "change_1m": round(change_1m, 1)},
            "regime": regime,
            "defi_signal": defi_signal
        }

    def analyze_sol_usd(self):
        """分析Solana/美元 - 高性能区块链"""
        if 'SOL-USD' not in self.data.columns:
            return {"status": "unavailable", "message": "Solana数据不可用"}
        
        series = self.data['SOL-USD'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1w = self._calculate_change(series, -5)
        change_1m = self._calculate_change(series, -21)
        
        if current > 200:
            regime = "投机泡沫"
            ecosystem_health = "生态过热"
        elif current > 100:
            regime = "强势上涨"
            ecosystem_health = "生态快速发展"
        elif current > 50:
            regime = "健康增长"
            ecosystem_health = "生态稳步扩张"
        elif current > 20:
            regime = "温和增长"
            ecosystem_health = "基础建设期"
        else:
            regime = "低位整理"
            ecosystem_health = "生态发展缓慢"
        
        return {
            "indicator": "Solana",
            "current_value": f"${current:,.2f}",
            "statistics": {"change_1w": round(change_1w, 1), "change_1m": round(change_1m, 1)},
            "regime": regime,
            "ecosystem_health": ecosystem_health
        }




#经济不确定性
    

    def analyze_world_epu(self):
        """分析世界经济政策不确定性指数 - 简化版"""
        if 'WLEMUINDXD' not in self.data.columns:
            return {"status": "unavailable", "message": "世界经济政策不确定性指数数据不可用"}
        
        series = self.data['WLEMUINDXD'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1m = self._calculate_change(series, -21)
        
        # 简化制度分析
        if current > 300:
            regime = "极高不确定性"
            risk_level = "系统性风险显著"
        elif current > 200:
            regime = "高不确定性"
            risk_level = "政策风险需关注"
        elif current > 150:
            regime = "中等不确定性"
            risk_level = "风险适中"
        else:
            regime = "低不确定性"
            risk_level = "政策风险较低"
        
        return {
            "indicator": "世界经济政策不确定性",
            "current_value": round(float(current), 1),
            "statistics": {"change_1m": round(change_1m, 1)},
            "regime": regime,
            "risk_level": risk_level
        }

    def analyze_us_epu(self):
        """分析美国经济政策不确定性指数 - 简化版"""
        if 'USEPUINDXD' not in self.data.columns:
            return {"status": "unavailable", "message": "美国经济政策不确定性指数数据不可用"}
        
        series = self.data['USEPUINDXD'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_1m = self._calculate_change(series, -21)
        
        # 简化制度分析
        if current > 400:
            regime = "政治危机级别"
            impact = "强烈全球溢出"
        elif current > 250:
            regime = "高政策不确定"
            impact = "显著全球溢出"
        elif current > 150:
            regime = "中等不确定"
            impact = "温和影响"
        else:
            regime = "低不确定"
            impact = "影响有限"
        
        return {
            "indicator": "美国经济政策不确定性",
            "current_value": round(float(current), 1),
            "statistics": {"change_1m": round(change_1m, 1)},
            "regime": regime,
            "impact": impact
        }

    def analyze_us_fiscal_balance(self):
        """分析美国月度财政余额 - 简化版"""
        if 'MTSDS133FMS' not in self.data.columns:
            return {"status": "unavailable", "message": "美国月度财政余额数据不可用"}
        
        series = self.data['MTSDS133FMS'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_billions = current / 1000  # 转换为十亿美元
        change_3m = self._calculate_change(series, -63)
        
        # 简化财政状况分析
        if current_billions > 0:
            regime = "财政盈余"
            fiscal_health = "财政状况良好"
        elif current_billions > -100:
            regime = "温和赤字"
            fiscal_health = "财政压力可控"
        elif current_billions > -300:
            regime = "中等赤字"
            fiscal_health = "财政压力显现"
        else:
            regime = "高赤字"
            fiscal_health = "财政状况严峻"
        
        return {
            "indicator": "美国月度财政余额",
            "current_value": f"${current_billions:+.0f}B",
            "statistics": {"change_3m": round(change_3m, 1)},
            "regime": regime,
            "fiscal_health": fiscal_health
        }

    def analyze_michigan_consumer_sentiment(self):
         """分析密歇根消费者信心指数 - 简化版"""
         if 'UMCSENT' not in self.data.columns:
             return {"status": "unavailable", "message": "密歇根消费者信心指数数据不可用"}
         
         series = self.data['UMCSENT'].dropna()
         if len(series) < 2:
             return {"status": "insufficient_data"}
             
         current = series.iloc[-1]
         change_1m = self._calculate_change(series, -21)
         
         # 简化信心水平分析
         if current > 90:
             regime = "高信心"
             economic_signal = "经济增长强劲"
         elif current > 70:
             regime = "中高信心"
             economic_signal = "经济稳健增长"
         elif current > 50:
             regime = "中等信心"
             economic_signal = "经济增长温和"
         else:
             regime = "低信心"
             economic_signal = "经济增长承压"
         
         return {
             "indicator": "密歇根消费者信心",
             "current_value": round(float(current), 1),
             "statistics": {"change_1m": round(change_1m, 1)},
             "regime": regime,
             "economic_signal": economic_signal
         }

    def analyze_5y_inflation_expectation(self):
         """分析5年期通胀预期 - 简化版"""
         if 'T5YIE' not in self.data.columns:
             return {"status": "unavailable", "message": "5年期通胀预期数据不可用"}
         
         series = self.data['T5YIE'].dropna()
         if len(series) < 2:
             return {"status": "insufficient_data"}
             
         current = series.iloc[-1]
         change_1m = self._calculate_change(series, -21)
         
         # 简化通胀预期分析
         target_deviation = current - 2.0  # Fed 2%目标
         
         if current > 3.5:
             regime = "高通胀预期"
             fed_challenge = "央行目标面临挑战"
         elif current > 2.5:
             regime = "偏高通胀预期"
             fed_challenge = "需要政策关注"
         elif current > 1.5:
             regime = "适中通胀预期"
             fed_challenge = "接近政策目标"
         else:
             regime = "低通胀预期"
             fed_challenge = "通缩风险担忧"
         
         return {
             "indicator": "5年期通胀预期",
             "current_value": f"{current:.2f}%",
             "statistics": {
                 "change_1m": f"{change_1m:+.2f}pp",
                 "vs_target": f"{target_deviation:+.2f}pp"
             },
             "regime": regime,
             "fed_challenge": fed_challenge
         }
   

# 美国宏观指标
    def analyze_core_cpi(self):
        """分析核心美国CPI - 简化版"""
        if 'CPILFESL' not in self.data.columns:
            return {"status": "unavailable"}
        
        series = self.data['CPILFESL'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
        
        current = series.iloc[-1]
        yoy_change = self._calculate_change(series, -252) if len(series) > 252 else 0
        
        if yoy_change > 4:
            regime = "高通胀"
        elif yoy_change > 3:
            regime = "通胀偏高"
        elif yoy_change > 2:
            regime = "温和通胀"
        else:
            regime = "低通胀"
        
        return {
            "indicator": "核心CPI",
            "current_value": round(float(current), 1),
            "yoy_change": f"{yoy_change:.1f}%",
            "regime": regime
        }
    def analyze_nonfarm_payrolls(self):
        """分析非农就业 - 简化版"""
        if 'PAYEMS' not in self.data.columns:
            return {"status": "unavailable"}
        
        series = self.data['PAYEMS'].dropna()
        if len(series) < 2:
            return {"status": "insufficient_data"}
        
        current = series.iloc[-1]
        change_1y = self._calculate_change(series, -12) if len(series) > 12 else 0
        
        if change_1y > 3:
            regime = "强劲就业增长"
        elif change_1y > 1.5:
            regime = "稳健就业增长"
        elif change_1y > 0:
            regime = "温和就业增长"
        else:
            regime = "就业增长乏力"
        
        return {
            "indicator": "非农就业",
            "current_value": f"{current/1000:.1f}M",
            "yoy_growth": f"{change_1y:.1f}%",
            "regime": regime
        }

    def analyze_trade_balance(self):
        """分析美国贸易差额 - 6个月分析版"""
        if 'BOPGSTB' not in self.data.columns:
            return {"status": "unavailable", "message": "美国贸易差额数据不可用"}
        
        series = self.data['BOPGSTB'].dropna()
        if len(series) < 7:  # 需要至少7个月数据计算6个月变化
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        current_billions = current / 1000  # 转换为十亿美元
        change_6m = self._calculate_change(series, -6)  # 6个月变化
        
        # 根据贸易差额规模进行专业制度分析（注意：负值为逆差，正值为顺差）
        if current_billions > 0:
            regime = "贸易顺差"
            fiscal_impact = "贸易盈余支撑美元，减轻财政压力"
            global_balance = "全球贸易格局调整，美国竞争力提升"
            policy_implication = "贸易政策成效显现，但需防范报复性措施"
        elif current_billions > -40:
            regime = "温和贸易逆差"
            fiscal_impact = "逆差规模可控，对美元支撑影响有限"
            global_balance = "全球贸易相对均衡，经济一体化正常运行"
            policy_implication = "贸易政策保持稳定，关注结构性调整"
        elif current_billions > -60:
            regime = "中等贸易逆差"
            fiscal_impact = "逆差压力显现，美元承受一定贬值压力"
            global_balance = "全球贸易失衡加剧，需要政策协调"
            policy_implication = "贸易政策面临调整压力，可能加强保护措施"
        elif current_billions > -80:
            regime = "高贸易逆差"
            fiscal_impact = "逆差严重影响财政，美元贬值压力增大"
            global_balance = "全球贸易严重失衡，引发贸易摩擦风险"
            policy_implication = "贸易保护主义抬头，关税政策趋紧"
        else:
            regime = "极高贸易逆差"
            fiscal_impact = "逆差威胁经济稳定，美元霸权地位受挑战"
            global_balance = "全球贸易体系面临重构，经济脱钩风险"
            policy_implication = "贸易战风险升级，全球供应链重塑"
    
        # 分析6个月变化趋势的含义
        if change_6m > 8:  # 6个月变化大于8%
            if current_billions < 0:
                trend_signal = "贸易逆差半年来快速扩大，政策调整效果有限"
            else:
                trend_signal = "贸易顺差半年来显著增长，竞争力快速提升"
        elif change_6m < -8:  # 6个月变化小于-8%
            if current_billions < 0:
                trend_signal = "贸易逆差半年来明显改善，政策效果开始显现"
            else:
                trend_signal = "贸易顺差半年来大幅收窄，竞争优势有所削弱"
        else:
            trend_signal = "贸易差额半年来变化平稳，短期政策影响有限"
        
        return {
            "indicator": "美国贸易差额",
            "current_value": f"${current_billions:+.0f}B",
            "statistics": {"change_6m": f"{change_6m:+.1f}%"},
            "regime": regime,
            "fiscal_impact": fiscal_impact,
            "global_balance": global_balance,
            "policy_implication": policy_implication,
            "trend_signal": trend_signal,
            "economic_significance": "6个月贸易差额变化反映短期政策效果和经济周期波动"
        }

    def analyze_china_exports(self):
        """分析中国出口 - 年度分析版"""
        if 'EXPCH' not in self.data.columns:
            return {"status": "unavailable", "message": "中国出口数据不可用"}
        
        series = self.data['EXPCH'].dropna()
        if len(series) < 13:  # 需要至少13个月数据计算年度变化
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_yoy = self._calculate_change(series, -12)  # 12个月同比变化
        
        # 根据年度同比变化进行专业制度分析
        if change_yoy > 15:
            regime = "出口强劲增长"
            global_impact = "全球需求旺盛，中国制造业竞争力显著提升"
            supply_chain = "供应链韧性强化，外贸企业盈利能力大幅改善"
            market_signal = "全球经济复苏强劲，国际贸易环境持续改善"
        elif change_yoy > 8:
            regime = "出口稳定增长" 
            global_impact = "全球贸易持续复苏，外需为经济增长提供有力支撑"
            supply_chain = "制造业出口订单稳定增长，产业链运转顺畅"
            market_signal = "全球需求结构性改善，中国出口竞争优势巩固"
        elif change_yoy > 2:
            regime = "出口温和增长"
            global_impact = "全球需求缓慢复苏，外贸增长动能有所减弱"
            supply_chain = "出口企业适应性调整，供应链压力总体可控"
            market_signal = "全球经济增长分化，外需支撑力度趋缓"
        elif change_yoy > -5:
            regime = "出口轻微下滑"
            global_impact = "全球需求疲软，贸易保护主义影响逐步显现"
            supply_chain = "出口企业面临订单波动，供应链稳定性面临考验"
            market_signal = "全球经济下行风险加大，贸易增长承压"
        elif change_yoy > -15:
            regime = "出口明显下滑"
            global_impact = "全球贸易显著收缩，经济衰退风险上升"
            supply_chain = "制造业出口受到严重冲击，供应链断裂风险增加"
            market_signal = "全球贸易保护升级，多边贸易体系承压"
        else:
            regime = "出口大幅下滑"
            global_impact = "全球经济深度衰退，外需急剧萎缩"
            supply_chain = "出口产业链面临系统性冲击，结构重组不可避免"
            market_signal = "全球贸易体系重构，经济脱钩风险显著"
        
        return {
            "indicator": "中国出口",
            "current_value": f"${current:.0f}B",
            "statistics": {"change_yoy": f"{change_yoy:+.1f}%"},
            "regime": regime,
            "global_impact": global_impact,
            "supply_chain": supply_chain,
            "market_signal": market_signal,
            "economic_significance": "出口年度变化反映中国在全球价值链中的地位变迁"
        }


    def analyze_china_imports(self):
        """分析中国进口 - 年度分析版"""
        if 'IMPCH' not in self.data.columns:
            return {"status": "unavailable", "message": "中国进口数据不可用"}
        
        series = self.data['IMPCH'].dropna()
        if len(series) < 13:
            return {"status": "insufficient_data"}
            
        current = series.iloc[-1]
        change_yoy = self._calculate_change(series, -12)  # 12个月同比变化
        
        # 根据年度同比变化进行专业制度分析
        if change_yoy > 15:
            regime = "进口强劲增长"
            domestic_demand = "内需强劲复苏，消费升级和投资扩张并进"
            economic_health = "经济内生动力充沛，高质量发展态势明确"
            policy_signal = "经济过热压力显现，政策或将适度收紧"
        elif change_yoy > 8:
            regime = "进口稳定增长"
            domestic_demand = "内需持续改善，消费和投资保持稳定增长"
            economic_health = "内外需协调发展，经济运行在合理区间"
            policy_signal = "政策环境总体稳定，支持经济持续复苏"
        elif change_yoy > 2:
            regime = "进口温和增长"
            domestic_demand = "内需恢复缓慢，消费和投资动能仍显不足"
            economic_health = "经济增长对外需依赖较重，内需潜力待释放"
            policy_signal = "需要更多政策措施激发内需活力"
        elif change_yoy > -5:
            regime = "进口轻微下滑"
            domestic_demand = "内需增长乏力，消费信心和投资意愿偏弱"
            economic_health = "经济下行压力加大，内外需双重挑战"
            policy_signal = "亟需扩张性政策组合提振内需"
        elif change_yoy > -15:
            regime = "进口明显下滑"
            domestic_demand = "内需显著萎缩，消费和投资大幅放缓"
            economic_health = "经济衰退风险上升，结构性问题凸显"
            policy_signal = "需要大力度逆周期调节政策"
        else:
            regime = "进口大幅下滑"
            domestic_demand = "内需严重收缩，经济面临硬着陆风险"
            economic_health = "经济深度调整，系统性风险需高度警惕"
            policy_signal = "必须实施危机应对级别的政策干预"
        
        return {
            "indicator": "中国进口",
            "current_value": f"${current:.0f}B",
            "statistics": {"change_yoy": f"{change_yoy:+.1f}%"},
            "regime": regime,
            "domestic_demand": domestic_demand,
            "economic_health": economic_health,
            "policy_signal": policy_signal,
            "economic_significance": "进口年度变化是观察中国内需强度和经济结构调整的关键指标"
        }

    
#———    ———————————————————————————————————————————————
#计算框架
    def calculate_risk_matrix(self):
        """生成风险矩阵JSON数据"""
        
        # 获取各项分析结果
        vix_data = self.analyze_vix()
        fed_rrp_data = self.analyze_fed_rrp()
        dollar_data = self.analyze_dollar_index()
        walcl_data = self.analyze_walcl()
        skew_data = self.analyze_skew()
        move_data = self.analyze_move() 
        t10y2y_data = self.analyze_yield_curve_t10y2y() 
        hy_spread_data = self.analyze_hy_credit_spread()  
        nfci_data = self.analyze_nfci() 
        sofr_data = self.analyze_sofr()

   
        # 大宗商品分析
        wti_crude_data = self.analyze_wti_crude()
        gold_data = self.analyze_gold_futures()
        copper_data = self.analyze_copper_futures()
        natural_gas_data = self.analyze_natural_gas()
        soybean_data = self.analyze_soybean()
        corn_data = self.analyze_corn()
        wheat_data = self.analyze_wheat()
        dbc_data = self.analyze_dbc_etf()

         #汇率风险分析
        jpy_data = self.analyze_jpy_usd()
        eur_data = self.analyze_eur_usd()
        cny_data = self.analyze_cny_usd()
        #gbp_data = self.analyze_gbp_usd()
        btc_data = self.analyze_btc_usd()
        eth_data = self.analyze_eth_usd()
        sol_data = self.analyze_sol_usd()

        # 经济政策不确定性分析
        world_epu_data = self.analyze_world_epu()
        us_epu_data = self.analyze_us_epu()
        fiscal_balance_data = self.analyze_us_fiscal_balance()
        consumer_sentiment_data = self.analyze_michigan_consumer_sentiment()
        inflation_expectation_5y_data = self.analyze_5y_inflation_expectation()
        #宏观经济
        core_cpi_data = self.analyze_core_cpi(),
        nonfarm_data = self.analyze_nonfarm_payrolls(),
        trade_balance_data = self.analyze_trade_balance(),
        china_exports_data = self.analyze_china_exports(),
        china_imports_data = self.analyze_china_imports()
            
        
        # 构建完整的JSON数据
        risk_matrix = {
            "metadata": {
                "report_type": "全球风险情绪综合仪表盘",
                "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "data_date": self.data.index.max().strftime('%Y-%m-%d'),
                "version": "1.0"
            },
            "main_indicators": {
                "vix": vix_data,
                "fed_rrp": fed_rrp_data,
                "dollar_index": dollar_data,
                "walcl": walcl_data,
                "skew": skew_data  # 修正：使用 "skew" 键
                ,"move": move_data 
                ,"t10y2y": t10y2y_data
                ,"hy_spread": hy_spread_data
                ,"nfci": nfci_data 
                ,"sofr": sofr_data
                ,"wti_crude": wti_crude_data 
                ,"gold": gold_data
                ,"copper": copper_data
                ,"natural_gas": natural_gas_data
                ,"soybean": soybean_data
                ,"corn": corn_data
                ,"wheat": wheat_data
                ,"dbc": dbc_data
                ,"jpy": jpy_data,
                "eur": eur_data,
                "cny": cny_data,
                #"gbp": gbp_data,
                "btc": btc_data,
                "eth": eth_data,
                "sol": sol_data
                ,"world_epu": world_epu_data,
                "us_epu": us_epu_data,
                "fiscal_balance": fiscal_balance_data,
                "consumer_sentiment": consumer_sentiment_data,
                "inflation_expectation_5y": inflation_expectation_5y_data
                ,"core_cpi":core_cpi_data
                ,"nonfarm":nonfarm_data
                ,"trade_balance":trade_balance_data
                ,"china_exports":china_exports_data
                ,"china_imports":china_imports_data
            },
            #"other_indicators": other_data
        }
        
        return risk_matrix


    
     
if __name__ == "__main__":
    # 修正：正确创建分析器并获取数据
    risk_analyzer = RiskSentimentAnalyzer()
    data = risk_analyzer.calculate_risk_matrix()
    
    # 创建数据目录
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # 保存到本地文件
    today = datetime.now().strftime("%Y-%m-%d")
    with open(f"data/risk-matrix-{today}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 同时保存为latest.json
    with open("data/risk-matrix-latest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已保存到 risk-matrix-{today}.json")
    print(f"✅ 数据已保存到 risk-matrix-latest.json")
    
    # 展示分析结果
    risk_analyzer.display_analysis_results(data)

