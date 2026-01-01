import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# --- 1. DATABASE SETUP (The "Backend") ---
def init_db():
    conn = sqlite3.connect('gym.db')
    c = conn.cursor()
    
    # Create Tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, status TEXT, join_date DATE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY, member_id INTEGER, date DATE, time TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS finance
                 (id INTEGER PRIMARY KEY, type TEXT, amount REAL, description TEXT, date DATE)''')
    
    conn.commit()
    conn.close()

# Initialize DB on first run
init_db()

# --- 2. HELPER FUNCTIONS ---
def run_query(query, params=()):
    conn = sqlite3.connect('gym.db')
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def run_command(command, params=()):
    conn = sqlite3.connect('gym.db')
    c = conn.cursor()
    c.execute(command, params)
    conn.commit()
    conn.close()

# --- 3. APP INTERFACE (The "Frontend") ---
st.set_page_config(page_title="Iron Muscle Gym AI", layout="wide")
st.title("💪 Iron Muscle Gym Manager")

# Sidebar Navigation
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Members", "Attendance", "Finance"])

# --- DASHBOARD PAGE ---
if menu == "Dashboard":
    st.header("📊 Gym Analytics")
    
    # KPI Metrics
    members = run_query("SELECT * FROM members")
    finance = run_query("SELECT * FROM finance")
    
    total_members = len(members)
    active_members = len(members[members['status'] == 'Active'])
    
    income = finance[finance['type'] == 'Income']['amount'].sum()
    expense = finance[finance['type'] == 'Expense']['amount'].sum()
    profit = income - expense
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Members", total_members)
    col2.metric("Active Members", active_members)
    col3.metric("Total Profit", f"₹{profit}")
    
    # Simple "AI" Prediction (Rule-based)
    st.subheader("🤖 AI Insights")
    if profit < 0:
        st.error("⚠️ Warning: Expenses are higher than income. Suggestion: Launch a 'Summer Sale' to boost new joinings.")
    elif active_members < 10:
        st.warning("⚠️ Logic: Member count is low. Marketing campaign recommended.")
    else:
        st.success("✅ Business is healthy. Keep up the good work!")

# --- MEMBERS PAGE ---
elif menu == "Members":
    st.header("busts Member Management")
    
    # Add New Member Form
    with st.expander("Add New Member"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        status = st.selectbox("Status", ["Active", "Expired"])
        if st.button("Add Member"):
            run_command("INSERT INTO members (name, phone, status, join_date) VALUES (?, ?, ?, ?)", 
                        (name, phone, status, datetime.now().date()))
            st.success(f"Added {name}!")
            st.rerun()
            
    # Show List
    st.subheader("Member List")
    members_df = run_query("SELECT * FROM members")
    st.dataframe(members_df, use_container_width=True)

# --- ATTENDANCE PAGE ---
elif menu == "Attendance":
    st.header("📝 Daily Attendance")
    
    # Check-In System
    member_list = run_query("SELECT id, name FROM members WHERE status='Active'")
    if not member_list.empty:
        member_dict = dict(zip(member_list['name'], member_list['id']))
        selected_member = st.selectbox("Select Member", list(member_dict.keys()))
        
        if st.button("Mark Present"):
            m_id = member_dict[selected_member]
            run_command("INSERT INTO attendance (member_id, date, time) VALUES (?, ?, ?)", 
                        (m_id, datetime.now().date(), datetime.now().strftime("%H:%M:%S")))
            st.success(f"Marked {selected_member} as Present!")
    else:
        st.info("No active members found.")

    # Show Attendance Log
    st.subheader("Today's Logs")
    logs = run_query("""
        SELECT members.name, attendance.time 
        FROM attendance 
        JOIN members ON attendance.member_id = members.id
        WHERE attendance.date = ?
    """, (str(datetime.now().date()),))
    st.dataframe(logs, use_container_width=True)

# --- FINANCE PAGE ---
elif menu == "Finance":
    st.header("💰 Income & Expenses")
    
    # Add Transaction
    with st.form("finance_form"):
        f_type = st.selectbox("Type", ["Income", "Expense"])
        amount = st.number_input("Amount", min_value=0.0)
        desc = st.text_input("Description (e.g., Fees, Cleaning)")
        if st.form_submit_button("Add Transaction"):
            run_command("INSERT INTO finance (type, amount, description, date) VALUES (?, ?, ?, ?)", 
                        (f_type, amount, desc, datetime.now().date()))
            st.success("Saved!")
            st.rerun()

    # Financial Graph
    st.subheader("Financial Overview")
    fin_data = run_query("SELECT type, amount FROM finance")
    if not fin_data.empty:
        # Group by type for the chart
        chart_data = fin_data.groupby('type')['amount'].sum().reset_index()
        st.bar_chart(chart_data, x="type", y="amount", color="type")