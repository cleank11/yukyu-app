# yukyu-app
有給管理ソフト（Streamlit + Google スプレッドシート）

## セットアップ

### 必要な設定値（secrets）

パスワードやスプレッドシートのURLはソースコードに書かず、Streamlit の secrets または環境変数で渡します。

| キー | 内容 | 未設定時の動作 |
| --- | --- | --- |
| `ADMIN_PASSWORD` | 管理者画面のパスワード | 管理者機能が無効になり、一般社員モードのみ使用可能 |
| `URL_MASTER` | 社員マスタのスプレッドシートURL | エラーを表示してアプリを停止 |
| `URL_REQUESTS` | 申請履歴のスプレッドシートURL | エラーを表示してアプリを停止 |

読み込み順は `st.secrets` → 環境変数 です。

### ローカルで動かす場合

```bash
pip install streamlit pandas
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# .streamlit/secrets.toml を編集して実際の値を入れる
streamlit run app.py
```

`.streamlit/secrets.toml` は `.gitignore` に登録済みです。**実際の値は絶対にコミットしないでください。**

環境変数で渡す場合:

```bash
ADMIN_PASSWORD='...' URL_MASTER='https://...' URL_REQUESTS='https://...' streamlit run app.py
```

### Streamlit Community Cloud で動かす場合

アプリの **Settings → Secrets** に、`secrets.toml.example` と同じ形式で値を貼り付けてください。
