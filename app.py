import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Configuración de la página
st.set_page_config(page_title='Dashboard de Readiness & rMSSD', layout='wide')

st.title('📈 Dashboard de Rendimiento: Evolución rMSSD y Readiness')

# 1. Función para generar datos simulados con varios atletas
@st.cache_data
def generar_datos_atletas():
    np.random.seed(42)
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=30)
    
    # Lista de atletas para el selector
    atletas = ["Enrique", "Joseba", "Pau"]
    lista_df = []
    
    for atleta in atletas:
        # Cada atleta tiene medias ligeramente diferentes para simular realidad
        if atleta == "Enrique":
            media, desviacion = 65, 8
        elif atleta == "Joseba":
            media, desviacion = 58, 6
        else:
            media, desviacion = 62, 7
            
        rmssd = np.random.normal(loc=media, scale=desviacion, size=30).round(1)
        
        df = pd.DataFrame({
            'Fecha': fechas, 
            'Atleta': atleta,
            'rMSSD': rmssd
        })
        
        df['Baseline'] = df['rMSSD'].rolling(window=7, min_periods=1).mean().round(1)
        std_atleta = df['rMSSD'].std()
        
        colores = []
        for idx, row in df.iterrows():
            desvio = row['rMSSD'] - row['Baseline']
            if desvio > -0.5 * std_atleta:
                colores.append('#27ae60') # Verde (Ready)
            elif desvio > -1.5 * std_atleta:
                colores.append('#f1c40f') # Amarillo (Precaución)
            else:
                colores.append('#e74c3c') # Rojo (Descanso)
        df['Color'] = colores
        lista_df.append(df)
        
    return pd.concat(lista_df)

# Cargar todos los datos
df_todos = generar_datos_atletas()

# 2. Sidebar para Filtros (Atleta + Estados)
st.sidebar.header('🎛️ Filtros de Control')

# NUEVO: Selector de Atleta
atleta_seleccionado = st.sidebar.selectbox(
    'Selecciona el Atleta:',
    options=df_todos['Atleta'].unique()
)

# Filtro secundario por estado
estados = st.sidebar.multiselect(
    'Filtrar Estado Visual:', 
    ['Verde (Ready)', 'Amarillo (Precaución)', 'Rojo (Descanso)'], 
    default=['Verde (Ready)', 'Amarillo (Precaución)', 'Rojo (Descanso)']
)

# Mapear estados a hexadecimal
mapa_colores = {
    'Verde (Ready)': '#27ae60',
    'Amarillo (Precaución)': '#f1c40f',
    'Rojo (Descanso)': '#e74c3c'
}
colores_filtrados = [mapa_colores[e] for e in estados]

# Aplicar filtros encadenados (Primero atleta, luego estados)
df_atleta = df_todos[df_todos['Atleta'] == atleta_seleccionado]
std_sim = df_atleta['rMSSD'].std() # Desviación típica específica del atleta elegido

df_filtrado = df_atleta[df_atleta['Color'].isin(colores_filtrados)]

# 3. Métricas principales con la lógica de color del atleta elegido
if not df_filtrado.empty:
    last = df_filtrado.iloc[-1]
    
    # Estructura de 3 columnas para el estado diario
    col1, col2, col3 = st.columns(3)
    col1.metric(label=f"rMSSD Hoy ({atleta_seleccionado})", value=f"{last['rMSSD']} ms")
    col2.metric(label="Línea Base (7d)", value=f"{last['Baseline']} ms")
    
    # Lógica de color del Semáforo en la métrica
    if last['Color'] == '#27ae60':
        estado_texto = "🟢 Verde (Ready)"
    elif last['Color'] == '#f1c40f':
        estado_texto = "🟡 Amarillo (Precaución)"
    else:
        estado_texto = "🔴 Rojo (Descanso)"
        
    col3.metric(label="Disposición Diaria", value=estado_texto)

st.divider()

# 4. Gráfico de Tendencias adaptado al Atleta con Semáforo
if not df_filtrado.empty:
    st.subheader(f"📊 Evolución Temporal - {atleta_seleccionado}")
    
    fig, ax = plt.subplots(figsize=(15, 6))
    
    # Sombreado de la zona de confort basado en el atleta seleccionado
    ax.fill_between(df_filtrado['Fecha'], df_filtrado['Baseline'] - 0.5*std_sim, df_filtrado['Baseline'] + 0.5*std_sim, color='gray', alpha=0.1, label='Rango Normal')
    
    # Línea base intermitente
    ax.plot(df_filtrado['Fecha'], df_filtrado['Baseline'], color='#e67e22', linestyle='--', linewidth=2, label='Línea Base (7d)')
    
    # Línea continua gris que une los puntos del deportista
    ax.plot(df_filtrado['Fecha'], df_filtrado['rMSSD'], color='#bdc3c7', alpha=0.6, zorder=2)
    
    # Puntos coloreados dinámicamente con el semáforo de fatiga
    ax.scatter(df_filtrado['Fecha'], df_filtrado['rMSSD'], color=df_filtrado['Color'], s=120, edgecolors='black', linewidth=1, zorder=3)
    
    # Estética limpia
    ax.set_title(f"ANÁLISIS DE CARGA INTERNA: {atleta_seleccionado.upper()}", fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel("rMSSD (ms)", fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Leyenda personalizada
    legend_elements = [
        Line2D([0], [0], color='#e67e22', linestyle='--', label='Línea Base'),
        Line2D([0], [0], marker='o', color='w', label='Verde (Ready)', markerfacecolor='#27ae60', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Amarillo (Precaución)', markerfacecolor='#f1c40f', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Rojo (Descanso)', markerfacecolor='#e74c3c', markersize=10)
    ]
    ax.legend(handles=legend_elements, loc='upper left', frameon=True)
    
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.warning("Selecciona al menos un estado en la barra lateral para renderizar los datos.")

# 5. Tabla de datos filtrada
st.subheader('📋 Historial de Registros')
st.dataframe(df_filtrado[['Fecha', 'Atleta', 'rMSSD', 'Baseline']].sort_values('Fecha', ascending=False), use_container_width=True)
