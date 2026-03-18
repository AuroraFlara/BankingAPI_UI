import streamlit as st
import requests
import time
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Banking Research Portal", layout="centered")

# CSS 
st.markdown("""
<style>
    /* 1. Global Field Labels (Forms) */
    [data-testid="stWidgetLabel"] p {
        font-size: 1.2rem !important; /* Slightly bigger per previous request */
        font-weight: 600 !important;
        color: #262730;
    }
            
    /* 2. Dashboard Labels (Bold text like 'Full Name:') */
    .stMarkdown strong {
        font-size: 1.15rem !important;
    }

    /* 3. Dashboard Data Text */
    .stMarkdown p {
        font-size: 1.1rem !important;
        line-height: 1.2 !important; /* Tightened for the 'closer together' look */
        margin-bottom: 2px !important;
    }

    /* 4. Metric Styling (Available Balance 💵) */
    [data-testid="stMetricLabel"] p {
        font-size: 1.3rem !important; /* Bigger label for the Balance */
        font-weight: 700 !important;
        color: #262730 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important; /* Prominent Cash Amount */
    }

    /* 5. Form Padding & Spacing */
    div[data-testid="stForm"] > div {
        padding-top: 10px;
        padding-bottom: 10px;
    }
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] > div {
        padding-top: 5px;
        padding-bottom: 5px;
    }
        
    /* 6. Dividers (Standardized to your preferred 20px) */
    hr {
        margin-top: 20px !important;
        margin-bottom: 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for Experiment Control
st.sidebar.title("🔬 Experiment Control")
backend_choice = st.sidebar.selectbox(
    "Select Target Backend",
    ["Java Baseline", "Manual Python", "Claude Assisted", "Claude FullGenAI", "Codex Assisted", "Codex FullGenAI"]
)

URL_MAP = {
    "Java Baseline": "http://localhost:8180",
    "Manual Python": "http://127.0.0.1:8005",
    "Claude Assisted": "http://127.0.0.1:8004",
    "Claude FullGenAI": "http://127.0.0.1:8001",
    "Codex Assisted": "http://127.0.0.1:8003",
    "Codex FullGenAI": "http://127.0.0.1:8000"
}
BASE_URL = URL_MAP[backend_choice]

if 'token' not in st.session_state:
    st.session_state.token = None

# --- API HELPER ---
def api_call(method, endpoint, data=None):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
    url = f"{BASE_URL}{endpoint}"
    
    start_time = time.time()
    try:
        if method == "POST":
            res = requests.post(url, json=data, headers=headers)
        else:
            res = requests.get(url, headers=headers)
        
        duration = (time.time() - start_time) * 1000
        
        if res.status_code in [200, 201]:
            return res.json()
        else:
            st.error(f"Error {res.status_code}: {res.text}")
            return None
    except Exception as e:
        st.sidebar.error(f"Connection Failed: {e}")
        return None

# --- MAIN UI ---
st.title("🏦 Banking API Portal")

menu = ["User Management", "Account Security", "Financial Operations", "Dashboard"]
choice = st.selectbox("Select Category", menu)


# --- 1. USER MANAGEMENT (Stacked) ---
if choice == "User Management":
    st.info("### 1) Register User")
    with st.expander("Show Registration Form", expanded=True):
        with st.form("reg_form"):
            name = st.text_input("Full Name (e.g., Java_Test3)")
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")
            address = st.text_input("Address")
            phone = st.text_input("Phone Number")
            country = st.selectbox("Country Code", ["SG", "MY", "US", "UK"], index=0)
            
            if st.form_submit_button("Register"):
                payload = {
                    "name": name, 
                    "password": pwd, 
                    "email": email, 
                    "address": address, 
                    "phoneNumber": phone, 
                    "countryCode": country
                }
                res = api_call("POST", "/api/users/register", payload)
                if res: st.success(f"Success! Response: {res}")

    st.divider()
    st.success("### 2) Login")
    with st.expander("Show Login Form", expanded=True):
        # Renamed to Account Number as requested
        l_id = st.text_input("Account Number")
        l_pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            res = api_call("POST", "/api/users/login", {"identifier": l_id, "password": l_pw})
            if res:
                st.session_state.token = res.get("token")
                st.success("Authenticated! Token stored in session.")



# --- 2. ACCOUNT SECURITY ---
elif choice == "Account Security":
    st.subheader("🛡️ Account Security & PIN Management")
    
    # 6) Check PIN Created
    st.info("### 6) Check PIN Status")
    if st.button("Query PIN Status"):
        res = api_call("GET", "/api/account/pin/check")
        if res:
            # Displays a nice status message based on the boolean response
            is_created = res.get("isPinCreated")
            status = "✅ PIN is already set." if is_created else "❌ No PIN found. Please create one."
            st.write(status)

    st.divider()

    # Layout for Create and Update
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("### 4) Create PIN")
        with st.form("create_pin_form"):
            new_pin = st.text_input("New 4-Digit PIN", type="password", max_chars=4)
            v_pwd = st.text_input("Confirm Account Password", type="password", key="create_v_pwd")
            if st.form_submit_button("Submit Create"):
                payload = {"pin": new_pin, "password": v_pwd}
                res = api_call("POST", "/api/account/pin/create", payload)
                if res: st.success("PIN Created Successfully!")

    with col2:
        st.warning("### 5) Update PIN")
        with st.form("update_pin_form"):
            old_pin = st.text_input("Current PIN", type="password", max_chars=4)
            up_pin = st.text_input("New 4-Digit PIN", type="password", max_chars=4)
            # Added password field to match backend requirements
            up_pwd = st.text_input("Account Password", type="password", key="update_v_pwd")
            
            if st.form_submit_button("Submit Update"):
                payload = {
                    "oldPin": old_pin, 
                    "newPin": up_pin, 
                    "password": up_pwd
                }
                res = api_call("POST", "/api/account/pin/update", payload)
                if res: 
                    st.success("PIN Updated Successfully!")



# --- 3. FINANCIAL OPERATIONS ---
elif choice == "Financial Operations":
    st.subheader("💰 Financial Transaction Suite")

    # 7 & 8) Deposit and Withdraw
    # Grouped together as they share a similar JSON structure
    st.info("### 7 & 8) Cash Deposit / Withdrawal")
    with st.expander("Perform Cash Operation", expanded=True):
        with st.form("cash_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                op_type = st.radio("Select Action", ["Deposit", "Withdraw"], horizontal=True)
            with col_b:
                amt = st.number_input("Amount ($)", min_value=0, value=0, step=100)
            
            f_pin = st.text_input("Enter 4-Digit PIN", type="password", max_chars=4)
            
            if st.form_submit_button("Execute Transaction"):
                # Dynamically set path based on radio selection
                path = "/api/account/deposit" if op_type == "Deposit" else "/api/account/withdraw"
                res = api_call("POST", path, {"amount": amt, "pin": f_pin})
                if res: 
                    st.success(f"Success! {op_type} of ${amt} processed.")

    st.divider()

    # 9) Fund Transfer
    # Requires a target account number
    st.success("### 9) Internal Fund Transfer")
    with st.expander("Transfer to Another Account", expanded=True):
        with st.form("transfer_form"):
            target = st.text_input("Recipient Account Number")
            t_amt = st.number_input("Transfer Amount ($)", min_value=0, value=0, step=100)
            t_pin = st.text_input("Your 4-Digit PIN", type="password", max_chars=4)
            
            if st.form_submit_button("Confirm Transfer"):
                payload = {
                    "targetAccountNumber": target, 
                    "amount": t_amt, 
                    "pin": t_pin
                }
                res = api_call("POST", "/api/account/fund-transfer", payload)
                if res: 
                    st.success(f"Transfer of ${t_amt} to Account {target} successful!")

    st.divider()

    # 10) Transaction History
    # Fetches the history of all the operations performed above
    st.warning("### 10) Transaction History & Statement")
    if st.button("Fetch Statement"):
        res = api_call("GET", "/api/account/transactions")
        if res:
            transactions = res.get("transactions", [])
            if transactions:
                df = pd.DataFrame(transactions)
                # Cleanup: Format the date and filter relevant columns for a cleaner table
                if 'transactionDate' in df.columns:
                    df['transactionDate'] = pd.to_datetime(df['transactionDate']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Displaying using st.dataframe for sortable columns
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("No transactions found for this account.")



# --- 4. DASHBOARD ---
elif choice == "Dashboard":
    st.title("📊 Account Dashboard")
    
    # Refresh button to pull latest data for both sections
    if st.button("🔄 Refresh All Data"):
        st.rerun()

    st.divider()

    # Layout for User and Account Info
    col1, col2 = st.columns(2)

    # --- Section 1: User Details (Endpoint 3) ---
    with col1:
        st.markdown("### 3) User Profile 👤")
        user_res = api_call("GET", "/api/dashboard/user")
        
        if user_res and "user" in user_res:
            u = user_res["user"]
            with st.container(border=True):
                # Personal Information Sub-header
                st.markdown("##### 📝 Personal Info")
                
                # Separation of Country Code and Phone Number for clarity
                st.markdown(f"""
                **Full Name:** {u.get('name')}  
                **Email:** {u.get('email')}  
                **Address:** {u.get('address')}  
                **Country Code:** {u.get('countryCode')}  
                **Phone:** {u.get('phoneNumber')}
                """)
                
                st.divider()
                
                # Linked Account Info Sub-header
                st.markdown("##### 🔗 Linked Account")
                st.markdown(f"""
                **Account No:** `{u.get('accountNumber')}`  
                **Account Type:** {u.get('accountType')}  
                **Branch:** {u.get('branch')}  
                **IFSC Code:** `{u.get('ifscCode')}`
                """)
                
                st.divider()
                st.success(f"✔️ {user_res.get('msg')}")
        else:
            st.warning("Please log in to view User Details.")

    # --- Section 2: Account Details (Endpoint 11) ---
    with col2:
        st.markdown("### 11) Bank Account Detail 💳")
        acc_res = api_call("GET", "/api/dashboard/account")
        
        if acc_res and "account" in acc_res:
            a = acc_res["account"]
            with st.container(border=True):
                # 1. Metric with Cash Emoji
                raw_balance = a.get('balance')
                balance_display = f"${raw_balance:,}" if raw_balance is not None else "$0"
                
                st.metric("💵 Available Balance", balance_display)
                
                st.divider()
                
                # 2. Grouping details into ONE markdown block to remove gaps
                # The two spaces at the end of each line are key for tight line breaks
                st.markdown(f"""
                **Account Number:** `{a.get('accountNumber')}`  
                **Type:** {a.get('accountType')}  
                **Branch:** {a.get('branch')}  
                **IFSC Code:** `{a.get('ifscCode')}`
                """)
                
                st.divider()
                st.success(f"✔️ Status: {acc_res.get('msg')}")
        else:
            st.warning("No account data found. Are you logged in?")

    st.divider()

    # --- Section 3: Transaction History (Endpoint 10) ---
    st.markdown("### 10) Recent Activity 📝 ")
    if st.button("Fetch Transaction History"):
        res = api_call("GET", "/api/account/transactions")
        if res:
            transactions = res.get("transactions", [])
            if transactions:
                df = pd.DataFrame(transactions)
                display_df = df[['transactionDate', 'transactionType', 'amount', 'targetAccountNumber']].copy()
                display_df.columns = ['Date', 'Type', 'Amount ($)', 'Recipient']
                
                # FIXED: Updated use_container_width to width='stretch' for 2026 standards
                st.dataframe(display_df, width="stretch", hide_index=True)