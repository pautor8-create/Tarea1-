import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Configuración de la página
st.set_page_config(page_title='Dashboard de Carga Interna', layout='wide')

st.title('⚽ Dashboard de Rendimiento: Monitorización de Carga Interna')

# 1. Función para procesar y calcular semáforos de cualquier DataFrame (Simulado o Real)
def calcular_metricas_y_colores(df):
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values('Fecha')
    
    lista_procesada = []
    for atleta, sub_df in df.groupby('Atleta'):
        sub_df = sub_df.copy()
        # Calcular Línea Base de 7 días
        sub_df['Baseline'] = sub_df['rMSSD'].rolling(window=7, min_periods=1).mean().round(1)
        std_atleta = sub_df['rMSSD'].std()
        if pd.isna(std_atleta) or std_atleta == 0:
            std_atleta = 5.0 # Valor por defecto si hay pocos datos
            
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
        
    return pd.concat(lista_processed) if lista_procesada else df

# 2. Función de datos simulados (Por si no se sube ningún archivo)
@st.cache_data
def generar_datos_simulados():
    np.random.seed(44)
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=30)
    atletas = ["Pau", "Rafa", "Nordin"]
    lista_df = []
    
    for atleta in atletas:
        if atleta == "Pau": media, desviacion = 65, 6
        elif atleta == "Rafa": media, desviacion = 70, 8
        else: media, desviacion = 64, 7
            
        rmssd = np.random.normal(loc=media, scale=desviacion, size=30).round(1)
        if atleta == "Pau": rmssd[-1] = 71.0       
        elif atleta == "Rafa": rmssd[-1] = 62.0     
        elif atleta == "Nordin": rmssd[-1] = 46.0   
            
        df = pd.DataFrame({'Fecha': fechas, 'Atleta': atleta, 'rMSSD': rmssd})
        lista_df.append(df)
    return pd.concat(lista_df)

# ==========================================
# GESTIÓN DE FUENTE DE DATOS (Simulados vs Reales)
# ==========================================
# Creamos la pestaña 3 primero en la interfaz conceptual para la carga
tab1, tab2, tab3 = st.tabs(["👤 Análisis Individual", "👥 Vista de Equipo (Comparador)", "📂 Subir Datos Wearables"])

with tab3:
    st.subheader("📂 Importación Manual de Datos (.csv o .xlsx)")
    st.markdown("Arrastra aquí las exportaciones de tus aplicaciones (**Amazfit, Oura, Mi Fit, HRV4Training**, etc.).")
    
    archivo_subido = st.file_uploader("Selecciona el archivo de tu ordenador:", type=['csv', 'xlsx'])
    
    if archivo_subido is not None:
        try:
            if archivo_subido.name.endswith('.csv'):
                df_real = pd.read_csv(archivo_subido)
            else:
                df_real = pd.read_excel(archivo_subido)
                
            # Verificar columnas mínimas obligatorias
            columnas_requeridas = {'Fecha', 'Atleta', 'rMSSD'}
            if columnas_requeridas.issubset(df_real.columns):
                st.success(f"¡Archivo '{archivo_subido.name}' cargado con éxito! El dashboard ahora usa tus datos reales.")
                df_base = df_real
                datos_son_reales = True
            else:
                st.error(f"Error: El archivo debe contener obligatoriamente las columnas: **Fecha, Atleta, rMSSD**. Columnas encontradas: {list(df_real.columns)}")
                df_base = generar_datos_simulados()
                datos_son_reales = False
        except Exception as e:
            st.error(f"No se pudo procesar el archivo: {e}")
            df_base = generar_datos_simulados()
            datos_son_reales = False
    else:
        st.info("💡 Actualmente mostrando **Datos de Ejemplo (Simulados)**. Sube un archivo en esta pestaña para ver métricas reales.")
        df_base = generar_datos_simulados()
        datos_son_reales = False

# Procesar el dataframe elegido con la lógica de carga y semáforos
df_todos = calcular_metricas_y_colores(df_base)

# ==========================================
# PESTAÑA 1: ANÁLISIS INDIVIDUAL
# ==========================================
with tab1:
    st.sidebar.header('🎛️ Filtros Individuales')
    atleta_seleccionado = st.sidebar.selectbox('Selecciona el Atleta:', options=df_todos['Atleta'].unique(), key='sb_atleta')
    
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

# ==========================================
# PESTAÑA 2: VISTA DE EQUIPO (EL COMPARADOR)
# ==========================================
with tab2:
    st.subheader("📊 Análisis Comparativo: Desviación de Carga Interna (Hoy)")
    st.markdown("Este gráfico muestra cuánto se desvía el rMSSD de hoy respecto a la media de cada jugador.")
    
    hoy_atletas = df_todos.groupby('Atleta').last().reset_index()
    
    fig_
