import streamlit as st
import services
import time
import traceback

def display_error(message, details=None):
    st.error(message)
    if details:
        with st.expander("Error Details"):
            st.code(details)
    st.stop()

@st.cache_data(show_spinner=False)
def analyze_data(file_content):
    return services.analyze_lessons(file_content)

def safe_get(dictionary, keys, default=None):
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(dictionary, dict) and key in dictionary:
            dictionary = dictionary[key]
        else:
            return default
    return dictionary

def main():
    st.set_page_config(page_title="Post-Mortem Analysis", layout="wide")
    st.title("Post-Mortem Analysis Tool")
    
    uploaded_file = st.file_uploader("Upload your post-mortem data file", type=["txt"])
    
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8").splitlines()
            if not file_content:
                display_error("Uploaded file is empty")
            
            with st.spinner("Analyzing post-mortem data (this may take a minute)..."):
                try:
                    start_time = time.time()
                    report = analyze_data(file_content)
                    st.success(f"Analysis completed in {time.time() - start_time:.1f} seconds")
                except Exception as e:
                    display_error("Analysis failed", traceback.format_exc())
            
            if "error" in report:
                # Check if there's debug info available
                if "debug_info" in report:
                    display_error(f"Analysis error: {report['error']}", report['debug_info'])
                else:
                    display_error(f"Analysis error: {report['error']}")
            
            display_results(report)
            
        except Exception as e:
            display_error(f"Unexpected error: {str(e)}", traceback.format_exc())

def display_results(report):
    tab1, tab2, tab3, tab4 = st.tabs([
        "Unrecoverable Lines", 
        "Common Themes", 
        "Unclassified Lines", 
        "Summary & Recommendations"
    ])
    
    with tab1:
        st.subheader("Lines with Unrecoverable Meaning")
        if safe_get(report, ["unrecoverable_lines"]):
            for line in report["unrecoverable_lines"]:
                st.write(f"- {line}")
        else:
            st.info("No unrecoverable lines found")
    
    with tab2:
        st.subheader("Common Themes")
        if safe_get(report, ["common_ideas"]):
            for category in report["common_ideas"]:
                with st.expander(f"{safe_get(category, ['title'], 'Untitled')} (Confidence: {safe_get(category, ['overall_confidence'], '?')}%)"):
                    examples = safe_get(category, ['examples'], [])
                    if examples:
                        for example in examples:
                            st.write(f"- {safe_get(example, ['text'], '')} (Fit: {safe_get(example, ['confidence'], '?')}%)")
                    else:
                        st.info("No examples for this category")
        else:
            st.info("No common themes identified")
    
    with tab3:
        st.subheader("Meaningful but Unclassified Lines")
        if safe_get(report, ["uncategorized_lines"]):
            for line in report["uncategorized_lines"]:
                st.write(f"- {line}")
        else:
            st.info("All meaningful lines were categorized")
    
    with tab4:
        st.subheader("Summary")
        st.write(safe_get(report, ["summary"], "No summary available"))
        
        st.subheader("Key Observations")
        if safe_get(report, ["observations"]):
            for obs in report["observations"]:
                st.write(f"- {obs}")
        else:
            st.info("No observations available")
        
        st.subheader("Recommendations")
        if safe_get(report, ["recommendations"]):
            for rec in report["recommendations"]:
                st.write(f"- {rec}")
        else:
            st.info("No recommendations available")

if __name__ == "__main__":
    main()