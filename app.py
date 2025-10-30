import streamlit as st
import json
import base64
import pandas as pd
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Document Validation Workflow",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .doc-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        color: white;
    }
    .checklist-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        color: white;
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    h1 {
        color: #1e293b;
        font-weight: 700;
    }
    .feature-section {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    .feature-heading {
        font-size: 1.2rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    .feature-item {
        background: white;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        border: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .feature-key {
        font-weight: 600;
        color: #475569;
        flex: 0 0 40%;
    }
    .feature-value {
        color: #1e293b;
        flex: 1;
        text-align: right;
    }
    .pdf-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        z-index: 9999;
        display: flex;
        flex-direction: column;
    }
    .pdf-header {
        background: #1e293b;
        color: white;
        padding: 1rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .pdf-content {
        flex: 1;
        overflow: auto;
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# File paths configuration
FILE_PATHS = {
    "airwaybill": {
        "pdf": r"BTS30161036 HAWB.pdf",
        "json": r"BTS30161036 HAWB_output.json"
    },
    "invoice": {
        "pdf": r"BTS30161036 inv.pdf",
        "json": r"BTS30161036 inv_output.json"
    },
    "packinglist": {
        "pdf": r"BTS30161036 pl.pdf",
        "json": r"BTS30161036 pl_output.json"
    },
    "original_checklist": {
        "pdf": r"BTS30161036 checklist.pdf",
        "json": r"BTS30161036 checklist_original.json"
    },
    "generated_checklist": {
        "pdf": r"genChecklist.pdf",
        "json": r"BTS30161036 checklist_output.json"
    }
}



# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'documents'
if 'viewing_pdf' not in st.session_state:
    st.session_state.viewing_pdf = None
if 'viewing_json' not in st.session_state:
    st.session_state.viewing_json = None

# Helper functions
def load_json(file_path):
    """Load and return JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}

def display_pdf_modal(file_path, title):
    """Display PDF in a full-screen modal"""
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        st.markdown(f"### 📄 {title}")
        
        col1, col2, col3 = st.columns([1, 6, 1])
        with col2:
            if st.button("❌ Close PDF Viewer", key="close_pdf", use_container_width=True, type="secondary"):
                st.session_state.viewing_pdf = None
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display PDF with full width
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf" style="border: none; border-radius: 8px;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.error(f"PDF file not found: {file_path}")
    except Exception as e:
        st.error(f"Error loading PDF: {str(e)}")

def format_value(value):
    """Format value for display"""
    if isinstance(value, bool):
        return "✅ Yes" if value else "❌ No"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return value
    elif isinstance(value, list):
        return ", ".join(str(v) for v in value)
    else:
        return str(value)


def flatten_json_to_table(data):
    """Convert nested JSON to a flat list of rows for tabular display"""
    rows = []
    
    for key, value in data.items():
        formatted_key = key.replace("_", " ").title()
        
        if isinstance(value, dict):
            # Add section header
            rows.append({
                'Section': formatted_key,
                'Field': '',
                'Value': ''
            })
            # Add nested items
            for sub_key, sub_value in value.items():
                sub_formatted_key = sub_key.replace("_", " ").title()
                rows.append({
                    'Section': '',
                    'Field': sub_formatted_key,
                    'Value': format_value(sub_value)
                })
        elif isinstance(value, list):
            # Add section header
            rows.append({
                'Section': formatted_key,
                'Field': '',
                'Value': ''
            })
            # Add list items
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    rows.append({
                        'Section': '',
                        'Field': f'Item {idx + 1}',
                        'Value': ''
                    })
                    for sub_key, sub_value in item.items():
                        sub_formatted_key = sub_key.replace("_", " ").title()
                        rows.append({
                            'Section': '',
                            'Field': f'  {sub_formatted_key}',
                            'Value': format_value(sub_value)
                        })
                else:
                    rows.append({
                        'Section': '',
                        'Field': f'Item {idx + 1}',
                        'Value': format_value(item)
                    })
        else:
            rows.append({
                'Section': formatted_key,
                'Field': '',
                'Value': format_value(value)
            })
    
    return pd.DataFrame(rows)
def display_features(file_path, title):
    """Display JSON features in a beautiful formatted view"""
    data = load_json(file_path)
    
    st.markdown(f"### 🧩 {title} - Features")
    
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        if st.button("❌ Close Features", key="close_json", use_container_width=True, type="secondary"):
            st.session_state.viewing_json = None
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "error" in data:
        st.error(data["error"])
        return
    
    # Group features by category
    for section_key, section_value in data.items():
        # Create section heading
        section_title = section_key.replace("_", " ").title()
        icon = "📋"
        
        if "document" in section_key.lower():
            icon = "📄"
        elif "date" in section_key.lower() or "time" in section_key.lower():
            icon = "📅"
        elif "amount" in section_key.lower() or "price" in section_key.lower() or "cost" in section_key.lower():
            icon = "💰"
        elif "address" in section_key.lower() or "location" in section_key.lower():
            icon = "📍"
        elif "contact" in section_key.lower() or "phone" in section_key.lower() or "email" in section_key.lower():
            icon = "📞"
        elif "item" in section_key.lower() or "product" in section_key.lower():
            icon = "📦"
        elif "weight" in section_key.lower() or "dimension" in section_key.lower():
            icon = "⚖️"
        
        st.markdown(f"""
            <div class="feature-section">
                <div class="feature-heading">{icon} {section_title}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Display key-value pairs
        if isinstance(section_value, dict):
            for key, value in section_value.items():
                display_key = key.replace("_", " ").title()
                display_val = format_value(value)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"**{display_key}**")
                with col2:
                    st.markdown(f"{display_val}")
                st.markdown("<hr style='margin: 0.5rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        elif isinstance(section_value, list):
            for idx, item in enumerate(section_value):
                if isinstance(item, dict):
                    st.markdown(f"**Item {idx + 1}**")
                    for key, value in item.items():
                        display_key = key.replace("_", " ").title()
                        display_val = format_value(value)
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.markdown(f"*{display_key}*")
                        with col2:
                            st.markdown(f"{display_val}")
                    st.markdown("<hr style='margin: 0.5rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                else:
                    st.markdown(f"• {format_value(item)}")
        else:
            display_val = format_value(section_value)
            st.markdown(f"**Value:** {display_val}")
        
        st.markdown("<br>", unsafe_allow_html=True)

def render_document_card(title, doc_key, gradient_colors):
    """Render a document card with PDF and JSON view buttons"""
    st.markdown(f"""
        <div class="doc-card" style="background: linear-gradient(135deg, {gradient_colors[0]} 0%, {gradient_colors[1]} 100%);">
            <div class="card-title">📄 {title}</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"📄 View PDF", key=f"{doc_key}_pdf_btn", use_container_width=True):
            st.session_state.viewing_pdf = (FILE_PATHS[doc_key]["pdf"], title)
            st.session_state.viewing_json = None
            st.rerun()
    
    with col2:
        if st.button(f"🧩 View Features", key=f"{doc_key}_json_btn", use_container_width=True):
            st.session_state.viewing_json = (FILE_PATHS[doc_key]["json"], title)
            st.session_state.viewing_pdf = None
            st.rerun()

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    
    if st.button("🏠 Document Viewer", use_container_width=True):
        st.session_state.page = 'documents'
        st.session_state.viewing_pdf = None
        st.session_state.viewing_json = None
        st.rerun()
    
    if st.button("📊 Checklist Comparison", use_container_width=True):
        st.session_state.page = 'comparison'
        st.session_state.viewing_pdf = None
        st.session_state.viewing_json = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📁 Documents")
    st.markdown("""
    - Airwaybill
    - Invoice
    - Packing List
    """)
    
    st.markdown("### ✅ Checklists")
    st.markdown("""
    - Original Checklist
    - Generated Checklist
    """)

# Main content area - Check if viewing PDF or JSON
if st.session_state.viewing_pdf:
    file_path, title = st.session_state.viewing_pdf
    display_pdf_modal(file_path, title)

elif st.session_state.viewing_json:
    file_path, title = st.session_state.viewing_json
    display_features(file_path, title)

elif st.session_state.page == 'documents':
    st.title("📋 Document Validation Workflow")
    st.markdown("### Upload and review your shipping documents")
    st.markdown("---")
    
    # Document cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_document_card("Airwaybill", "airwaybill", ["#667eea", "#764ba2"])
    
    with col2:
        render_document_card("Invoice", "invoice", ["#f093fb", "#f5576c"])
    
    with col3:
        render_document_card("Packing List", "packinglist", ["#4facfe", "#00f2fe"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Generate Checklist button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate Checklist", key="generate_btn", use_container_width=True, type="primary"):
            st.session_state.page = 'comparison'
            st.rerun()

elif st.session_state.page == 'comparison':
    st.title("📊 Checklist Comparison")
    st.markdown("### Compare original and generated checklists")
    st.markdown("---")
    
    # View selection tabs
    tab1, tab2 = st.tabs(["📄 PDF Comparison", "🧩 Features Comparison"])
    
    with tab1:
        st.markdown("### Side-by-Side PDF Comparison")
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ✅ Original Checklist")
            try:
                with open(FILE_PATHS["original_checklist"]["pdf"], "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border: 2px solid #43e97b; border-radius: 8px;"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            except FileNotFoundError:
                st.error("Original checklist PDF not found")
            except Exception as e:
                st.error(f"Error loading PDF: {str(e)}")
        
        with col2:
            st.markdown("#### 🤖 Generated Checklist")
            try:
                with open(FILE_PATHS["generated_checklist"]["pdf"], "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border: 2px solid #fa709a; border-radius: 8px;"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            except FileNotFoundError:
                st.error("Generated checklist PDF not found")
            except Exception as e:
                st.error(f"Error loading PDF: {str(e)}")
    
    with tab2:
        st.markdown("### Side-by-Side Features Comparison")
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ✅ Original Checklist Features")
            original_data = load_json(FILE_PATHS["original_checklist"]["json"])
            
            if "error" in original_data:
                st.error(original_data["error"])
            else:
                # Convert JSON to DataFrame and display as table
                df_original = flatten_json_to_table(original_data)
                
                # Style the dataframe
                st.dataframe(
                    df_original,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Section": st.column_config.TextColumn(
                            "Section",
                            width="medium",
                        ),
                        "Field": st.column_config.TextColumn(
                            "Field",
                            width="medium",
                        ),
                        "Value": st.column_config.TextColumn(
                            "Value",
                            width="large",
                        ),
                    }
                )
        
        with col2:
            st.markdown("#### 🤖 Generated Checklist Features")
            generated_data = load_json(FILE_PATHS["generated_checklist"]["json"])
            
            if "error" in generated_data:
                st.error(generated_data["error"])
            else:
                # Convert JSON to DataFrame and display as table
                df_generated = flatten_json_to_table(generated_data)
                
                # Style the dataframe
                st.dataframe(
                    df_generated,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Section": st.column_config.TextColumn(
                            "Section",
                            width="medium",
                        ),
                        "Field": st.column_config.TextColumn(
                            "Field",
                            width="medium",
                        ),
                        "Value": st.column_config.TextColumn(
                            "Value",
                            width="large",
                        ),
                    }
                )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Back button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⬅️ Back to Documents", use_container_width=True):
            st.session_state.page = 'documents'
            st.rerun()