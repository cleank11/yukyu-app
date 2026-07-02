import os
from datetime import datetime
import pandas as pd
import streamlit as st
import os
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# ====================================================================
# 🌐 あなたのGoogleスプレッドシートのURLを設定しました
# ====================================================================
URL_MASTER_ORIGINAL = "https://docs.google.com/spreadsheets/d/1rcyz61n9tHltstGWcZsOsb2sosGiZRgKPpBFIx4Bc-Y/edit?gid=0#gid=0"
URL_REQUESTS_ORIGINAL = "https://docs.google.com/spreadsheets/d/1Pa9KGK0VWxHw1u3XGPesc-f8-bQ6yre--9q6_9QfnRg/edit?gid=0#gid=0"

# 🔒 管理者用のパスワード設定
ADMIN_PASSWORD = "shacho-fujisan-2026"

MONTHS = [f"{i}月" for i in range(1, 12 + 1)]
CURRENT_YEAR = datetime.now().year
YEARS = [str(CURRENT_YEAR - i) for i in range(4)]


def convert_google_sheet_url(url):
    if "/edit" in url:
        base_url = url.split("/edit")[0]
        return base_url + "/gviz/tq?tqx=out:csv"
    return url


URL_MASTER = convert_google_sheet_url(URL_MASTER_ORIGINAL)
URL_REQUESTS = convert_google_sheet_url(URL_REQUESTS_ORIGINAL)


# --- 📥 データの読み込み ---
def load_master_data():
    try:
        df = pd.read_csv(URL_MASTER, encoding="utf-8")
        df.columns = df.columns.str.strip()

        # 💡 スプレッドシートが完全に空っぽ、または「社員名」の列がない場合の安全装置
        if df.empty or "社員名" not in df.columns:
            return create_default_master()

        df["入社日"] = pd.to_datetime(df["入社日"], errors="coerce").dt.date
        for y in YEARS:
            for m in MONTHS:
                col = f"{y}_{m}"
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(
                        0.0
                    )
        return df
    except Exception as e:
        return create_default_master()


def create_default_master():
    # スプレッドシートが空の時に使う初期データ
    base_cols = {
        "社員名": "山田 花子",
        "入社日": datetime.strptime(
            f"{CURRENT_YEAR-2}-04-01", "%Y-%m-%d"
        ).date(),
        "1年目消費日": 0.0,
        "2年目消費日": 0.0,
    }
    for y in YEARS:
        for m in MONTHS:
            base_cols[f"{y}_{m}"] = 13.0
    return pd.DataFrame([base_cols])


def load_requests_data():
    try:
        df = pd.read_csv(URL_REQUESTS, encoding="utf-8")
        df.columns = df.columns.str.strip()
        if df.empty or "💡申請ID" not in df.columns:
            return pd.DataFrame(
                columns=[
                    "申請ID",
                    "社員名",
                    "申請日",
                    "取得希望日数",
                    "ステータス",
                ]
            )
        return df
    except Exception as e:
        return pd.DataFrame(
            columns=["申請ID", "社員名", "申請日", "取得希望日数", "ステータス"]
        )


def save_all(df_master, df_req):
    df_m_save = df_master.copy()
    if "入社日" in df_m_save.columns:
        df_m_save["入社日"] = df_m_save["入社日"].astype(str)
    df_m_save.to_csv("backup_master.csv", index=False, encoding="utf-8-sig")
    df_req.to_csv("backup_requests.csv", index=False, encoding="utf-8-sig")
    st.info(
        "💡 クラウドへ一時的に反映されました。次のGitHub登録とWeb公開の完了後、スプレッドシートへリアルタイムに同期が開始されます！"
    )


df = load_master_data()
df_req = load_requests_data()


# 統計ロジック
def calculate_weekly_days_for_year(row, year):
    total_days = sum(row[f"{year}_{m}"] for m in MONTHS if f"{year}_{m}" in row)
    if total_days >= 217:
        return "週5日", total_days, 5
    elif total_days >= 169:
        return "週4日", total_days, 4
    elif total_days >= 121:
        return "週3日", total_days, 3
    elif total_days >= 73:
        return "週2日", total_days, 2
    elif total_days >= 48:
        return "週1日", total_days, 1
    else:
        return "週1日（少）", total_days, 1


GRANT_TABLE = {
    5: [10.0, 11.0, 12.0, 14.0, 16.0, 18.0, 20.0],
    4: [7.0, 8.0, 9.0, 10.0, 12.0, 13.0, 15.0],
    3: [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0],
    2: [3.0, 4.0, 4.0, 5.0, 6.0, 6.0, 7.0],
    1: [1.0, 2.0, 2.0, 2.0, 3.0, 3.0, 4.0],
}


def get_grant_days(weekly_code, missing_years_count):
    step = min(missing_years_count, 6)
    return GRANT_TABLE[weekly_code][step]


# --- 🔒 サイドバー認証 ---
st.sidebar.title("🔐 ログイン")
input_password = st.sidebar.text_input(
    "管理者用パスワード", type="password", help="一般社員の方は入力不要です"
)
is_admin = input_password == ADMIN_PASSWORD

if is_admin:
    st.sidebar.success("管理者モードでログイン中")
else:
    st.sidebar.info("【一般社員（申請者）モード】")

st.title("📅 有休管理システム ☁️クラウド連携版")

# タブ切り替え
if is_admin:
    tab1, tab_approve, tab2, tab3, tab4 = st.tabs(
        [
            "📊 有休確認・申請",
            "💮 有休の承認手続き（管理者限定）",
            "✍️ 過去3年〜今年の出勤入力",
            "👤 社員登録",
            "⚙️ 管理者データ",
        ]
    )
else:
    tab1 = st.tabs(["📊 自分の有休確認・申請"])[0]

# --- タブ1: 残数確認・有休申請 ---
with tab1:
    st.header("有休の確認と申請")

    if df.empty or ("社員名" not in df.columns):
        st.info("社員データを読み込めませんでした。")
    else:
        selected_emp = st.selectbox(
            "あなたのお名前を選択してください",
            df["社員名"].unique(),
            key="sb_request",
        )
        emp_data = df[df["社員名"] == selected_emp].iloc[0]

        today = datetime.now().date()
        hire_date = emp_data["入社日"]

        if pd.isna(hire_date):
            hire_date = today

        first_grant_date = hire_date + timedelta(days=182)
        second_grant_date = hire_date + timedelta(days=365 + 182)
        expire_date = first_grant_date + timedelta(days=730)

        hire_year = str(hire_date.year)
        if hire_year not in YEARS:
            hire_year = YEARS[-1]

        weeks_1st, total_days_1st, code_1st = calculate_weekly_days_for_year(
            emp_data, hire_year
        )
        prev_year = str(CURRENT_YEAR - 1)
        weeks_2nd, total_days_2nd, code_2nd = calculate_weekly_days_for_year(
            emp_data, prev_year
        )

        g_days_1st = get_grant_days(code_1st, 0)
        g_days_2nd = get_grant_days(code_2nd, 1)

        current_year_str = str(CURRENT_YEAR)
        weeks_now, total_days_now, code_now = calculate_weekly_days_for_year(
            emp_data, current_year_str
        )

        if today < first_grant_date:
            next_grant_date = first_grant_date
            next_grant_count = 0
        elif today < second_grant_date:
            next_grant_date = second_grant_date
            next_grant_count = 1
        else:
            years_passed = (today - hire_date).days // 365
            next_grant_date = hire_date + timedelta(days=(years_passed + 1) * 365)
            next_grant_count = years_passed

        estimated_next_grant_days = get_grant_days(code_now, next_grant_count)

        st.subheader(f"ℹ️ {selected_emp} さんの有休ステータス")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**入社日:** {hire_date}")
            st.write(f"**初年度({hire_year}年)の週換算:** {weeks_1st}")
            st.write(f"**前年度({prev_year}年)の週換算:** {weeks_2nd}")
        with col2:
            if today < first_grant_date:
                st.warning(f"次回付与予定日: {first_grant_date}")
            else:
                st.success(f"初年度付与日: {first_grant_date} ({g_days_1st}日)")
                if today >= second_grant_date:
                    st.success(f"2年度付与日: {second_grant_date} ({g_days_2nd}日)")

        is_expired_first_year = today >= expire_date
        current_1st_grant = 0.0 if is_expired_first_year else g_days_1st

        used_1st = pd.to_numeric(
            emp_data.get("1年目消費日", 0), errors="coerce"
        )
        if pd.isna(used_1st):
            used_1st = 0.0
        used_2nd = pd.to_numeric(
            emp_data.get("2年目消費日", 0), errors="coerce"
        )
        if pd.isna(used_2nd):
            used_2nd = 0.0

        current_1st_remain = max(0.0, current_1st_grant - used_1st)
        current_2nd_grant = g_days_2nd if today >= second_grant_date else 0.0
        current_2nd_remain = max(0.0, current_2nd_grant - used_2nd)
        total_remain = current_1st_remain + current_2nd_remain

        st.markdown("### 💡 現在使用可能な有給休暇残数")
        c1, c2, c3 = st.columns(3)
        c1.metric(label="総残日数", value=f"{total_remain} 日")
        if is_expired_first_year:
            c2.metric(label="1年目分", value="0.0 日 (期限切れ消滅)")
        else:
            c2.metric(label="1年目分（優先消化）", value=f"{current_1st_remain} 日")
        c3.metric(label="2年目分（最新）", value=f"{current_2nd_remain} 日")

        st.markdown("---")
        st.subheader("🔮 次回付与のシミュレーション（概算予測）")
        cx1, cx2 = st.columns(2)
        cx1.metric(label="次回付与の予定日", value=str(next_grant_date))
        cx2.metric(
            label="次回付与される日数（概算）",
            value=f"＋ {estimated_next_grant_days} 日",
        )

        st.markdown("---")
        st.subheader("📝 有休の取得申請")
        apply_days = st.number_input(
            "取得する日数（0.5日単位）",
            min_value=0.5,
            max_value=10.0,
            value=1.0,
            step=0.5,
        )

        if st.button("有休を申請する"):
            if apply_days > total_remain:
                st.error("残日数が足りません。")
            else:
                new_id = (
                    int(df_req["申請ID"].max()) + 1 if not df_req.empty else 1
                )
                new_request = pd.DataFrame(
                    [
                        {
                            "申請ID": new_id,
                            "社員名": selected_emp,
                            "申請日": str(today),
                            "取得希望日数": apply_days,
                            "ステータス": "承認待ち",
                        }
                    ]
                )
                df_req = pd.concat([df_req, new_request], ignore_index=True)
                save_all(df, df_req)
                st.success(
                    "申請が完了しました！管理者の承認をお待ちください。"
                )
                st.rerun()

        st.markdown("---")
        st.subheader("📋 あなたの申請履歴・結果")
        if not df_req.empty and ("社員名" in df_req.columns):
            my_reqs = df_req[df_req["社員名"] == selected_emp]
            if my_reqs.empty:
                st.caption("過去の申請履歴はありません。")
            else:
                st.dataframe(my_reqs, use_container_width=True)
        else:
            st
