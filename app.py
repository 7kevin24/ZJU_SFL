import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 配置页面 ---
st.set_page_config(page_title="SF6 SFL Manager", layout="wide")
st.title("🥊 SF6 小型联赛 (SFL Rules)")

# --- 1. 连接 Google Sheets ---
# 使用 ttl 缓存防止频繁请求 API
# 强制指定 URL，跳过 secrets 文件的 URL 读取
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    # 读取指定工作表
    return conn.read(worksheet=sheet_name, ttl=0) # ttl=0 保证读取最新数据

def save_data(df, sheet_name):
    # 写入数据 (全量更新，生产环境建议优化为追加模式)
    conn.update(worksheet=sheet_name, data=df)
    st.cache_data.clear() # 清除缓存

# 加载数据
try:
    df_schedule = load_data("schedule")
    df_logs = load_data("matchlogs")
    df_config = load_data("configs")
    
    # 获取下拉菜单选项
    teams_list = df_config['Teams'].dropna().unique().tolist()
    chars_list = df_config['Characters'].dropna().unique().tolist()
    players_list = df_config['Players'].dropna().unique().tolist()
except Exception as e:
    st.error(f"连接数据库失败，请检查配置。Error: {e}")
    st.stop()

# --- 导航栏 ---
tab1, tab2, tab3 = st.tabs(["📝 比赛录入 (Admin)", "🏆 积分榜 (Standings)", "📊 数据统计 (Stats)"])

# ==============================================================================
# TAB 1: 比赛录入 (核心逻辑)
# ==============================================================================
with tab1:
    st.header("常规赛录入")
    
    # 1. 选择场次
    pending_matches = df_schedule[df_schedule['Status'] == 'Pending']
    if pending_matches.empty:
        st.success("所有比赛已完成！")
    else:
        selected_match_label = st.selectbox(
            "选择场次", 
            pending_matches['MatchID'] + " | " + pending_matches['HomeTeam'] + " vs " + pending_matches['AwayTeam']
        )
        
        # 解析选中的比赛信息
        match_id = selected_match_label.split(" | ")[0]
        current_match = df_schedule[df_schedule['MatchID'] == match_id].iloc[0]
        home_team = current_match['HomeTeam']
        away_team = current_match['AwayTeam']

        st.info(f"正在录入: **{home_team} (Home)** vs **{away_team} (Away)**")
        st.markdown("---")

        with st.form("match_entry_form"):
            st.write("#### 1. 先锋战 (Vanguard) - 10 pts")
            col1, col2, col3, col4 = st.columns(4)
            v_home_p = col1.selectbox("Home 选手", players_list, key="v_hp")
            v_home_c = col2.selectbox("Home 角色", chars_list, key="v_hc")
            v_away_p = col3.selectbox("Away 选手", players_list, key="v_ap")
            v_away_c = col4.selectbox("Away 角色", chars_list, key="v_ac")
            
            col5, col6, col7 = st.columns(3)
            v_score_home = col5.number_input("Home 胜局 (Sets)", 0, 2, key="v_sh")
            v_score_away = col6.number_input("Away 胜局 (Sets)", 0, 2, key="v_sa")
            # SFL规则：用于Tie-breaker的灯数
            v_rounds_home = col7.number_input("Home 总获胜灯数 (Rounds)", 0, 10, key="v_rh", help="用于平局判定")
            v_rounds_away = col7.number_input("Away 总获胜灯数 (Rounds)", 0, 10, key="v_ra")

            st.markdown("---")
            st.write("#### 2. 中坚战 (Center) - 10 pts")
            # (此处重复类似的 Input 结构，为了代码简洁省略，实际需补全)
            # ... 变量名 c_home_p 等 ...
            c_score_home = st.number_input("Home 胜局 (Center)", 0, 2, key="c_sh")
            c_score_away = st.number_input("Away 胜局 (Center)", 0, 2, key="c_sa")
            
            st.markdown("---")
            st.write("#### 3. 大将战 (General) - 20 pts")
            # ... 变量名 g_home_p 等 ...
            g_score_home = st.number_input("Home 胜局 (General)", 0, 3, key="g_sh")
            g_score_away = st.number_input("Away 胜局 (General)", 0, 3, key="g_sa")

            # 计算是否需要加赛
            # 逻辑：V(10) + C(10) + G(20) = 40 total. Tie occurs at 20-20.
            
            st.markdown("---")
            st.write("#### 4. 加赛 (Extra Battle) - 10 pts (仅在平局时有效)")
            e_winner = st.radio("加赛胜者", ["无加赛", "Home", "Away"], key="e_win")
            
            submitted = st.form_submit_button("提交比赛结果")
            
            if submitted:
                # 1. 计算积分
                home_pts = 0
                away_pts = 0
                
                # 先锋
                if v_score_home > v_score_away: home_pts += 10
                else: away_pts += 10
                # 中坚
                if c_score_home > c_score_away: home_pts += 10
                else: away_pts += 10
                # 大将
                if g_score_home > g_score_away: home_pts += 20
                else: away_pts += 20
                
                # 校验是否需要加赛
                if home_pts == away_pts and e_winner == "无加赛":
                    st.error("比分 20-20 平，必须录入加赛结果！")
                else:
                    if e_winner == "Home": home_pts += 10
                    elif e_winner == "Away": away_pts += 10
                    
                    # 2. 构建 MatchLog 数据并保存 (此处为简化，实际应append到df_logs)
                    new_logs = pd.DataFrame([
                        # Vanguard
                        {
                            "MatchID": match_id, "Position": "Vanguard", 
                            "Winner": "Home" if v_score_home > v_score_away else "Away",
                            "HomeChar": v_home_c, "AwayChar": v_away_c
                            # ...其他字段
                        },
                        # ... Center, General ...
                    ])
                    # 写入 df_logs (追加模式)
                    updated_logs = pd.concat([df_logs, new_logs], ignore_index=True)
                    save_data(updated_logs, "MatchLog")

                    # 3. 更新 Schedule 表的状态和总分
                    df_schedule.loc[df_schedule['MatchID'] == match_id, ['Status', 'HomeTotalPoints', 'AwayTotalPoints']] = ['Done', home_pts, away_pts]
                    save_data(df_schedule, "Schedule")
                    
                    st.success(f"录入成功！比分: {home_pts} - {away_pts}")
                    st.rerun()

# ==============================================================================
# TAB 2: 积分榜 (Standings)
# ==============================================================================
with tab2:
    st.header("🏆 实时积分榜")
    
    # 计算每个队伍的总分
    # 这一步需要聚合 HomeTotalPoints 和 AwayTotalPoints
    team_stats = {team: {'Points': 0, 'Matches': 0} for team in teams_list}
    
    done_matches = df_schedule[df_schedule['Status'] == 'Done']
    
    for _, row in done_matches.iterrows():
        team_stats[row['HomeTeam']]['Points'] += row['HomeTotalPoints']
        team_stats[row['HomeTeam']]['Matches'] += 1
        team_stats[row['AwayTeam']]['Points'] += row['AwayTotalPoints']
        team_stats[row['AwayTeam']]['Matches'] += 1
        
        # 这里还需要从 MatchLog 聚合 Battle Diff 和 Round Diff (SFL 排位关键)
        # 为了代码简洁，此处略去复杂聚合，实际开发需从 df_logs 计算 diff
        
    df_standings = pd.DataFrame.from_dict(team_stats, orient='index').reset_index()
    df_standings.columns = ['Team', 'Points', 'Matches Played']
    df_standings = df_standings.sort_values(by='Points', ascending=False).reset_index(drop=True)
    
    st.dataframe(df_standings, use_container_width=True)

# ==============================================================================
# TAB 3: 数据统计 (Analytics)
# ==============================================================================
with tab3:
    st.header("📊 数据统计")
    
    if df_logs.empty:
        st.info("暂无比赛数据")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("角色出场率")
            # 合并 Home 和 Away 的角色
            all_chars = pd.concat([df_logs['HomeChar'], df_logs['AwayChar']])
            char_counts = all_chars.value_counts()
            st.bar_chart(char_counts)
            
        with col2:
            st.subheader("先手胜率 (Home Win Rate)")
            home_wins = len(df_logs[df_logs['Winner'] == 'Home'])
            total = len(df_logs)
            if total > 0:
                st.metric("主场胜率", f"{home_wins/total:.1%}")