import json
import streamlit as st

def load_css(file_path: str = "assets/css/style.css"):
    with open(file_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_template(template_name: str, **kwargs) -> str:
    path = f"assets/templates/{template_name}.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content.format(**kwargs)

def load_presets(file_path: str = "assets/data/presets.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
