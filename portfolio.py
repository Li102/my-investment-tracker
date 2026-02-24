import streamlit as st
import yfinance as yf
import pandas as pd

# Step1：設定頁面配置 (必須在第一行)
st.set_page_config(page_title="Python 投資小工具", layout="wide")

# --- 長頸鹿 CSS ---
giraffe_url = "https://raw.githubusercontent.com/Li102/my-investment-tracker/refs/heads/main/giraffe.png"
st.markdown(f"""
    <style>
    .giraffe-container {{ position: fixed; bottom: 20px; right: 20px; z-index: 100; }}
    .giraffe-container img {{ width: 100px; }}
    </style>
    <div class="giraffe-container"><img src="{giraffe_url}"></div>
    """, unsafe_allow_html=True)

st.title("📈 投資組合分析")

# ====== 1. 介面輸入區 ======
st.sidebar.header("📥 你的投資組合")
init_data = [
    {"Ticker": "0050.TW", "Shares": 100.00, "Cost": 50, "Target": 0.40},
    {"Ticker": "BNDW", "Shares": 50.00, "Cost": 100.0, "Target": 0.15},
    {"Ticker": "VT", "Shares": 100.00, "Cost": 150.0, "Target": 0.45}
]
edited_df = st.sidebar.data_editor(pd.DataFrame(init_data), num_rows="dynamic", key="portfolio_editor")

# ====== 2. 核心運算函數 (加入快取避免閃退) ======
@st.cache_data(ttl=600)
def fetch_data(tickers):
    data = yf.download(tickers + ["TWD=X"], period="5d", progress=False)['Close'].ffill().iloc[-1]
    return data

# 提取 Tickers
tickers_list = edited_df["Ticker"].tolist()

# 點擊按鈕或初次載入執行計算
if st.sidebar.button("🚀 更新數據") or 'df' not in st.session_state:
    with st.spinner('抓取數據中...'):
        all_data = fetch_data(tickers_list)
        usdtwd = all_data["TWD=X"]
        
        calc_df = edited_df.set_index("Ticker")
        calc_df['Current_Price'] = all_data[tickers_list]
        
        # 匯率轉換與計算
        calc_df['Price_TWD'] = calc_df.apply(lambda x: x['Current_Price'] * usdtwd if ".TW" not in x.name else x['Current_Price'], axis=1)
        calc_df['Cost_TWD'] = calc_df.apply(lambda x: x['Cost'] * usdtwd if ".TW" not in x.name else x['Cost'], axis=1)
        calc_df['Market_Value'] = calc_df['Price_TWD'] * calc_df['Shares']
        
        # 存入 session_state 確保按其他按鈕時資料不會消失
        st.session_state.total_val = calc_df['Market_Value'].sum()
        st.session_state.usdtwd = usdtwd
        st.session_state.df = calc_df
        st.session_state.df['Weight'] = calc_df['Market_Value'] / st.session_state.total_val
        st.session_state.df['Return_%'] = (calc_df['Price_TWD'] - calc_df['Cost_TWD']) / calc_df['Cost_TWD'] * 100

# ====== 3. 視覺化呈現 (從 session_state 拿資料) ======
if 'df' in st.session_state:
    df = st.session_state.df
    total_val = st.session_state.total_val
    
    m1, m2 = st.columns(2)
    m1.metric("總市值 (TWD)", f"${total_val:,.0f}")
    m2.metric("USD/TWD 匯率", f"{st.session_state.usdtwd:.2f}")

    st.subheader("📊 分析結果")
    st.dataframe(df[['Current_Price', 'Return_%', 'Weight', 'Target']].style.format({
        'Current_Price': '{:,.2f}', 'Return_%': '{:+.2f}%', 'Weight': '{:.2%}', 'Target': '{:.2%}'
    }), use_container_width=True)

    # 顯示警報
    for idx, row in df.iterrows():
        diff = row['Weight'] - row['Target']
        if abs(diff) > 0.05:
            st.warning(f"⚠️ **{idx}** 偏離目標平衡點 ({diff:+.2%})，建議調整。")

    # ====== 4. 智能再平衡 (獨立區塊，不嵌套) ======
    st.divider()
    st.subheader("🤖 智能再平衡")
    monthly_budget = st.number_input("額外可投入金額 (TWD)", min_value=0, value=5000, step=1000)

    if st.button("📊 額外資金投入建議"):
        actions = []
        new_total_val = total_val + monthly_budget
        
        for idx, row in df.iterrows():
            ideal_val = new_total_val * row['Target']
            gap = max(0, ideal_val - row['Market_Value'])
            actions.append({"Ticker": idx, "Gap": gap})
        
        total_gap = sum(item["Gap"] for item in actions)
        
        if total_gap > 0:
            advice_list = []
            for item in actions:
                alloc = (item["Gap"] / total_gap) * monthly_budget
                if alloc > 0:
                    advice_list.append({
                        "標的": item["Ticker"],
                        "建議投入 (TWD)": alloc,
                        "分配比例": alloc/monthly_budget
                    })

            # 建立 DataFrame 並進行視覺化格式處理
            advice_df = pd.DataFrame(advice_list)

            # 使用 style.format 將金額設為整數，比例設為百分比
            st.table(advice_df.style.format({
                "建議投入 (TWD)": "{:,.0f}", # 加上千分位，並取 0 位小數
                "分配比例": "{:.1%}"        # 轉為百分比顯示，保留 1 位小數
            }))

            st.success("💡 優先補足權重偏低標的，達成再平衡！")
        else:
            st.write("目前組合非常平衡，建議按原比例分配。")

