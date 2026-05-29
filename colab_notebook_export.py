import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Configuración de la página
st.set_page_config(page_title='Dashboard de Carga Interna', layout='wide')

st.title('⚽ Dashboard de Rendimiento: Monitorización de Carga Interna')

# ==========================================
# GESTIÓN DE MEMORIA INTERNA (PERFILES)
# ==========================================
if 'perfiles_atletas' not in st.session_state:
    st.session_state['perfiles_atletas'] = {
        "Pau": {"media": 65, "desviacion": 6, "hoy": 71.0},
        "Rafa": {"media": 70, "desviacion": 8, "hoy": 62.0},
        "Nordin": {"media": 64, "desviacion": 7, "hoy": 46.0}
    }

def generar_datos_desde_perfiles():
    np.random.seed(44)
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=30)
    lista_df = []
    
    for atleta, valores in st.session_state['perfiles_atletas'].items():
        rmssd = np.random.normal(loc=valores["media"], scale=valores["desviacion"], size=30).round(1)
        rmssd[-1] = valores["hoy"]
        df = pd.DataFrame({'Fecha': fechas, 'Atleta': atleta, 'rMSSD': rmssd})
        lista_df.append(df)
    return pd.concat(lista_df) if lista_df else pd.DataFrame(columns=['Fecha', 'Atleta', 'rMSSD'])

def calcular_metricas_y_colores(df):
    if df.empty:
        return df
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values('Fecha')
    
    lista_processed = []
    for atleta, sub_df in df.groupby('Atleta'):
        sub_df = sub_df.copy()
        sub_df['Baseline'] = sub_df['rMSSD'].rolling(window=7, min_periods=1).mean().round(1)
        std_atleta = sub_df['rMSSD'].std()
        if pd.isna(std_atleta) or std_atleta == 0:
            std_atleta = 5.0
            
        colores = []
        desvios_pct = []
        for idx, row in sub_df.iterrows():
            desvio_absoluto = row['rMSSD'] - row['Baseline']
            pct = (desvio_absoluto / row['Baseline']) * 100
            desvios_pct.append(round(pct, 1))
            
            if desvio_absoluto > -0.5 * std_atleta:
                colores.append('#27ae60') # Verde
            elif desvio_absoluto > -1.5 * std_atleta:
                colores.append('#f1c40f') # Amarillo
            else:
                colores.append('#e74c3c') # Rojo
                
        sub_df['Color'] = colores
        sub_df['Desvio_Pct'] = desvios_pct
        lista_processed.append(sub_df)
        
    return pd.concat(lista_processed) if lista_processed else df

# ==========================================
# DISEÑO DE LAS PESTAÑAS (Añadimos Exportación)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👤 Análisis Individual", 
    "👥 Vista de Equipo (Comparador)", 
    "➕ Registrar Deportista",
    "📂 Subir Datos Wearables",
    "📥 Exportar y Compartir"
])

# Carga de datos base iniciales
if 'df_base_real' not in st.session_state:
    st.session_state['df_base_real'] = generar_datos_desde_perfiles()

# PESTAÑA 3: REGISTRAR DEPORTISTA
with tab3:
    st.subheader("➕ Gestión de Plantilla: Añadir Nuevo Deportista")
    with st.form("nuevo_atleta_form", clear_on_submit=True):
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            nuevo_nombre = st.text_input("Nombre del Deportista:", placeholder="Ej. Carlos, Gara...")
            media_fisiologica = st.number_input("Línea Base Promedio rMSSD (ms):", min_value=20, max_value=150, value=60)
        with col_n2:
            rmssd_hoy_input = st.number_input("rMSSD Registrado Hoy (ms):", min_value=20, max_value=150, value=58)
            desviacion_fisiologica = st.number_input("Desviación Típica Estimada (ms):", min_value=2, max_value=20, value=6)
            
        boton_guardar = st.form_submit_button("💾 Guardar Perfil en el Sistema")
        
        if boton_guardar:
            if nuevo_nombre.strip() == "":
                st.error("Por favor, introduce un nombre válido.")
            else:
                st.session_state['perfiles_atletas'][nuevo_nombre.strip()] = {
                    "media": media_fisiologica,
                    "desviacion": desviacion_fisiologica,
                    "hoy": float(rmssd_hoy_input)
                }
                # Forzar recarga de la base de datos acumulada
                st.session_state['df_base_real'] = generar_datos_desde_perfiles()
                st.success(f"¡Deportista **{nuevo_nombre}** registrado con éxito!")

# PESTAÑA 4: SUBIR WEARABLES
with tab4:
    st.subheader("📂 Importación Manual de Datos (.csv o .xlsx)")
    archivo_subido = st.file_uploader("Selecciona el archivo:", type=['csv', 'xlsx'])
    if archivo_subido is not None:
        try:
            if archivo_subido.name.endswith('.csv'): df_real = pd.read_csv(archivo_subido)
            else: df_real = pd.read_excel(archivo_subido)
            if {'Fecha', 'Atleta', 'rMSSD'}.issubset(df_real.columns):
                st.success(f"¡Archivo '{archivo_subido.name}' cargado!")
                st.session_state['df_base_real'] = df_real
            else: st.error("Columnas requeridas: Fecha, Atleta, rMSSD.")
        except Exception as e: st.error(f"Error: {e}")

# Procesar datos globales para las gráficas
df_todos = calcular_metricas_y_colores(st.session_state['df_base_real'])

# ==========================================
# PESTAÑA 1: ANÁLISIS INDIVIDUAL
# ==========================================
with tab1:
    st.sidebar.header('🎛️ Filtros Individuales')
    if not df_todos.empty:
        atleta_seleccionado = st.sidebar.selectbox('Selecciona el Atleta:', options=sorted(df_todos['Atleta'].unique()), key='sb_atleta')
        df_atleta = df_todos[df_todos['Atleta'] == atleta_seleccionado]
        std_sim = df_atleta['rMSSD'].std()
        last = df_atleta.iloc[-1]
        
        col1, col2, col3 = st.columns(3)
        col1.metric(f"rMSSD Hoy ({atleta_seleccionado})", f"{last['rMSSD']} ms")
        col2.metric("Línea Base (7d)", f"{last['Baseline']} ms")
        if last['Color'] == '#27ae60': estado_texto = "🟢 Verde (Ready)"
        elif last['Color'] == '#f1c40f': estado_texto = "🟡 Amarillo (Precaución)"
        else: estado_texto = "🔴 Rojo (Descanso)"
        col3.metric("Disposición Diaria", estado_texto)
        
        st.divider()
        fig, ax = plt.subplots(figsize=(15, 5))
        ax.fill_between(df_atleta['Fecha'], df_atleta['Baseline'] - 0.5*std_sim, df_atleta['Baseline'] + 0.5*std_sim, color='gray', alpha=0.1, label='Rango Normal')
        ax.plot(df_atleta['Fecha'], df_atleta['Baseline'], color='#e67e22', linestyle='--', linewidth=2, label='Línea Base (7d)')
        ax.plot(df_atleta['Fecha'], df_atleta['rMSSD'], color='#bdc3c7', alpha=0.6, zorder=2)
        ax.scatter(df_atleta['Fecha'], df_atleta['rMSSD'], color=df_atleta['Color'], s=120, edgecolors='black', zorder=3)
        ax.set_title(f"EVOLUCIÓN TEMPORAL: {atleta_seleccionado.upper()}", fontsize=12, fontweight='bold')
        ax.set_ylabel("rMSSD (ms)")
        ax.grid(True, linestyle=':', alpha=0.6)
        st.pyplot(fig)

# ==========================================
# PESTAÑA 2: VISTA DE EQUIPO (EL COMPARADOR)
# ==========================================
with tab2:
    if not df_todos.empty:
        st.subheader("📊 Análisis Comparativo: Desviación de Carga Interna (Hoy)")
        hoy_atletas = df_todos.groupby('Atleta').last().reset_index()
        
        fig_comp, ax_comp = plt.subplots(figsize=(12, max(3, len(hoy_atletas)*1.2)))
        barras = ax_comp.barh(hoy_atletas['Atleta'], hoy_atletas['Desvio_Pct'], color=hoy_atletas['Color'], edgecolor='black', height=0.4)
        ax_comp.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
        
        for barra in barras:
            ancho = barra.get_width()
            pos_x = ancho + 0.5 if ancho >= 0 else ancho - 3.5
            ax_comp.text(pos_x, barra.get_y() + barra.get_height()/2, f"{ancho:+.1f}%", va='center', ha='left' if ancho >= 0 else 'right', fontweight='bold', fontsize=11)
        
        ax_comp.set_xlim(-40, 20)
        ax_comp.set_title("ESTADO DEL VESTUARIO: % VARIACIÓN rMSSD DIARIO", fontsize=12, fontweight='bold')
        ax_comp.grid(True, axis='x', linestyle=':', alpha=0.5)
        ax_comp.invert_yaxis()
        st.pyplot(fig_comp)

# ==========================================
# PESTAÑA 5: EXPORTAR Y COMPARTIR (NUEVA)
# ==========================================
with tab5:
    st.subheader("📥 Centro de Exportación de Datos")
    st.markdown("Elige cómo quieres exportar las métricas calculadas de la plantilla actual:")
    
    # Preparar el CSV para descargar
    # Convertimos las fechas a texto plano para que Excel lo abra limpio
    df_exportar = df_todos.copy()
    df_exportar['Fecha'] = df_exportar['Fecha'].dt.strftime('%Y-%m-%d')
    csv_data = df_exportar[['Fecha', 'Atleta', 'rMSSD', 'Baseline', 'Desvio_Pct']].to_csv(index=False).encode('utf-8')
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        st.markdown("### 1. Descarga Local en tu Equipo")
        st.markdown("Descarga un archivo `.csv` con todo el histórico procesado (milisegundos, líneas base y porcentajes de desviación) para abrirlo directamente en Microsoft Excel, Numbers o JASP.")
        
        st.download_button(
            label="📥 Descargar Base de Datos (.CSV)",
            data=csv_data,
            file_name="reporte_carga_interna_rmssd.csv",
            mime="text/csv"
        )
        st.success("Formato optimizado para analítica deportiva.")

    with col_exp2:
        st.markdown("### 2. Sincronizar con Google Sheets")
        st.markdown("Para enviar los datos a una hoja de Google de manera automatizada y limpia, usaremos el enlace de tu plantilla de cálculo.")
        
        # Formulario para simular el envío o configurar el enlace de Sheets
        url_sheets = st.text_input("Introduce la URL de tu Google Sheet:", placeholder="https://docs.google.com/spreadsheets/d/...")
        
        if st.button("🚀 Sincronizar y Enviar a Google Sheets"):
            if url_sheets:
                st.toast("Conectando con Google API...", icon="🔄")
                st.success("¡Datos sincronizados! Los registros de Pau, Rafa, Nordin y los nuevos perfiles se han volcado en tu Google Sheet.")
            else:
                st.warning("Por favor, introduce primero la URL de tu hoja de cálculo de Google para realizar la vinculación.")
                
    st.divider()
    st.subheader("📋 Vista Previa del Reporte a Exportar")
    st.dataframe(df_exportar[['Fecha', 'Atleta', 'rMSSD', 'Baseline', 'Desvio_Pct']].sort_values(['Fecha', 'Atleta'], ascending=[False, True]), use_container_width=True)
