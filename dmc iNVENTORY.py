import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib
import logging
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import time

# Set up logging
logging.basicConfig(filename='inventory.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DMCInventoryApp:
    def __init__(self):
        st.set_page_config(
            page_title="DMC Inventory Management System",
            page_icon="📦",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize database
        self.init_db()
        
        # Create main interface
        self.create_main_interface()
        
    def init_db(self):
        """Initialize the SQLite database with required tables"""
        self.conn = sqlite3.connect('dmc_inventory.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create IT Inventory table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS it_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assets_id TEXT UNIQUE,
                system_type TEXT,
                location TEXT,
                brand TEXT,
                model TEXT,
                serial_number TEXT UNIQUE,
                status TEXT,
                windows TEXT,
                config TEXT,
                warranty_status TEXT,
                last_audit_date TEXT,
                remarks TEXT
            )
        ''')
        
        # Create Inventory Tracker table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT,
                assets_id TEXT,
                system_type TEXT,
                location TEXT,
                brand TEXT,
                model TEXT,
                serial_number TEXT,
                status TEXT,
                windows TEXT,
                config TEXT,
                warranty_status TEXT,
                date_of_allocation TEXT,
                date_of_return TEXT,
                last_audit_date TEXT,
                phone_number TEXT,
                extra_allocated_item TEXT,
                FOREIGN KEY (assets_id) REFERENCES it_inventory (assets_id)
            )
        ''')
        
        # Create user table for authentication (simple implementation)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        ''')
        
        # Insert default admin user if not exists
        default_password = hashlib.sha256("admin123".encode()).hexdigest()
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash) 
            VALUES (?, ?)
        ''', ("admin", default_password))
        
        self.conn.commit()
        
    def create_main_interface(self):
        """Create the main application interface"""
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 2rem;
        }
        .section-header {
            font-size: 1.8rem;
            color: #34495e;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .success-box {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .error-box {
            background-color: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown('<h1 class="main-header">DMC Inventory Management System</h1>', unsafe_allow_html=True)
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["IT Inventory", "Inventory Tracker", "Reports", "Dashboard"])
        
        with tab1:
            self.build_it_inventory_section()
            
        with tab2:
            self.build_inventory_tracker_section()
            
        with tab3:
            self.build_reports_section()
            
        with tab4:
            self.build_dashboard_section()
        
        # Status bar equivalent
        st.sidebar.markdown("---")
        st.sidebar.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    def build_it_inventory_section(self):
        """Build the IT Inventory section"""
        st.markdown('<h2 class="section-header">IT Inventory Management</h2>', unsafe_allow_html=True)
        
        # Form for adding/editing items
        with st.expander("Add/Edit IT Inventory Item", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                assets_id = st.text_input("Assets ID*", key="it_assets_id")
                system_type = st.text_input("System Type", key="it_system_type")
                location = st.selectbox("Location", ["", "Indore", "Mumbai"], key="it_location")
                brand = st.text_input("Brand", key="it_brand")
                
            with col2:
                model = st.text_input("Model", key="it_model")
                serial_number = st.text_input("Serial Number*", key="it_serial_number")
                status = st.selectbox("Status", ["", "Available", "Allocated", "Under Maintenance"], key="it_status")
                windows = st.text_input("Windows", key="it_windows")
                
            with col3:
                config = st.text_input("Config", key="it_config")
                warranty_status = st.selectbox("Warranty Status", ["", "Active", "Expired", "No Warranty", "AMC"], key="it_warranty")
                last_audit_date = st.date_input("Last Audit Date", key="it_audit_date")
                remarks = st.text_area("Remarks", key="it_remarks")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("Add Item", type="primary", key="it_add_btn"):
                    self.add_it_item({
                        "Assets ID": assets_id, "System Type": system_type, "Location": location,
                        "Brand": brand, "Model": model, "Serial Number": serial_number,
                        "Status": status, "Windows": windows, "Config": config,
                        "Warranty Status": warranty_status, "Last Audit Date": last_audit_date.strftime("%Y-%m-%d") if last_audit_date else "",
                        "Remarks": remarks
                    })
            
            with col2:
                if st.button("Update Item", key="it_update_btn"):
                    st.info("Select an item from the table below to update")
            
            with col3:
                if st.button("Clear Form", key="it_clear_btn"):
                    st.rerun()
            
            with col4:
                if st.button("Export to Excel", key="it_export_btn"):
                    self.export_it_to_excel()
        
        # Search and filters
        st.subheader("IT Inventory Records")
        search_col, filter_col = st.columns([2, 1])
        
        with search_col:
            search_term = st.text_input("Search IT Inventory", placeholder="Search by any field...", key="it_search")
        
        with filter_col:
            status_filter = st.selectbox("Filter by Status", ["All", "Available", "Allocated", "Under Maintenance"], key="it_status_filter")
        
        # Display data
        self.display_it_inventory(search_term, status_filter)
    
    def add_it_item(self, item_data):
        """Add a new item to IT Inventory"""
        try:
            # Validate required fields
            if not item_data["Assets ID"] or not item_data["Serial Number"]:
                st.error("Assets ID and Serial Number are required")
                return
            
            # Insert into database
            self.cursor.execute('''
                INSERT INTO it_inventory 
                (assets_id, system_type, location, brand, model, serial_number, 
                 status, windows, config, warranty_status, last_audit_date, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_data["Assets ID"], item_data["System Type"], item_data["Location"],
                item_data["Brand"], item_data["Model"], item_data["Serial Number"],
                item_data["Status"], item_data["Windows"], item_data["Config"],
                item_data["Warranty Status"], item_data["Last Audit Date"], item_data["Remarks"]
            ))
            
            self.conn.commit()
            st.success("IT Item added successfully")
            logging.info(f"IT Item added: {item_data['Assets ID']}")
            
        except sqlite3.IntegrityError:
            st.error("Assets ID or Serial Number already exists")
        except Exception as e:
            st.error(f"Failed to add item: {str(e)}")
            logging.error(f"Error adding IT item: {str(e)}")
    
    def display_it_inventory(self, search_term="", status_filter="All"):
        """Display IT Inventory data with search and filter"""
        # Build query
        query = "SELECT * FROM it_inventory"
        params = []
        
        if search_term or status_filter != "All":
            query += " WHERE "
            conditions = []
            
            if search_term:
                conditions.append("(assets_id LIKE ? OR system_type LIKE ? OR location LIKE ? OR brand LIKE ? OR model LIKE ? OR serial_number LIKE ? OR status LIKE ?)")
                params.extend([f"%{search_term}%"] * 7)
            
            if status_filter != "All":
                if conditions:
                    conditions.append("AND status = ?")
                else:
                    conditions.append("status = ?")
                params.append(status_filter)
            
            query += " ".join(conditions)
        
        # Execute query
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        if not rows:
            st.info("No IT inventory items found")
            return
        
        # Convert to DataFrame
        columns = ["ID", "Assets ID", "System Type", "Location", "Brand", "Model", 
                  "Serial Number", "Status", "Windows", "Config", "Warranty Status", 
                  "Last Audit Date", "Remarks"]
        
        df = pd.DataFrame(rows, columns=columns)
        
        # Display data
        st.dataframe(
            df.drop(columns=["ID"]), 
            use_container_width=True,
            hide_index=True
        )
        
        # Show statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Items", len(df))
        with col2:
            st.metric("Available", len(df[df["Status"] == "Available"]))
        with col3:
            st.metric("Allocated", len(df[df["Status"] == "Allocated"]))
        with col4:
            st.metric("Under Maintenance", len(df[df["Status"] == "Under Maintenance"]))
    
    def export_it_to_excel(self):
        """Export IT Inventory to Excel"""
        try:
            # Get all data
            self.cursor.execute("SELECT * FROM it_inventory")
            rows = self.cursor.fetchall()
            
            # Create DataFrame
            columns = ["ID", "Assets ID", "System Type", "Location", "Brand", "Model", 
                      "Serial Number", "Status", "Windows", "Config", "Warranty Status", 
                      "Last Audit Date", "Remarks"]
            
            df = pd.DataFrame(rows, columns=columns)
            
            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='IT Inventory')
            
            # Download button
            st.download_button(
                label="Download IT Inventory Excel",
                data=output.getvalue(),
                file_name=f"IT_Inventory_Export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="it_download_btn"
            )
            
            logging.info("IT Inventory exported to Excel")
            
        except Exception as e:
            st.error(f"Failed to export data: {str(e)}")
            logging.error(f"Error exporting IT Inventory: {str(e)}")
    
    def build_inventory_tracker_section(self):
        """Build the Inventory Tracker section"""
        st.markdown('<h2 class="section-header">Inventory Tracker</h2>', unsafe_allow_html=True)
        
        # Form for adding/editing tracker records
        with st.expander("Add/Edit Inventory Record", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                employee_name = st.text_input("Employee Name*", key="tracker_employee")
                assets_id = st.text_input("Assets ID*", key="tracker_assets_id")
                system_type = st.text_input("System Type", key="tracker_system_type")
                location = st.selectbox("Location", ["", "Indore", "Mumbai"], key="tracker_location")
                
            with col2:
                brand = st.text_input("Brand", key="tracker_brand")
                model = st.text_input("Model", key="tracker_model")
                serial_number = st.text_input("Serial Number", key="tracker_serial_number")
                status = st.selectbox("Status", ["", "Allocated", "Returned", "Pending Return"], key="tracker_status")
                
            with col3:
                windows = st.text_input("Windows", key="tracker_windows")
                config = st.text_input("Config", key="tracker_config")
                warranty_status = st.selectbox("Warranty Status", ["", "Active", "Expired", "No Warranty", "AMC"], key="tracker_warranty")
                phone_number = st.text_input("Phone Number", key="tracker_phone")
            
            col1, col2 = st.columns(2)
            with col1:
                date_of_allocation = st.date_input("Date of Allocation", key="tracker_alloc_date")
            with col2:
                date_of_return = st.date_input("Date of Return", key="tracker_return_date")
            
            extra_allocated_item = st.text_area("Extra Allocated Item", key="tracker_extra_item")
            last_audit_date = st.date_input("Last Audit Date", key="tracker_audit_date")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("Add Record", type="primary", key="tracker_add_btn"):
                    self.add_tracker_record({
                        "Employee Name": employee_name, "Assets ID": assets_id, 
                        "System Type": system_type, "Location": location,
                        "Brand": brand, "Model": model, "Serial Number": serial_number,
                        "Status": status, "Windows": windows, "Config": config,
                        "Warranty Status": warranty_status, 
                        "Date of Allocation": date_of_allocation.strftime("%Y-%m-%d") if date_of_allocation else "",
                        "Date of Return": date_of_return.strftime("%Y-%m-%d") if date_of_return else "",
                        "Last Audit Date": last_audit_date.strftime("%Y-%m-%d") if last_audit_date else "",
                        "Phone Number": phone_number, "Extra Allocated Item": extra_allocated_item
                    })
            
            with col2:
                if st.button("Update Record", key="tracker_update_btn"):
                    st.info("Select a record from the table below to update")
            
            with col3:
                if st.button("Clear Form", key="tracker_clear_btn"):
                    st.rerun()
            
            with col4:
                if st.button("Export to Excel", key="tracker_export_btn"):
                    self.export_tracker_to_excel()
        
        # Search and filters
        st.subheader("Inventory Records")
        search_col, filter_col = st.columns([2, 1])
        
        with search_col:
            search_term = st.text_input("Search Inventory Records", placeholder="Search by any field...", key="tracker_search")
        
        with filter_col:
            status_filter = st.selectbox("Filter by Status", ["All", "Allocated", "Returned", "Pending Return"], key="tracker_status_filter")
        
        # Display data
        self.display_inventory_tracker(search_term, status_filter)
    
    def add_tracker_record(self, record_data):
        """Add a new record to Inventory Tracker"""
        try:
            # Validate required fields
            if not record_data["Employee Name"] or not record_data["Assets ID"]:
                st.error("Employee Name and Assets ID are required")
                return
            
            # Insert into database
            self.cursor.execute('''
                INSERT INTO inventory_tracker 
                (employee_name, assets_id, system_type, location, brand, model, 
                 serial_number, status, windows, config, warranty_status, 
                 date_of_allocation, date_of_return, last_audit_date, 
                 phone_number, extra_allocated_item)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record_data["Employee Name"], record_data["Assets ID"], record_data["System Type"],
                record_data["Location"], record_data["Brand"], record_data["Model"],
                record_data["Serial Number"], record_data["Status"], record_data["Windows"],
                record_data["Config"], record_data["Warranty Status"], record_data["Date of Allocation"],
                record_data["Date of Return"], record_data["Last Audit Date"], record_data["Phone Number"],
                record_data["Extra Allocated Item"]
            ))
            
            self.conn.commit()
            st.success("Inventory Record added successfully")
            logging.info(f"Inventory Record added for: {record_data['Employee Name']}")
            
        except Exception as e:
            st.error(f"Failed to add record: {str(e)}")
            logging.error(f"Error adding inventory record: {str(e)}")
    
    def display_inventory_tracker(self, search_term="", status_filter="All"):
        """Display Inventory Tracker data with search and filter"""
        # Build query
        query = "SELECT * FROM inventory_tracker"
        params = []
        
        if search_term or status_filter != "All":
            query += " WHERE "
            conditions = []
            
            if search_term:
                conditions.append("(employee_name LIKE ? OR assets_id LIKE ? OR system_type LIKE ? OR location LIKE ? OR brand LIKE ? OR model LIKE ? OR serial_number LIKE ? OR status LIKE ?)")
                params.extend([f"%{search_term}%"] * 8)
            
            if status_filter != "All":
                if conditions:
                    conditions.append("AND status = ?")
                else:
                    conditions.append("status = ?")
                params.append(status_filter)
            
            query += " ".join(conditions)
        
        # Execute query
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        if not rows:
            st.info("No inventory records found")
            return
        
        # Convert to DataFrame
        columns = ["ID", "Employee Name", "Assets ID", "System Type", "Location", "Brand", "Model", 
                  "Serial Number", "Status", "Windows", "Config", "Warranty Status", 
                  "Date of Allocation", "Date of Return", "Last Audit Date", "Phone Number", 
                  "Extra Allocated Item"]
        
        df = pd.DataFrame(rows, columns=columns)
        
        # Display data
        st.dataframe(
            df.drop(columns=["ID"]), 
            use_container_width=True,
            hide_index=True
        )
        
        # Show statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Allocated", len(df[df["Status"] == "Allocated"]))
        with col3:
            st.metric("Returned", len(df[df["Status"] == "Returned"]))
        with col4:
            st.metric("Pending Return", len(df[df["Status"] == "Pending Return"]))
    
    def export_tracker_to_excel(self):
        """Export Inventory Tracker to Excel"""
        try:
            # Get all data
            self.cursor.execute("SELECT * FROM inventory_tracker")
            rows = self.cursor.fetchall()
            
            # Create DataFrame
            columns = ["ID", "Employee Name", "Assets ID", "System Type", "Location", "Brand", "Model", 
                      "Serial Number", "Status", "Windows", "Config", "Warranty Status", 
                      "Date of Allocation", "Date of Return", "Last Audit Date", "Phone Number", 
                      "Extra Allocated Item"]
            
            df = pd.DataFrame(rows, columns=columns)
            
            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Inventory Tracker')
            
            # Download button
            st.download_button(
                label="Download Inventory Tracker Excel",
                data=output.getvalue(),
                file_name=f"Inventory_Tracker_Export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="tracker_download_btn"
            )
            
            logging.info("Inventory Tracker exported to Excel")
            
        except Exception as e:
            st.error(f"Failed to export data: {str(e)}")
            logging.error(f"Error exporting Inventory Tracker: {str(e)}")
    
    def build_reports_section(self):
        """Build the Reports section"""
        st.markdown('<h2 class="section-header">Reports & Analytics</h2>', unsafe_allow_html=True)
        
        # Report options
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                "Select Report Type",
                ["Asset Summary Report", "Allocation History", "Warranty Expiry Report", 
                 "Maintenance Schedule", "Audit Trail Report"],
                key="report_type"
            )
            
            date_range = st.date_input(
                "Select Date Range",
                value=(datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()),
                max_value=datetime.date.today(),
                help="Select start and end date for the report",
                key="report_date_range"
            )
        
        with col2:
            export_format = st.radio(
                "Export Format",
                ["PDF", "Excel", "CSV"],
                horizontal=True,
                key="export_format"
            )
            
            if st.button("Generate Report", type="primary", key="generate_report_btn"):
                self.generate_report(report_type, date_range, export_format)
        
        # Report preview area
        st.subheader("Report Preview")
        st.info("Report preview will be shown here after generation")
    
    def generate_report(self, report_type, date_range, export_format):
        """Generate a report based on selected options"""
        try:
            # Simulate report generation
            with st.spinner(f"Generating {report_type}..."):
                time.sleep(2)  # Simulate processing time
                
                # Display report summary
                st.success(f"{report_type} generated successfully!")
                
                # Show sample report data
                if report_type == "Asset Summary Report":
                    self.cursor.execute("SELECT status, COUNT(*) FROM it_inventory GROUP BY status")
                    status_data = self.cursor.fetchall()
                    
                    if status_data:
                        status_df = pd.DataFrame(status_data, columns=["Status", "Count"])
                        fig = px.pie(status_df, values="Count", names="Status", title="Asset Status Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif report_type == "Allocation History":
                    self.cursor.execute("SELECT employee_name, assets_id, date_of_allocation FROM inventory_tracker ORDER BY date_of_allocation DESC LIMIT 10")
                    allocation_data = self.cursor.fetchall()
                    
                    if allocation_data:
                        allocation_df = pd.DataFrame(allocation_data, columns=["Employee", "Asset ID", "Allocation Date"])
                        st.dataframe(allocation_df, use_container_width=True)
                
                # Download button
                st.download_button(
                    label=f"Download {report_type} as {export_format}",
                    data=f"Sample {report_type} content in {export_format} format",
                    file_name=f"{report_type.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.{export_format.lower()}",
                    mime="application/octet-stream",
                    key="report_download_btn"
                )
                
                logging.info(f"Report generated: {report_type}")
                
        except Exception as e:
            st.error(f"Failed to generate report: {str(e)}")
            logging.error(f"Error generating report: {str(e)}")
    
    def build_dashboard_section(self):
        """Build the Dashboard section"""
        st.markdown('<h2 class="section-header">Dashboard Overview</h2>', unsafe_allow_html=True)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.cursor.execute("SELECT COUNT(*) FROM it_inventory")
            total_assets = self.cursor.fetchone()[0]
            st.metric("Total Assets", total_assets)
        
        with col2:
            self.cursor.execute("SELECT COUNT(*) FROM it_inventory WHERE status = 'Available'")
            available_assets = self.cursor.fetchone()[0]
            st.metric("Available Assets", available_assets)
        
        with col3:
            self.cursor.execute("SELECT COUNT(*) FROM inventory_tracker WHERE status = 'Allocated'")
            allocated_assets = self.cursor.fetchone()[0]
            st.metric("Allocated Assets", allocated_assets)
        
        with col4:
            self.cursor.execute("SELECT COUNT(DISTINCT employee_name) FROM inventory_tracker")
            total_employees = self.cursor.fetchone()[0]
            st.metric("Employees with Assets", total_employees)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Asset status chart
            self.cursor.execute("SELECT status, COUNT(*) FROM it_inventory GROUP BY status")
            status_data = self.cursor.fetchall()
            
            if status_data:
                status_df = pd.DataFrame(status_data, columns=["Status", "Count"])
                fig = px.pie(status_df, values="Count", names="Status", title="Asset Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Location distribution chart
            self.cursor.execute("SELECT location, COUNT(*) FROM it_inventory GROUP BY location")
            location_data = self.cursor.fetchall()
            
            if location_data:
                location_df = pd.DataFrame(location_data, columns=["Location", "Count"])
                fig = px.bar(location_df, x="Location", y="Count", title="Assets by Location")
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.subheader("Recent Allocations")
        self.cursor.execute("""
            SELECT employee_name, assets_id, date_of_allocation, status 
            FROM inventory_tracker 
            ORDER BY date_of_allocation DESC 
            LIMIT 10
        """)
        recent_activity = self.cursor.fetchall()
        
        if recent_activity:
            activity_df = pd.DataFrame(recent_activity, columns=["Employee", "Asset ID", "Allocation Date", "Status"])
            st.dataframe(activity_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent allocation activity")

# Main application
if __name__ == "__main__":
    app = DMCInventoryApp()