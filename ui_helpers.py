import os
import json
import streamlit as st

def load_css():
    css_path = os.path.join("assets", "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_template(template_name: str, **kwargs) -> str:
    path = os.path.join("assets", "templates", f"{template_name}.html")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        template = f.read()
    # Membersihkan karakter return baris yang dapat memicu markdown raw block
    rendered = template.format(**kwargs).strip()
    return rendered

def load_presets():
    path = os.path.join("assets", "data", "presets.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"name": "Google DNS", "url": "https://dns.google", "label": "Google DNS (Fast Global)"},
        {"name": "Cloudflare CDN", "url": "https://1.1.1.1", "label": "Cloudflare CDN"},
        {"name": "GitHub Status", "url": "https://www.githubstatus.com", "label": "GitHub Status"}
    ]
