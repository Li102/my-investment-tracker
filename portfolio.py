import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit as st

# Step1：設定頁面配置
st.set_page_config(page_title="Python 投資小工具", layout="wide")

# 1. 定義長頸鹿圖片的網址 (你可以換成任何你喜歡的 GIF 或 PNG)
giraffe_url = "https://raw.githubusercontent.com/Li102/my-investment-tracker/refs/heads/main/giraffe.png"

# 2. 使用 CSS 把它固定在右下角
st.markdown(
    f"""
    <style>
    .giraffe-container {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 100;
    }}
    .giraffe-container img {{
        width: 100px;  /* 調整長頸鹿的大小 */
    }}
    </style>
    <div class="giraffe-container">
        <img src="{giraffe_url}" alt="Giraffe">
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📈 投資組合分析")

# ====== 1. 介面輸入區：讓使用者自行定義組合 ======
st.sidebar.header("📥 你的投資組合")

# 預設資料 (DataFrame 格式，方便介面編輯)
init_data = [
    {"Ticker": "0050", "Shares": 100.00, "Cost": 50, "Target": 0.40},
    {"Ticker": "BNDW", "Shares": 50.00, "Cost": 100.0, "Target": 0.15},
    {"Ticker": "VT", "Shares": 100.00, "Cost": 150.0, "Target": 0.45}
]

# 使用 st.data_editor 建立像 Excel 一樣的可編輯表格
edited_df = st.sidebar.data_editor(
    pd.DataFrame(init_data), 
    num_rows="dynamic", # 允許動態增加或刪除列
    key="portfolio_editor"
)

# ====== 2. 核心運算邏輯 ======
if st.sidebar.button("🚀 開始計算"):
    with st.spinner('正在從 Yahoo Finance 抓取數據...'):
        tickers = edited_df["Ticker"].tolist()
        
        # 批次抓取 (含匯率)
        all_data = yf.download(tickers + ["TWD=X"], period="5d", progress=False)['Close'].ffill().iloc[-1]
        usdtwd = all_data["TWD=X"]
        
        # 整理計算
        df = edited_df.set_index("Ticker")
        df['Current_Price'] = all_data[tickers]
        
        # 匯率轉換
        df['Price_TWD'] = df.apply(lambda x: x['Current_Price'] * usdtwd if ".TW" not in x.name else x['Current_Price'], axis=1)
        df['Cost_TWD'] = df.apply(lambda x: x['Cost'] * usdtwd if ".TW" not in x.name else x['Cost'], axis=1)
        
        df['Market_Value'] = df['Price_TWD'] * df['Shares']
        total_val = df['Market_Value'].sum()
        df['Weight'] = df['Market_Value'] / total_val
        df['Return_%'] = (df['Price_TWD'] - df['Cost_TWD']) / df['Cost_TWD'] * 100

        # ====== 智能投顧邏輯：再平衡行動指令 ======
    st.divider()
    st.subheader("🤖 智能再平衡行動指令 (Smart Action Plan)")

    # 1. 輸入下個月預計投入金額
    monthly_budget = st.number_input("下個月預計投入金額 (TWD)", min_value=0, value=24000, step=1000)

    if st.button("📊 生成投資建議"):
        # 計算投入後的理想總市值
        new_total_val = total_val + monthly_budget
        
        # 計算各標的「理想市值」與「現有市值」的差距
        actions = []
        for idx, row in df.iterrows():
            ideal_val = new_total_val * row['Target']
            gap = ideal_val - row['Market_Value']
            # gap > 0 代表需要補倉
            actions.append({"Ticker": idx, "Gap": max(0, gap)})
    
    # 2. 比例分配邏輯 (把 24,000 按缺口比例分配)
    total_gap = sum(item["Gap"] for item in actions)
    
    if total_gap > 0:
        st.info(f"依據您的目標比例 40:45:15，這 ${monthly_budget:,.0f} 建議分配如下：")
        
        # 建立建議表格
        advice_list = []
        for item in actions:
            # 按缺口比例分配預算
            allocation = (item["Gap"] / total_gap) * monthly_budget
            advice_list.append({
                "標的": item["Ticker"],
                "建議投入金額 (TWD)": round(allocation, 0),
                "分配比例": f"{(allocation/monthly_budget)*100:.1f}%"
            })
        
        st.table(pd.DataFrame(advice_list))
        st.success("💡 優先補足「目前權重偏低」的標的，無需賣出即可達成再平衡！")
    else:
        st.write("目前組合非常平衡，建議按原比例分配即可。")

        # ====== 3. 視覺化呈現 ======
        # 顯示重點指標 (Metric)
        m1, m2 = st.columns(2)
        m1.metric("總市值 (TWD)", f"${total_val:,.0f}")
        m2.metric("USD/TWD 匯率", f"{usdtwd:.2f}")

        # 顯示主要表格
        st.subheader("📊 詳細分析報表")
        st.dataframe(
            df[['Current_Price', 'Return_%', 'Weight', 'Target']].style.format({
                'Current_Price': '{:,.2f}',
                'Return_%': '{:+.2f}%',
                'Weight': '{:.2%}',
                'Target': '{:.2%}'
            }), 
            use_container_width=True
        )

        # 顯示警報
        for idx, row in df.iterrows():
            diff = row['Weight'] - row['Target']
            if abs(diff) > 0.05:
                st.warning(f"⚠️ **{idx}** 偏離目標平衡點 ({diff:+.2%})，建議調整。")
