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
# Inicializamos la base de datos interna en la sesión si no existe aún
if 'perfiles_atletas' not in st.session_state:
    st.session_state['perfiles_atletas'] = {
        "Pau": {"media": 65, "desviacion": 6, "hoy": 71.0},
        "Rafa": {"media": 70, "desviacion": 8, "hoy": 62.0},
        "Nordin": {"media": 64, "desviacion": 7, "hoy": 46.0}
    }

# Función para generar los datos basados en los perfiles almacenados
def generar_datos_desde_perfiles():
    np.random.seed(44)
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=30)
    lista_df = []
    
    for atleta, valores in st.session_state['perfiles_atletas'].items():
        # Generar los 30 días simulados según el perfil del jugador
        rmssd = np.random.normal(loc=valores["media"], scale=valores["desviacion"], size=30).round(1)
        # Forzar el valor del último día (Hoy) con el registrado en su perfil
        rmssd[-1] = valores["hoy"]
            
        df = pd.DataFrame({'Fecha': fechas, 'Atleta': atleta, 'rMSSD': rmssd})
        lista_df.append(df)
    return pd.concat(lista_df) if lista_df else pd.DataFrame(columns=['Fecha', 'Atleta', 'rMSSD'])

# Función para procesar y calcular semáforos
def calcular_metricas_y_colores(df):
    if df.empty:
        return df
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values('Fecha')
    
    lista_procesada = []
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
        lista_procesada.append(sub_df)
        
    return pd.concat(lista_procesada) if lista_procesada else df

# ==========================================
# DISEÑO DE LAS 4 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "👤 Análisis Individual", 
    "👥 Vista de Equipo (Comparador)", 
    "➕ Registrar Deportista",
    "📂 Subir Datos Wearables"
])

# PESTAÑA 3 (REGISTRAR): Definida antes cronológicamente para actualizar los datos base
with tab3:
    st.subheader("➕ Gestión de Plantilla: Añadir Nuevo Deportista")
    st.markdown("Crea un nuevo perfil fisiológico para el equipo. Se guardará de inmediato en el selector superior.")
    
    # Formulario de entrada
    with st.form("nuevo_atleta_form", clear_on_submit=True):
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            nuevo_nombre = st.text_input("Nombre del Deportista:", placeholder="Ej. Gara, Carlos...")
            media_fisiologica = st.number_input("Línea Base Promedio rMSSD (ms):", min_value=20, max_value=150, value=60)
        with col_n2:
            rmssd_hoy_input = st.number_input("rMSSD Registrado Hoy (ms):", min_value=20, max_value=150, value=58)
            desviacion_fisiologica = st.number_input("Desviación Típica Estimada (ms):", min_value=2, max_value=20, value=6)
            
        boton_guardar = st.form_submit_button("💾 Guardar Perfil en el Sistema")
        
        if boton_guardar:
            if nuevo_nombre.strip() == "":
                st.error("Por favor, introduce un nombre válido.")
            else:
                # Añadir o sobreescribir en la memoria de la sesión
                st.session_state['perfiles_atletas'][nuevo_nombre.strip()] = {
                    "media": media_fisiologica,
                    "desviacion": desviacion_fisiologica,
                    "hoy": float(rmssd_hoy_input)
                }
                st.success(f"¡Deportista **{nuevo_nombre}** registrado con éxito! Ya puedes seleccionarlo en las pestañas de análisis.")

with tab4:
    st.subheader("📂 Importación Manual de Datos (.csv o .xlsx)")
    st.markdown("Arrastra aquí un documento externo si prefieres cargar datos masivos de golpe.")
    archivo_subido = st.file_uploader("Selecciona el archivo:", type=['csv', 'xlsx'])
    
    if archivo_subido is not None:
        try:
            if archivo_subido.name.endswith('.csv'): df_real = pd.read_csv(archivo_subido)
            else: df_real = pd.read_excel(archivo_subido)
            
            if {'Fecha', 'Atleta', 'rMSSD'}.issubset(df_real.columns):
                st.success(f"¡Archivo '{archivo_subido.name}' cargado!")
                df_base = df_real
                datos_son_reales = True
            else:
                st.error("Columnas requeridas: Fecha, Atleta, rMSSD.")
                df_base = generar_datos_desde_perfiles()
                datos_son_reales = False
        except Exception as e:
            st.error(f"Error: {e}")
            df_base = generar_datos_desde_perfiles()
            datos_son_reales = False
    else:
        df_base = generar_datos_desde_perfiles()
        datos_son_reales = False

# Procesar datos globales
df_todos = calcular_metricas_y_colores(df_base)

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
        
        legend_elements = [
            Line2D([0], [0], color='#e67e22', linestyle='--', label='Línea Base'),
            Line2D([0], [0], marker='o', color='w', label='Verde (Ready)', markerfacecolor='#27ae60', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Amarillo', markerfacecolor='#f1c40f', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Rojo (Descanso)', markerfacecolor='#e74c3c', markersize=10)
        ]
        ax.legend(handles=legend_elements, loc='upper left')
        st.pyplot(fig)
    else:
        st.warning("No hay atletas registrados en el sistema.")

# ==========================================
# PESTAÑA 2: VISTA DE EQUIPO (EL COMPARADOR)
# ==========================================
with tab2:
    if not df_todos.empty:
        st.subheader("📊 Análisis Comparativo: Desviación de Carga Interna (Hoy)")
        st.markdown("Porcentaje de desvío del rMSSD actual respecto a la media de cada jugador registrado.")
        
        hoy_atletas = df_todos.groupby('Atleta').last().reset_index()
        
        fig_comp, ax_comp = plt.subplots(figsize=(12, max(3, len(hoy_atletas)*1.2)))
        barras = ax_comp.barh(hoy_atletas['Atleta'], hoy_atletas['Desvio_Pct'], color=hoy_atletas['Color'], edgecolor='black', height=0.4)
        ax_comp.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
        
        for barra in barras:
            ancho = barra.get_width()
            pos_x = ancho + 0.5 if ancho >= 0 else ancho - 3.5
            ax_comp.text(pos_x, barra.get_y() + barra.get_height()/2, f"{ancho:+.1f}%", 
                         va='center', ha='left' if ancho >= 0 else 'right', fontweight='bold', fontsize=11)
        
        ax_comp.set_xlim(-40, 20)
        ax_comp.set_xlabel("Porcentaje de Desviación respecto a la Línea Base (%)")
        ax_comp.set_title("ESTADO DEL VESTUARIO: % VARIACIÓN rMSSD DIARIO", fontsize=12, fontweight='bold', pad=10)
        ax_comp.grid(True, axis='x', linestyle=':', alpha=0.5)
        ax_comp.invert_yaxis()
        st.pyplot(fig_comp)
        
        st.markdown("### 📋 Recomendación de Estado de Carga")
        for idx, row in hoy_atletas.iterrows():
            if row['Color'] == '#27ae60':
                st.success(f"**{row['Atleta']}** -> 🟢 **Ready** ({row['Desvio_Pct']:+.1f}%): Óptimo estado. Ritmo normal de entrenamiento.")
            elif row['Color'] == '#f1c40f':
                st.warning(f"**{row['Atleta']}** -> 🟡 **Precaución** ({row['Desvio_Pct']:+.1f}%): Fatiga moderada detectada. Regular picos de intensidad.")
            else:
                st.error(f"**{row['Atleta']}** -> 🔴 **Descanso** ({row['Desvio_Pct']:+.1f}%): Variabilidad muy baja. Priorizar descarga o recuperación activa.")
    else:
        st.warning("Registra deportistas en la pestaña correspondiente para generar la comparativa.")
