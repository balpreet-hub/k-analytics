import streamlit as st

st.set_page_config(page_title="K-ANALYTICS", page_icon="🦅", layout="centered")

st.title("🦅 K-ANALYTICS Access")
st.info("Architecture MVC chargée. Connecte-toi (Simulé).")

# Simulation login
if st.button("Se Connecter"):
    st.session_state['authenticated'] = True
    st.success("Connecté ! Regarde le menu à gauche.")
    st.balloons()
    
    