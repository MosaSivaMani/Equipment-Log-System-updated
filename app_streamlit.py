import streamlit as st
import sqlite3
from fpdf import FPDF
import tempfile
import pandas as pd
import datetime
import io
import altair as alt

DB_PATH = 'log.db'

# --- DB Functions ---
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

def delete_equipment(equipment_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
    conn.commit()
    conn.close()

def update_equipment(equipment_id, name, model, location, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE equipment SET name = ?, model = ?, location = ?, date = ? WHERE id = ?",
              (name, model, location, date, equipment_id))
    conn.commit()
    conn.close()

def generate_pdf(equipment):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Equipment Log", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(40, 10, "Name", 1)
    pdf.cell(40, 10, "Model", 1)
    pdf.cell(40, 10, "Location", 1)
    pdf.cell(40, 10, "Date", 1)
    pdf.ln()
    for eq in equipment:
        pdf.cell(40, 10, str(eq[1]), 1)
        pdf.cell(40, 10, str(eq[2]), 1)
        pdf.cell(40, 10, str(eq[3]), 1)
        pdf.cell(40, 10, str(eq[4]), 1)
        pdf.ln()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    tmp_file.seek(0)
    return tmp_file

init_db()

# --- Sidebar Navigation ---
st.set_page_config(page_title="Equipment Log System", page_icon="🛠️", layout="wide")

st.sidebar.image("https://img.icons8.com/color/96/000000/toolbox.png", width=64)
st.sidebar.title("Equipment Log System")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Equipment", "Equipment List", "Export"]
)
st.sidebar.markdown("---")

# --- Header Bar ---
st.markdown(
    """
    <div style='background-color: #FF9800; padding: 1rem 0 0.5rem 0; border-radius: 0 0 16px 16px; margin-bottom: 1.5rem;'>
        <h1 style='color: white; text-align: center; margin-bottom: 0;'>🛠️ Equipment Log System</h1>
        <p style='color: #fffbe7; text-align: center; margin-top: 0.2rem;'>A modern dashboard to manage your equipment records.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Dashboard Page ---
def dashboard_page():
    st.subheader("📊 Dashboard Overview")
    # Add Equipment Button
    if 'show_add_form' not in st.session_state:
        st.session_state['show_add_form'] = False
    if st.button('➕ Add Equipment'):
        st.session_state['show_add_form'] = not st.session_state['show_add_form']
    if st.session_state['show_add_form']:
        with st.form("dashboard_add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Equipment Name", key="dash_name", help="Enter the name of the equipment.")
                model = st.text_input("Model", key="dash_model", help="Enter the model number or type.")
            with col2:
                location = st.text_input("Location", key="dash_location", help="Where is this equipment located?")
                date = st.date_input("Date", key="dash_date", help="Date of entry or last maintenance.")
            submitted = st.form_submit_button("Add Equipment")
            if submitted:
                if name and model and location and date:
                    add_equipment(name, model, location, str(date))
                    st.success("✅ Equipment added!")
                    st.session_state['show_add_form'] = False
                    st.experimental_rerun()
                else:
                    st.warning("Please fill in all fields.")
    equipment = get_equipment()
    if equipment:
        df = pd.DataFrame(equipment, columns=["ID", "Name", "Model", "Location", "Date"])
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        invalid_rows = df[df["Date"].isna()]
        df = df.dropna(subset=["Date"])
        df = df.sort_values(by="Date", ascending=False)
        today = datetime.date.today()
        this_month = today.month
        this_year = today.year
        # --- Key Metrics ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Equipment", len(df))
        col2.metric("Unique Models", df["Model"].nunique())
        col3.metric("Unique Locations", df["Location"].nunique())
        st.markdown("---")
        # --- Most Common Model/Location ---
        if not df.empty:
            most_common_model = df["Model"].mode()[0]
            most_common_location = df["Location"].mode()[0]
            st.write(f"**Most Common Model:** {most_common_model}")
            st.write(f"**Most Common Location:** {most_common_location}")
        # --- Equipment Added This Week/Month ---
        week_start = today - datetime.timedelta(days=today.weekday())
        added_this_week = df[df["Date"].dt.date >= week_start].shape[0]
        added_this_month = df[(df["Date"].dt.month == this_month) & (df["Date"].dt.year == this_year)].shape[0]
        st.write(f"**Added This Week:** {added_this_week}")
        st.write(f"**Added This Month:** {added_this_month}")
        # --- Oldest/Newest Entry ---
        if not df.empty:
            oldest = df.iloc[-1]
            newest = df.iloc[0]
            st.write(f"**Oldest Entry:** {oldest['Name']} ({oldest['Date'].date()})")
            st.write(f"**Newest Entry:** {newest['Name']} ({newest['Date'].date()})")
        st.markdown("---")
        # --- In-place Bar and Pie Charts for Model and Location ---
        st.markdown("#### 📊 Equipment Distribution by Model and Location")
        model_counts = df["Model"].value_counts().reset_index()
        model_counts.columns = ["Model", "Count"]
        location_counts = df["Location"].value_counts().reset_index()
        location_counts.columns = ["Location", "Count"]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**By Model**")
            bar_chart_model = alt.Chart(model_counts).mark_bar(color='#FF9800').encode(
                x=alt.X('Model', sort='-y'),
                y='Count'
            ).properties(height=300)
            st.altair_chart(bar_chart_model, use_container_width=True)
            pie_chart_model = alt.Chart(model_counts).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Model", type="nominal")
            )
            st.altair_chart(pie_chart_model, use_container_width=True)
            st.dataframe(model_counts, use_container_width=True)
        with col2:
            st.markdown("**By Location**")
            bar_chart_loc = alt.Chart(location_counts).mark_bar(color='#42a5f5').encode(
                x=alt.X('Location', sort='-y'),
                y='Count'
            ).properties(height=300)
            st.altair_chart(bar_chart_loc, use_container_width=True)
            pie_chart_loc = alt.Chart(location_counts).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Location", type="nominal")
            )
            st.altair_chart(pie_chart_loc, use_container_width=True)
            st.dataframe(location_counts, use_container_width=True)
        st.markdown("---")
        # --- Line Chart: Equipment Added Per Month ---
        st.markdown("#### 📈 Equipment Added Per Month")
        df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
        month_counts = df.groupby("YearMonth").size().reset_index(name="Count")
        line_chart = alt.Chart(month_counts).mark_line(point=True, color="#FF9800").encode(
            x=alt.X("YearMonth", title="Month"),
            y=alt.Y("Count", title="Equipment Added")
        ).properties(width=700, height=400)
        st.altair_chart(line_chart, use_container_width=True)
        st.markdown("---")
        # --- Recent Activity ---
        st.markdown("#### 🕒 Recent Activity")
        recent = df.head(5).drop("ID", axis=1)
        st.table(recent)
        # --- Highlight Invalid Data ---
        if not invalid_rows.empty:
            st.warning(f"There are {len(invalid_rows)} equipment records with invalid or missing dates. These are not shown in the statistics above.")
            st.dataframe(invalid_rows)
    else:
        st.info("No equipment data available.")

# --- Add Equipment Page ---
def add_equipment_page():
    st.subheader("➕ Add New Equipment")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Equipment Name", help="Enter the name of the equipment.")
            model = st.text_input("Model", help="Enter the model number or type.")
        with col2:
            location = st.text_input("Location", help="Where is this equipment located?")
            date = st.date_input("Date", help="Date of entry or last maintenance.")
        submitted = st.form_submit_button("Add Equipment")
        if submitted:
            if name and model and location and date:
                add_equipment(name, model, location, str(date))
                st.success("✅ Equipment added!")
            else:
                st.warning("Please fill in all fields.")

# --- Equipment List Page ---
def equipment_list_page():
    st.subheader("📋 Equipment List")
    equipment = get_equipment()
    if equipment:
        df = pd.DataFrame(equipment, columns=["ID", "Name", "Model", "Location", "Date"])
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df = df.sort_values(by="Date", ascending=False)
        # Filters
        with st.expander("🔎 Filters", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                name_filter = st.text_input("Name")
            with col2:
                model_filter = st.text_input("Model")
            with col3:
                location_filter = st.text_input("Location")
            with col4:
                min_date = df["Date"].min().date()
                max_date = df["Date"].max().date()
                start_date, end_date = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
        mask = (
            (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
            & (df["Name"].str.contains(name_filter, case=False, na=False))
            & (df["Model"].str.contains(model_filter, case=False, na=False))
            & (df["Location"].str.contains(location_filter, case=False, na=False))
        )
        filtered_df = df.loc[mask].reset_index(drop=True)
        st.markdown("---")
        # Table with Edit/Delete buttons in each row
        for idx, row in filtered_df.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2,2,2,2,1,1])
            c1.write(row['Name'])
            c2.write(row['Model'])
            c3.write(row['Location'])
            c4.write(row['Date'].date())
            edit_key = f"edit_{row['ID']}"
            delete_key = f"delete_{row['ID']}"
            if c5.button("Edit", key=edit_key):
                st.session_state[edit_key] = True
            if c6.button("Delete", key=delete_key):
                st.session_state[f"delete_confirm_{row['ID']}"] = True
            # Inline edit form
            if st.session_state.get(edit_key, False):
                with st.form(f"edit_form_{row['ID']}"):
                    new_name = st.text_input("Equipment Name", value=row['Name'])
                    new_model = st.text_input("Model", value=row['Model'])
                    new_location = st.text_input("Location", value=row['Location'])
                    new_date = st.date_input("Date", value=row['Date'])
                    save = st.form_submit_button("Save Changes")
                    cancel = st.form_submit_button("Cancel")
                    if save:
                        update_equipment(row['ID'], new_name, new_model, new_location, str(new_date))
                        st.success("✅ Equipment updated!")
                        st.session_state[edit_key] = False
                        st.experimental_rerun()
                    if cancel:
                        st.session_state[edit_key] = False
                        st.experimental_rerun()
            # Inline delete confirmation
            if st.session_state.get(f"delete_confirm_{row['ID']}", False):
                st.warning("Are you sure you want to delete this record?", icon="⚠️")
                confirm = st.button("Yes, Delete", key=f"confirm_delete_{row['ID']}")
                cancel_del = st.button("Cancel", key=f"cancel_delete_{row['ID']}")
                if confirm:
                    delete_equipment(row['ID'])
                    st.success("🗑️ Equipment deleted!")
                    st.session_state[f"delete_confirm_{row['ID']}"] = False
                    st.experimental_rerun()
                if cancel_del:
                    st.session_state[f"delete_confirm_{row['ID']}"] = False
                    st.experimental_rerun()
        st.markdown("---")
        st.dataframe(filtered_df.drop("ID", axis=1), use_container_width=True, height=600)
    else:
        st.info("No equipment found. Add some above!")

# --- Export Page ---
def export_page():
    st.subheader("⬇️ Export Equipment Data")
    equipment = get_equipment()
    if equipment:
        df = pd.DataFrame(equipment, columns=["ID", "Name", "Model", "Location", "Date"])
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df = df.sort_values(by="Date", ascending=False)
        # PDF Export
        if st.button("Export All to PDF"):
            tmp_file = generate_pdf(equipment)
            with open(tmp_file.name, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name="equipment_log.pdf",
                    mime="application/pdf"
                )
        # CSV Export
        csv_buffer = io.StringIO()
        df.drop("ID", axis=1).to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download All as CSV",
            data=csv_buffer.getvalue(),
            file_name="equipment_log.csv",
            mime="text/csv"
        )
    else:
        st.info("No equipment data to export.")

# --- Main Page Routing ---
if page == "Dashboard":
    dashboard_page()
elif page == "Add Equipment":
    add_equipment_page()
elif page == "Equipment List":
    equipment_list_page()
elif page == "Export":
    export_page()

# --- Footer ---
st.markdown(
    """
    <hr style='margin-top:2rem;margin-bottom:0.5rem;border:1px solid #FF9800;'>
    <div style='text-align:center;color:#888;font-size:0.9em;'>
        &copy; 2025 Equipment Log System &mdash; Powered by Streamlit
    </div>
    """,
    unsafe_allow_html=True
) 