import streamlit as st
import services
import time
from streamlit.runtime.scriptrunner import RerunException

def show_error(message):
    st.error(message)
    st.stop()

@st.cache_data(show_spinner=False)
def analyze_data(file_content):
    return services.analyze_lessons(file_content)

def main():
    st.set_page_config(page_title="Post-Mortem Analysis", layout="wide")
    st.title("Post-Mortem Analysis Tool")
    
    uploaded_file = st.file_uploader("Upload your post-mortem data file", type=["txt"])
    
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8").splitlines()
            if not file_content:
                show_error("Uploaded file is empty")
            
            with st.spinner("Analyzing post-mortem data (this may take a minute)..."):
                start_time = time.time()
                report = analyze_data(file_content)
                st.success(f"Analysis completed in {time.time() - start_time:.1f} seconds")
            
            if "error" in report:
                show_error(f"Analysis error: {report['error']}")
            
            display_results(report)
            
        except Exception as e:
            show_error(f"Unexpected error: {str(e)}")

def display_results(report):
    tab1, tab2, tab3, tab4 = st.tabs([
        "Unrecoverable Lines", 
        "Common Themes", 
        "Unclassified Lines", 
        "Summary & Recommendations"
    ])
    
    with tab1:
        if report["unrecoverable_lines"]:
            st.write("Lines that couldn't be understood:")
            for line in report["unrecoverable_lines"]:
                st.code(line, language="text")
        else:
            st.info("All lines had recoverable meaning")
    
    with tab2:
        if report["common_ideas"]:
            for category in report["common_ideas"]:
                with st.expander(f"{category['title']} (Confidence: {category['overall_confidence']}%)"):
                    for example in category["examples"]:
                        st.write(f"- {example['text']} (Fit: {example['confidence']}%)")
        else:
            st.info("No common themes identified")
    
    with tab3:
        if report["uncategorized_lines"]:
            st.write("Meaningful lines that didn't fit categories:")
            for line in report["uncategorized_lines"]:
                st.write(f"- {line}")
        else:
            st.info("All meaningful lines were categorized")
    
    with tab4:
        st.subheader("Summary")
        st.write(report["summary"])
        
        st.subheader("Key Observations")
        for obs in report["observations"]:
            st.write(f"- {obs}")
        
        st.subheader("Recommendations")
        for rec in report["recommendations"]:
            st.write(f"- {rec}")

if __name__ == "__main__":
    main()