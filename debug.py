import streamlit as st

st.title("🕵️ Secrets 诊断工具")

st.write("正在检查 secrets.toml 文件...")

# 尝试打印所有读取到的配置
try:
    # 把 secrets 转换成字典打印出来
    st.write("读取到的配置内容：", dict(st.secrets))

    # 专门检查有没有 gsheets 部分
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        st.success("✅ 成功检测到 [connections.gsheets] 配置！")
    else:
        st.error("❌ 未检测到 [connections.gsheets] 部分！请检查 TOML 文件的拼写。")

except FileNotFoundError:
    st.error("❌ 根本没找到 secrets.toml 文件！请检查文件路径。")