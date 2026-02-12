import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Python 投資接案工具", layout="wide")

st.title("📈 投資組合即時監控介面")

# ====== 1. 介面輸入區：讓使用者自行定義組合 ======
st.sidebar.header("📥 配置你的投資組合")

# 預設資料 (DataFrame 格式，方便介面編輯)
init_data = [
    {"Ticker": "0050.TW", "Shares": 9821, "Cost": 37.56, "Target": 0.40},
    {"Ticker": "VT", "Shares": 167, "Cost": 134.0, "Target": 0.45},
    {"Ticker": "BNDW", "Shares": 116, "Cost": 69.0, "Target": 0.15}
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
