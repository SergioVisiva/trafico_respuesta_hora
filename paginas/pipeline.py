def mostrar():
    import streamlit as st

    st.markdown(
        """
    <div style="
        text-align: center;
        padding: 50px;
        border-radius: 10px;
        background-color: #FFF3CD;
        color: #856404;
        font-family: 'Arial', sans-serif;
        box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
    ">
        <h2>🚧 Página en desarrollo</h2>
        <p>Estamos trabajando en esta sección para ofrecerle la mejor experiencia.</p>
        <p>Por favor, vuelva más tarde para acceder a las funcionalidades completas.</p>
        <p>💡 Mientras tanto, explore otras secciones disponibles en el menú.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
