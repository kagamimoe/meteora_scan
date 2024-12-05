from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from typing import List, Dict
import pandas as pd
import httpx
import time
from datetime import datetime
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建templates目录并使用Jinja2模板
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """渲染主页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

async def fetch_all_pages() -> List[Dict]:
    """获取所有页面数据"""
    print("\n=== 开始获取页面数据 ===")
    all_data = []
    page = 0
    MAX_PAGES = 10  # 添加最大页数限制
    
    try:
        while page < MAX_PAGES:  # 修改循环条件
            print(f"\n获取第 {page + 1} 页...")
            url = f"https://app.meteora.ag/clmm-api/pair/all_by_groups?page={page}&limit=100&unknown=true&sort_key=feetvlratio&order_by=desc"
            
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    print(f"发送请求: {url}")
                    response = await client.get(url)
                    print(f"响应状态码: {response.status_code}")
                    
                    if response.status_code != 200:
                        print(f"请求失败: {response.text}")
                        break
                        
                    data = response.json()
                    print(f"响应数据类型: {type(data)}")
                    
                    if not data.get('groups'):
                        print("没有更多数据，结束获取")
                        break
                        
                    all_data.append(data)
                    print(f"成功获取第 {page + 1} 页数据")
                    page += 1
                    
            except Exception as e:
                print(f"获取第 {page + 1} 页时出错: {str(e)}")
                print(f"错误类型: {type(e)}")
                break
                
            await asyncio.sleep(0.5)
            
    except Exception as e:
        print(f"获取页面数据时出错: {str(e)}")
        print(f"错误类型: {type(e)}")
        
    print(f"\n总共获取了 {len(all_data)} 页数据")
    return all_data

@app.get("/api/data")
async def get_data(
    min_apr: float = 50,
    max_apr: float = 500,
    min_volume: float = 200000,
    min_liquidity: float = 10000
):
    """获取数据API"""
    print(f"\n=== 开始获取数据 (过滤条件: APR {min_apr}-{max_apr}, 最小交易量 {min_volume}, 最小流动性 {min_liquidity}) ===")
    try:
        print("1. 开始调用 fetch_all_pages...")
        all_data = await fetch_all_pages()
        print(f"2. fetch_all_pages 返回结果类型: {type(all_data)}")
        print(f"2.1 是否获取到数据: {bool(all_data)}")
        
        if not all_data:
            print("3. 未获取到数据，返回空列表")
            return {
                "data": [],
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "no_data"
            }

        # 处理数据
        print("4. 开始处理数据...")
        all_pairs = []
        total_groups = sum(len(page.get('groups', [])) for page in all_data)
        print(f"4.1 总页数: {len(all_data)}, 总组数: {total_groups}")

        for page_idx, page_data in enumerate(all_data):
            print(f"\n5. 处理 {page_idx + 1} 页数据")
            for group in page_data.get('groups', []):
                print(f"5.1 处理组: {group.get('name', 'unknown')}")
                for pair in group.get('pairs', []):
                    try:
                        print(f"\n6. 开始处理交易对: {pair.get('name', 'unknown')}")
                        
                        # 获取并验证基本数据
                        apr = float(pair['apr']) if pair['apr'] not in ['', None] else 0
                        trade_volume_24h = float(pair['trade_volume_24h']) if pair['trade_volume_24h'] not in ['', None] else 0
                        liquidity = float(pair['liquidity']) if pair['liquidity'] not in ['', None] else 0
                        base_fee = float(pair['base_fee_percentage']) if pair['base_fee_percentage'] not in ['', None] else 0
                        
                        print(f"6.1 基本数据: APR={apr}, Volume24h={trade_volume_24h}, Liquidity={liquidity}")
                        
                        # 检查筛选条件
                        if not (min_apr < apr < max_apr and trade_volume_24h > min_volume and liquidity > min_liquidity):
                            print("6.2 不符合筛选条件，跳过")
                            continue
                        
                        print("7. 获 DexScreener 数据...")
                        dex_data = await get_dexscreener_data(pair['address'])
                        print(f"7.1 DexScreener 数据类型: {type(dex_data)}")
                        
                        volume_5min = float(dex_data.get('volume', {}).get('m5', 0))
                        fdv = float(dex_data.get('fdv', 0))
                        
                        fees_5min = volume_5min * (base_fee / 100)
                        apd_5min = (fees_5min / liquidity) * 12 * 24 * 100 if liquidity > 0 else 0
                        
                        pair_data = {
                            'pair_name': pair['name'],
                            'pair_link': f"https://app.meteora.ag/dlmm/{pair['address']}",
                            'address': pair['address'],
                            'liquidity': round(liquidity, 2),
                            'base_fee': round(base_fee, 2),
                            'trade_volume_24h': round(trade_volume_24h, 2),
                            'fees_24h': round(float(pair['fees_24h']) if pair['fees_24h'] not in ['', None] else 0, 2),
                            'volume_5min': round(volume_5min, 2),
                            'fees_5min': round(fees_5min, 2),
                            'apd_5min': round(apd_5min, 2),
                            'apr': round(apr, 2),
                            'fdv': round(fdv, 2),
                            'dex_name': 'dex_link',
                            'dex_link': f"https://dexscreener.com/solana/{pair['address']}"
                        }
                        all_pairs.append(pair_data)
                        print(f"8. 成功添加交易对: {pair['name']}")
                        
                    except Exception as e:
                        print(f"处理交易对时出错: {str(e)}")
                        print(f"错误类型: {type(e)}")
                        print(f"交易对数据: {pair}")
                        continue
                    
                    await asyncio.sleep(0.2)

        print("\n=== 数据处理完成 ===")
        print(f"总共处理成功的交易对数量: {len(all_pairs)}")
        
        if not all_pairs:
            print("没有符合条件的交易对")
            return {
                "data": [],
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "no_data"
            }

        print("返回数据...")
        print(f"返回的数据数量: {len(all_pairs)}")
        return {
            "data": all_pairs,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }

    except Exception as e:
        print("\n=== 发生错误 ===")
        print(f"错误类型: {type(e)}")
        print(f"错误信息: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        return {
            "data": [],
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "error",
            "error": str(e)
        }

async def get_dexscreener_data(address: str) -> Dict:
    """获取DexScreener数据"""
    url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{address}"
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            if data and 'pairs' in data and len(data['pairs']) > 0:
                return data['pairs'][0]
    except Exception as e:
        print(f"获取DexScreener数据失败: {str(e)}")
    return {}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 