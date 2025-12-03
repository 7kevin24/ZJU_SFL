import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# ==============================================================================
# 0. 基础配置
# ==============================================================================
st.set_page_config(page_title="SF6 SFL Manager", layout="wide")
st.title("ZJU SFL Beta")

# 建立连接
conn = st.connection("gsheets", type=GSheetsConnection)

# ==============================================================================
# 1. 数据加载与预处理
# ==============================================================================
def load_data():
    # 强制不缓存，确保读取最新数据
    df_s = conn.read(worksheet="schedule", ttl=0)
    df_l = conn.read(worksheet="matchlogs", ttl=0)
    df_c = conn.read(worksheet="configs", ttl=0)
    return df_s, df_l, df_c

try:
    df_schedule, df_logs, df_config = load_data()
    
    # --- 核心逻辑更新：构建 Team -> Players 的映射字典 ---
    # 假设 configs 表 A列是 Team, B列是 Player
    # 数据清洗：去空值
    valid_config = df_config.dropna(subset=['Team', 'Player'])
    
    # 制作字典: {'Team Beast': ['Daigo', 'Fuudo'], 'Team Liquid': ['Nemo', ...]}
    team_player_map = valid_config.groupby('Team')['Player'].apply(list).to_dict()
    
    # 制作角色列表 (C列)
    chars_list = df_config['Character'].dropna().unique().tolist()
    if not chars_list: # 如果没读到，给默认值防止报错
        chars_list = ["Luke", "Ken", "Ryu", "Chun-Li", "Guile", "JP", "Juri", "Dee Jay", "Cammy", "Zangief", "Marisa", "Manon", "Lily", "Blanka", "Dhalsim", "E. Honda", "Jamie", "Kimberly", "Rashid", "A.K.I.", "Ed", "Akuma", "M. Bison", "Terry", "Mai","C.viper", "Sagat",]

except Exception as e:
    st.error(f"数据加载失败，请检查 Google Sheet 的 configs 表格式是否正确 (A列Team, B列Player)。报错信息: {e}")
    st.stop()

# ==============================================================================
# 2. 侧边栏：管理员验证
# ==============================================================================
with st.sidebar:
    st.header("🔐 管理员登录")
    password = st.text_input("输入管理密码", type="password")
    
    is_admin = False
    if "admin_password" in st.secrets:
        if password == st.secrets["admin_password"]:
            is_admin = True
            st.success("身份验证成功")
    else:
        st.warning("⚠️ 未设置密码，默认开放 (调试模式)")
        is_admin = True

# ==============================================================================
# 3. 页面布局
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📝 比赛录入", "🏆 积分榜", "📊 数据统计", "📜 历史战报"])

# ==============================================================================
# TAB 1: 比赛录入 (核心功能) - UI 已优化
# ==============================================================================
with tab1:
    if not is_admin:
        st.info("请在侧边栏输入密码以解锁录入功能。")
    else:
        st.header("比赛结果录入/修改")
        st.caption("提示：可以重新提交已完成 (Done) 的比赛，旧结果将被覆盖。")

        # --- 选择比赛 (显示所有比赛，不仅仅是 Pending) ---
        try:
            match_options = df_schedule.apply(
                lambda x: f"{x['MatchID']} | {x['HomeTeam']} vs {x['AwayTeam']} ({x['Status']})", axis=1
            )
            selected_match_label = st.selectbox("选择场次", match_options)

            if selected_match_label:
                # 解析 ID 和 队伍
                match_id = selected_match_label.split(" | ")[0]
                current_match = df_schedule[df_schedule['MatchID'] == match_id].iloc[0]
                
                home_team = current_match['HomeTeam']
                away_team = current_match['AwayTeam']
                
                st.info(f"🏟️ **{home_team}** (HOME) vs **{away_team}** (AWAY)")

                # --- 动态获取该战队的成员 ---
                home_team_players = team_player_map.get(home_team, ["未在Config中找到该队成员"])
                away_team_players = team_player_map.get(away_team, ["未在Config中找到该队成员"])

                # --- 表单开始 ---
                with st.form("match_entry_form"):
                    
                    # ---------------------------------------------------------
                    # 1. 先锋战 (Vanguard) - 10 pts
                    # ---------------------------------------------------------
                    st.markdown("#### ⚔️ 先锋战 (Vanguard) - 10 pts")
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 2, 2])
                    
                    # Home Block (c1, c2)
                    v_hp = c1.selectbox("Home 选手", home_team_players, key="v_hp")
                    v_hc = c2.selectbox("Home 角色", chars_list, key="v_hc")
                    v_sh = c1.number_input("Home 得分", 0, 2, key="v_sh") # H Score under H Player

                    # Middle Block (c3)
                    c3.markdown("<center>&nbsp;</center>", unsafe_allow_html=True) # 占位
                    c3.markdown("<center>vs</center>", unsafe_allow_html=True) # "vs" label
                    
                    # Away Block (c4, c5)
                    v_ac = c4.selectbox("Away 角色", chars_list, key="v_ac")
                    v_ap = c5.selectbox("Away 选手", away_team_players, key="v_ap")
                    v_sa = c5.number_input("Away 得分", 0, 2, key="v_sa") # A Score under A Player

                    st.divider()

                    # ---------------------------------------------------------
                    # 2. 中坚战 (Center) - 10 pts
                    # ---------------------------------------------------------
                    st.markdown("#### 🛡️ 中坚战 (Center) - 10 pts")
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 2, 2])
                    
                    # Home Block
                    c_hp = c1.selectbox("Home 选手", home_team_players, key="c_hp")
                    c_hc = c2.selectbox("Home 角色", chars_list, key="c_hc")
                    c_sh = c1.number_input("Home 得分", 0, 2, key="c_sh")
                    
                    # Middle Block
                    c3.markdown("<center>&nbsp;</center>", unsafe_allow_html=True)
                    c3.markdown("<center>vs</center>", unsafe_allow_html=True)
                    
                    # Away Block
                    c_ac = c4.selectbox("Away 角色", chars_list, key="c_ac")
                    c_ap = c5.selectbox("Away 选手", away_team_players, key="c_ap")
                    c_sa = c5.number_input("Away 得分", 0, 2, key="c_sa")

                    st.divider()

                    # ---------------------------------------------------------
                    # 3. 大将战 (General) - 20 pts (抢3)
                    # ---------------------------------------------------------
                    st.markdown("#### 👑 大将战 (General) - 20 pts")
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 2, 2])
                    
                    # Home Block
                    g_hp = c1.selectbox("Home 选手", home_team_players, key="g_hp")
                    g_hc = c2.selectbox("Home 角色", chars_list, key="g_hc")
                    g_sh = c1.number_input("Home 得分", 0, 3, key="g_sh")
                    
                    # Middle Block
                    c3.markdown("<center>&nbsp;</center>", unsafe_allow_html=True)
                    c3.markdown("<center>vs</center>", unsafe_allow_html=True)
                    
                    # Away Block
                    g_ac = c4.selectbox("Away 角色", chars_list, key="g_ac")
                    g_ap = c5.selectbox("Away 选手", away_team_players, key="g_ap")
                    g_sa = c5.number_input("Away 得分", 0, 3, key="g_sa")

                    st.divider()

                    # ---------------------------------------------------------
                    # 4. 加赛 (Extra Battle) - 10 pts
                    # ---------------------------------------------------------
                    st.markdown("#### 🔥 加赛 (Extra) - 仅平局时填写")
                    st.caption("当且仅当比分 20-20 时进行。BO3 (抢2) 决定胜负。")
                    
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 2, 2])
                    
                    # Home Block (使用 ["无"] 选项)
                    e_hp = c1.selectbox("Home 选手", ["无"] + home_team_players, key="e_hp")
                    e_hc = c2.selectbox("Home 角色", ["无"] + chars_list, key="e_hc")
                    e_sh = c1.number_input("Home 得分", 0, 2, key="e_sh")
                    
                    # Middle Block
                    c3.markdown("<center>&nbsp;</center>", unsafe_allow_html=True)
                    c3.markdown("<center>vs</center>", unsafe_allow_html=True)
                    
                    # Away Block (使用 ["无"] 选项)
                    e_ac = c4.selectbox("Away 角色", ["无"] + chars_list, key="e_ac")
                    e_ap = c5.selectbox("Away 选手", ["无"] + away_team_players, key="e_ap")
                    e_sa = c5.number_input("Away 得分", 0, 2, key="e_sa")

                    # --- 提交按钮 ---
                    st.divider()
                    submitted = st.form_submit_button("💾 提交本场结果", type="primary")

                    if submitted:
                        # 提交逻辑保持不变
                        
                        # 1. 简易积分计算
                        h_total = 0
                        a_total = 0
                        
                        # 记录每小局的胜者
                        res_v = "Home" if v_sh > v_sa else "Away"
                        res_c = "Home" if c_sh > c_sa else "Away"
                        res_g = "Home" if g_sh > g_sa else "Away"
                        
                        # 算分
                        if res_v == "Home": h_total += 10 
                        else: a_total += 10
                        
                        if res_c == "Home": h_total += 10
                        else: a_total += 10
                        
                        if res_g == "Home": h_total += 20
                        else: a_total += 20
                        
                        # 检查是否加赛
                        res_e = "None"
                        if h_total == 20 and a_total == 20:
                            # 20平，必须看加赛结果
                            if e_sh > e_sa: 
                                h_total += 10
                                res_e = "Home"
                            elif e_sa > e_sh: 
                                a_total += 10
                                res_e = "Away"
                            else:
                                st.error("比分 20-20，请录入加赛比分（不能是平局）！")
                                st.stop()
                        
                        # 2. 准备写入数据 (覆盖旧记录)
                        df_logs_cleaned = df_logs[df_logs['MatchID'] != match_id]
                        
                        new_rows = [
                            # Vanguard
                            {"MatchID": match_id, "Position": "Vanguard", "HomePlayer": v_hp, "HomeChar": v_hc, "AwayPlayer": v_ap, "AwayChar": v_ac, "Winner": res_v, "Score": f"{v_sh}-{v_sa}"},
                            # Center
                            {"MatchID": match_id, "Position": "Center", "HomePlayer": c_hp, "HomeChar": c_hc, "AwayPlayer": c_ap, "AwayChar": c_ac, "Winner": res_c, "Score": f"{c_sh}-{c_sa}"},
                            # General
                            {"MatchID": match_id, "Position": "General", "HomePlayer": g_hp, "HomeChar": g_hc, "AwayPlayer": g_ap, "AwayChar": g_ac, "Winner": res_g, "Score": f"{g_sh}-{g_sa}"},
                        ]
                        
                        if res_e != "None":
                             new_rows.append({"MatchID": match_id, "Position": "Extra", "HomePlayer": e_hp, "HomeChar": e_hc, "AwayPlayer": e_ap, "AwayChar": e_ac, "Winner": res_e, "Score": f"{e_sh}-{e_sa}"})
                             
                        df_new_logs = pd.concat([df_logs_cleaned, pd.DataFrame(new_rows)], ignore_index=True)
                        
                        # 3. 更新 Schedule 表
                        df_schedule.loc[df_schedule['MatchID'] == match_id, ['Status', 'HomeTotalPoints', 'AwayTotalPoints']] = ['Done', h_total, a_total]
                        
                        # 4. 执行写入
                        try:
                            # 假设 conn.update 函数存在
                            conn.update(worksheet="MatchLog", data=df_new_logs)
                            conn.update(worksheet="Schedule", data=df_schedule)
                            st.success(f"✅ 录入成功！{home_team} {h_total} - {a_total} {away_team}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"写入 Google Sheet 失败: {e}")

        except Exception as e:
            st.error(f"加载比赛列表时出错: {e}")
            st.code(e) # 打印错误方便调试

# ==============================================================================
# TAB 2: 积分榜
# ==============================================================================
with tab2:
    st.header("🏆 实时积分榜")
    
    # 简单的积分计算
    teams = df_config['Team'].unique() if 'Team' in df_config.columns else []
    if len(teams) == 0:
        st.warning("configs 表中未找到 Team 列")
    else:
        standings = []
        for team in teams:
            # 找到主场比赛
            home_matches = df_schedule[(df_schedule['HomeTeam'] == team) & (df_schedule['Status'] == 'Done')]
            home_pts = home_matches['HomeTotalPoints'].sum()
            
            # 找到客场比赛
            away_matches = df_schedule[(df_schedule['AwayTeam'] == team) & (df_schedule['Status'] == 'Done')]
            away_pts = away_matches['AwayTotalPoints'].sum()
            
            total_matches = len(home_matches) + len(away_matches)
            
            standings.append({
                "Team": team,
                "Points": home_pts + away_pts,
                "Matches": total_matches
            })
            
        df_rank = pd.DataFrame(standings).sort_values("Points", ascending=False).reset_index(drop=True)
        # 索引从1开始
        df_rank.index = df_rank.index + 1
        st.dataframe(df_rank, use_container_width=True)

# ==============================================================================
# TAB 3: 数据统计
# ==============================================================================
# 辅助函数：根据对局位置确定获胜得分
def get_battle_points(position):
    if position == 'Vanguard': return 10
    if position == 'Center': return 10
    if position == 'General': return 20
    if position == 'Extra': return 10
    return 0

with tab3:
    st.header("📊 数据统计")
    if not df_logs.empty:
        
        # --- 0. 数据预处理 (将 Home 和 Away 的数据合并到一起) ---
        
        # 0a. Home 侧数据处理
        df_home = df_logs[['HomePlayer', 'HomeChar', 'Position', 'Winner']].rename(
            columns={'HomePlayer': 'Player', 'HomeChar': 'Character'}
        )
        df_home['IsWin'] = df_home['Winner'] == 'Home'
        df_home['Points'] = df_home.apply(lambda row: get_battle_points(row['Position']) if row['IsWin'] else 0, axis=1)

        # 0b. Away 侧数据处理
        df_away = df_logs[['AwayPlayer', 'AwayChar', 'Position', 'Winner']].rename(
            columns={'AwayPlayer': 'Player', 'AwayChar': 'Character'}
        )
        df_away['IsWin'] = df_away['Winner'] == 'Away'
        df_away['Points'] = df_away.apply(lambda row: get_battle_points(row['Position']) if row['IsWin'] else 0, axis=1)

        # 0c. 合并数据并清洗 (过滤掉 Extra Match 里 "无" 的情况)
        df_combined = pd.concat([df_home, df_away], ignore_index=True)
        df_combined = df_combined[df_combined['Character'] != '无']

        
        # --- 1. 角色统计 (角色胜率和得分) ---
        st.subheader("角色表现分析")
        col1, col2 = st.columns(2)
        
        char_stats = df_combined.groupby('Character').agg(
            Total_Battles=('Player', 'size'),
            Wins=('IsWin', 'sum'),
            Total_Points=('Points', 'sum')
        ).reset_index()
        
        char_stats['Win Rate'] = (char_stats['Wins'] / char_stats['Total_Battles']).map('{:.1%}'.format)
        
        # 格式化和排序
        char_stats_display = char_stats.sort_values('Total_Points', ascending=False).rename(
            columns={'Character': '角色', 'Total_Battles': '总场次', 'Wins': '胜场', 'Total_Points': '总得分', 'Win Rate': '胜率'}
        )
        
        with col1:
            st.markdown("##### 胜率和得分")
            st.dataframe(char_stats_display, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("##### 角色出场率")
            st.bar_chart(char_stats.set_index('Character')['Total_Battles'])


        st.divider()
        
        # --- 2. 选手个人胜率 (Player Stats) ---
        st.subheader("选手胜率")
        
        player_stats = df_combined.groupby('Player').agg(
            Total_Battles=('Character', 'size'),
            Wins=('IsWin', 'sum')
        ).reset_index()
        
        player_stats['Win Rate'] = (player_stats['Wins'] / player_stats['Total_Battles']).map('{:.1%}'.format)
        
        # 格式化和排序 (按胜率降序)
        player_stats_display = player_stats.sort_values('Win Rate', ascending=False).rename(
            columns={'Player': '选手', 'Total_Battles': '总场次', 'Wins': '胜场', 'Win Rate': '胜率'}
        )

        st.dataframe(player_stats_display, use_container_width=True, hide_index=True)


        st.divider()

        # --- 3. 对局位置分析 (原始代码保留，稍作优化) ---
        st.subheader("对局位置胜率")
        
        position_wins = df_logs.groupby('Position')['Winner'].value_counts().unstack(fill_value=0)
        
        # 避免只有一侧数据时报错
        home_col = 'Home' if 'Home' in position_wins.columns else 0
        away_col = 'Away' if 'Away' in position_wins.columns else 0

        position_wins['Total'] = position_wins[home_col] + position_wins[away_col]
        
        # 确保分母不为零
        if (position_wins['Total'] > 0).any():
            position_wins['Home Win %'] = (position_wins[home_col] / position_wins['Total']).map('{:.1%}'.format)
        else:
            position_wins['Home Win %'] = '0.0%'
            
        position_wins = position_wins.rename(columns={home_col: '主场胜', away_col: '客场胜', 'Total': '总局数'})
        
        # 只显示需要的列
        st.dataframe(position_wins[['主场胜', '客场胜', '总局数', 'Home Win %']], use_container_width=True)

    else:
        st.info("暂无数据")

# ==============================================================================
# TAB 4: 历史战报
# ==============================================================================
with tab4:
    st.header("📜 历史对局查询")
    
    # 简单展示日志
    if not df_logs.empty:
        # 增加筛选功能
        filter_team = st.selectbox("筛选队伍", ["All"] + list(team_player_map.keys()))
        
        display_df = df_logs.copy()
        
        if filter_team != "All":
            # 这里逻辑稍微复杂，因为Log里没有队伍名。
            # 简单做法：先去schedule找这个队打过的MatchID
            team_match_ids = df_schedule[
                (df_schedule['HomeTeam'] == filter_team) | (df_schedule['AwayTeam'] == filter_team)
            ]['MatchID'].unique()
            display_df = display_df[display_df['MatchID'].isin(team_match_ids)]
            
        st.dataframe(
            display_df[['MatchID', 'Position', 'HomePlayer', 'Score', 'AwayPlayer', 'Winner']], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无记录")