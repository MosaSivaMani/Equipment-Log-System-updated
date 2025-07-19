import streamlit as st
import sqlite3

DB_PATH = 'log.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Ensure DB and table exist on startup
init_db()

def get_equipment():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM equipment")
    rows = c.fetchall()
    conn.close()
    return rows

def add_equipment(name, model, location, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO equipment (name, model, location, date) VALUES (?, ?, ?, ?)",
              (name, model, location, date))
    conn.commit()
    conn.close()

st.title("Equipment Log System")

st.header("Add New Equipment")
with st.form("add_form"):
    name = st.text_input("Equipment Name")
    model = st.text_input("Model")
    location = st.text_input("Location")
    date = st.date_input("Date")
    submitted = st.form_submit_button("Add")
    if submitted:
        add_equipment(name, model, location, str(date))
        st.success("Equipment added!")

st.header("Equipment List")
equipment = get_equipment()
if equipment:
    st.table(equipment)
else:
    st.write("No equipment found.") 