import streamlit as st
import json
import re
from pathlib import Path

# Set page configuration
st.set_page_config(page_title="Documentation Explorer", page_icon="📖", layout="wide")

# Load documentation from JSON file
@st.cache_data
def load_documentation():
    with open(
        "/Users/davidperso/projects/DeepRepo/docstrings_json/spark-nlp.json", "r"
    ) as f:
        data = json.load(f)
    # Filter out documents without 'documentation' key
    docs_with_docs = [doc for doc in data["documentation"] if "documentation" in doc]
    return docs_with_docs


documentation = load_documentation()

# Create a list of file options with full paths
@st.cache_data
def get_file_options(docs):
    file_options = sorted(set(doc["file_paths"] for doc in docs))
    return file_options


file_options = get_file_options(documentation)

# Sidebar
st.sidebar.title("📂 Documentation Explorer")

# File selector
selected_file_path = st.sidebar.selectbox("Select a file:", file_options)

# Display File Content Button
show_code = st.sidebar.button("Display File Code", key="show_code")

# Keyword search
search_query = st.sidebar.text_input("🔍 Search Documentation", value="", key="search")

# Initialize session state for code visibility if not already present
if "code_visible" not in st.session_state:
    st.session_state.code_visible = False

# Initialize session state for current document if not already present
if "current_doc" not in st.session_state:
    st.session_state.current_doc = None

# Main Content
st.markdown(
    "<h1 style='text-align: center;'>📖 Documentation Explorer</h1>",
    unsafe_allow_html=True,
)
st.write("---")


def display_doc(doc, highlight=None):
    st.session_state.current_doc = doc
    st.header(f"🗂️ {doc['file_name']}")
    st.markdown(f"**Path:** `{doc['file_paths']}`")
    st.markdown(f"**Classification:** `{doc['classification']}`")

    if doc["classification"] == "code_file" and "documentation" in doc:
        doc_data = doc["documentation"]
        tabs = []
        content_tabs = []

        if "global_code_description" in doc_data:
            tabs.append("Description")
        if "classes" in doc_data:
            tabs.append("Classes")
        if "functions_out_class" in doc_data:
            tabs.append("Functions")

        if tabs:
            content_tabs = st.tabs(tabs)

            tab_index = 0

            # Description Tab
            if "global_code_description" in doc_data:
                with content_tabs[tab_index]:
                    st.markdown("### 📄 Global Description")
                    description = doc_data["global_code_description"]
                    if highlight:
                        description = highlight_text(description, highlight)
                    st.markdown(description, unsafe_allow_html=True)
                tab_index += 1

            # Classes Tab
            if "classes" in doc_data:
                with content_tabs[tab_index]:
                    for cls in doc_data["classes"]:
                        class_name = cls["class_name"]
                        if highlight and highlight.lower() in class_name.lower():
                            class_name = highlight_text(class_name, highlight)
                        with st.expander(f"🔸 Class: `{class_name}`", expanded=False):
                            class_desc = cls["class_description"]
                            if highlight:
                                class_desc = highlight_text(class_desc, highlight)
                            st.markdown(class_desc, unsafe_allow_html=True)
                            if "attributes" in cls:
                                st.markdown("#### Attributes:")
                                for attr in cls["attributes"]:
                                    attr_name = attr["attribute_name"]
                                    attr_desc = attr["attribute_description"]
                                    if highlight:
                                        attr_name = highlight_text(attr_name, highlight)
                                        attr_desc = highlight_text(attr_desc, highlight)
                                    st.markdown(
                                        f"- `{attr_name}`: {attr_desc}",
                                        unsafe_allow_html=True,
                                    )
                            if "functions_in_class" in cls:
                                st.markdown("#### Methods:")
                                for func in cls["functions_in_class"]:
                                    func_name = func["function_name"]
                                    func_desc = func["function_description"]
                                    if highlight:
                                        func_name = highlight_text(func_name, highlight)
                                        func_desc = highlight_text(func_desc, highlight)
                                    st.markdown(
                                        f"- `{func_name}`: {func_desc}",
                                        unsafe_allow_html=True,
                                    )
                tab_index += 1

            # Functions Tab
            if "functions_out_class" in doc_data:
                with content_tabs[tab_index]:
                    for func in doc_data["functions_out_class"]:
                        func_name = func["function_name"]
                        if highlight and highlight.lower() in func_name.lower():
                            func_name = highlight_text(func_name, highlight)
                        with st.expander(f"🔹 Function: `{func_name}`", expanded=False):
                            func_desc = func["function_description"]
                            if highlight:
                                func_desc = highlight_text(func_desc, highlight)
                            st.markdown(func_desc, unsafe_allow_html=True)
                tab_index += 1
        else:
            st.info("No documentation available for this file.")


def search_documentation(query, docs):
    results = []
    query_lower = query.lower()
    for doc in docs:
        matches = False

        # Concatenate all searchable fields into one string
        searchable_text = " ".join(
            [
                doc.get("file_name", ""),
                doc.get("file_paths", ""),
                doc.get("classification", ""),
            ]
        ).lower()

        # Search in concatenated text
        if query_lower in searchable_text:
            matches = True

        # Search in code documentation
        if doc["classification"] == "code_file" and "documentation" in doc:
            doc_data = doc["documentation"]

            # Collect all texts to search
            code_searchable_text = ""
            code_searchable_text += doc_data.get("global_code_description", "").lower()

            # Classes
            for cls in doc_data.get("classes", []):
                code_searchable_text += cls.get("class_name", "").lower()
                code_searchable_text += cls.get("class_description", "").lower()
                for attr in cls.get("attributes", []):
                    code_searchable_text += attr.get("attribute_name", "").lower()
                    code_searchable_text += attr.get(
                        "attribute_description", ""
                    ).lower()
                for func in cls.get("functions_in_class", []):
                    code_searchable_text += func.get("function_name", "").lower()
                    code_searchable_text += func.get("function_description", "").lower()

            # Functions outside classes
            for func in doc_data.get("functions_out_class", []):
                code_searchable_text += func.get("function_name", "").lower()
                code_searchable_text += func.get("function_description", "").lower()

            if query_lower in code_searchable_text:
                matches = True

        if matches:
            results.append(doc)

    return results


def highlight_text(text, highlight):
    # Escape special characters in highlight
    highlight_escaped = re.escape(highlight)
    pattern = re.compile(f"({highlight_escaped})", re.IGNORECASE)
    # Replace matches with highlighted HTML
    return pattern.sub(r'<mark style="background-color: #FFFF00">\1</mark>', text)


if search_query:
    # Display search results
    st.subheader(f"Search Results for '{search_query}':")
    search_results = search_documentation(search_query, documentation)

    if search_results:
        for doc in search_results:
            if st.button(
                f"📄 View Documentation for {doc['file_name']}",
                key=f"search_result_{doc['file_paths']}",
            ):
                display_doc(doc, highlight=search_query)
                st.markdown("---")
    else:
        st.warning("No results found.")
else:
    # Find the selected file's documentation
    selected_doc = next(
        (doc for doc in documentation if doc["file_paths"] == selected_file_path), None
    )
    if selected_doc:
        display_doc(selected_doc)
    else:
        st.warning("No documentation available for the selected file.")

    # Display the code content when the button is clicked or if already visible
    if show_code or st.session_state.code_visible:
        st.session_state.code_visible = True  # Ensure it stays visible
        # Read and display the code from the file
        try:
            with open(selected_doc["file_paths"], "r") as code_file:
                code_content = code_file.read()
            st.markdown("### 📜 Code Content")
            st.code(code_content, language="python")
            # Add a button to hide the code
            if st.button("Hide Code"):
                st.session_state.code_visible = False
                st.experimental_rerun()  # Rerun the app to hide the code
        except Exception as e:
            st.error(f"Error reading the file: {e}")
    elif selected_doc:  # Only show the button if a document is selected
        st.info("Click the 'Display File Code' button to view the code.")

# Footer
st.write("---")
st.markdown(
    "<p style='text-align: center;'>Documentation Explorer</p>", unsafe_allow_html=True
)
