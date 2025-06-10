import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configuración de página
st.set_page_config(
    page_title='Ebed - División de Honor G5',
    layout="wide",
    page_icon="⚽"
)

# Cargar datos
@st.cache_data
def load_data():
    return pd.read_csv('DH_G5_Players/G5_DH_Players.csv')

df = load_data()

# Función para crear gráfico de radar con colores por impacto
def create_radar_chart_real(df_selected, df_mean_pos, players, with_mean=False):
    categories = ['Goles_por_partido', 'RC', 'IDR', 'Impacto_Total']

    fig = go.Figure()

    max_impact = df['Impacto_Total'].max()
    min_impact = df['Impacto_Total'].min()

    # Añadir cada jugador seleccionado con color en degradado
    for player in players:
        player_data = df_selected[df_selected['Nombre'] == player]
        values = [player_data[col].values[0] for col in categories]

        # Asignar color basado en el impacto
        impacto = player_data['Impacto_Total'].values[0]
        color_scale = (impacto - min_impact) / (max_impact - min_impact)
        color = px.colors.sample_colorscale("Turbo", [color_scale])[0]

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=player,
            line=dict(color=color)
        ))

    # Añadir media de posición si corresponde
    if with_mean and not df_mean_pos.empty:
        mean_values = [df_mean_pos[col].values[0] for col in categories]
        fig.add_trace(go.Scatterpolar(
            r=mean_values + [mean_values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=f"Media {df_mean_pos['Posicion'].values[0]}",
            line=dict(color='gray', dash='dot')
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True
            )),
        showlegend=True,
        title="Comparativa de Jugadores" if not with_mean else "Comparativa con Media de Posición"
    )

    return fig

# Función para crear scatter plot con colores en degradado
def create_scatter_plot(filtered_df):
    max_impact = df['Impacto_Total'].max()
    min_impact = df['Impacto_Total'].min()

    color_scale = (filtered_df['Impacto_Total'] - min_impact) / (max_impact - min_impact)
    colors = px.colors.sample_colorscale("Turbo", color_scale)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=filtered_df['Impacto_Total'],
        y=filtered_df['RC'],
        mode='markers+text',
        marker=dict(size=12, color=colors),
        text=filtered_df['Nombre'],
        textposition='top center',
        name='Jugadores'
    ))

    fig.update_layout(
        title='Impacto Total vs RC (Colores por Impacto)',
        xaxis_title='Impacto Total',
        yaxis_title='RC',
        showlegend=False
    )

    return fig

def main():
    st.title('División de Honor G5')
    st.header('Estadísticas avanzadas de la liga de DH')

    # --- FILTROS GENERALES ---
    st.sidebar.header('Filtros Generales')

    posiciones = df['Posicion'].unique()
    posicion_seleccionada = st.sidebar.multiselect(
        'Posición:',
        options=posiciones,
        default=posiciones
    )

    equipos = df['Equipo'].unique()
    equipo_seleccionado = st.sidebar.multiselect(
        'Equipo:',
        options=equipos,
        default=equipos
    )

    filtered_df = df[
        (df['Posicion'].isin(posicion_seleccionada)) &
        (df['Equipo'].isin(equipo_seleccionado))
    ]

    # --- SELECTOR DE JUGADORES ---
    st.sidebar.header("Comparativa de Radar")
    jugadores_disponibles = filtered_df['Nombre'].unique()
    jugadores_seleccionados = st.sidebar.multiselect(
        'Selecciona jugadores (máx 5):',
        options=jugadores_disponibles,
        default=[],
        max_selections=5
    )

    if jugadores_seleccionados:
        df_selected = filtered_df[filtered_df['Nombre'].isin(jugadores_seleccionados)]

        posicion_comparar = df_selected['Posicion'].iloc[0]
        df_pos_filtrada = filtered_df[filtered_df['Posicion'] == posicion_comparar]

        categorias = ['Goles_por_partido', 'RC', 'IDR', 'Impacto_Total']

        mean_values = df_pos_filtrada[categorias].mean()
        mean_values['Posicion'] = posicion_comparar
        df_mean_pos = pd.DataFrame([mean_values])

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Comparativa entre Jugadores (Valores Reales)")
            fig_jugadores = create_radar_chart_real(df_selected, pd.DataFrame(), jugadores_seleccionados, with_mean=False)
            st.plotly_chart(fig_jugadores, use_container_width=True)

        with col2:
            st.subheader(f"Comparativa con la Media de {posicion_comparar} (Valores Reales)")
            fig_comparativa = create_radar_chart_real(df_selected, df_mean_pos, jugadores_seleccionados, with_mean=True)
            st.plotly_chart(fig_comparativa, use_container_width=True)

        st.subheader('Resumen de Partidos Jugados y Goles')
        resumen_df = df_selected[['Nombre', 'Partidos_jugados', 'Goles']].copy()

        media_partidos = df_pos_filtrada['Partidos_jugados'].mean()
        media_goles = df_pos_filtrada['Goles'].mean()

        media_row = pd.DataFrame([{
            'Nombre': f'Media {posicion_comparar}',
            'Partidos_jugados': round(media_partidos, 2),
            'Goles': round(media_goles, 2)
        }])

        resumen_df = pd.concat([resumen_df, media_row], ignore_index=True)

        st.dataframe(resumen_df, hide_index=True, use_container_width=True)

    # --- TABLA DE DATOS COMPLETA ---
    st.subheader('Tabla Completa Filtrada')
    st.dataframe(
        filtered_df,
        height=600,
        use_container_width=True,
        hide_index=True,
        column_order=['Nombre', 'Posicion', 'Equipo', 'Partidos_jugados',
                      'Goles', 'Goles_por_partido', 'Aporte_Goles',
                      'RC', 'IDR', 'Impacto_Total']
    )

    # --- SCATTER PLOT CON FILTROS PROPIOS ---
    st.markdown('---')
    st.subheader('Análisis de Impacto Total vs RC')

    st.markdown('### Filtros Scatter Plot')

    scatter_posiciones = st.multiselect(
        'Posiciones (Scatter Plot):',
        options=df['Posicion'].unique(),
        default=df['Posicion'].unique()
    )

    scatter_equipos = st.multiselect(
        'Equipos (Scatter Plot):',
        options=df['Equipo'].unique(),
        default=df['Equipo'].unique()
    )

    scatter_df = df[
        (df['Posicion'].isin(scatter_posiciones)) &
        (df['Equipo'].isin(scatter_equipos))
    ]

    scatter_fig = create_scatter_plot(scatter_df)
    st.plotly_chart(scatter_fig, use_container_width=True)

    # --- TOP 10 JUGADORES ---
    st.markdown('---')
    st.subheader('Top 10 Jugadores por Impacto Total')

    top_10_df = df.sort_values(by='Impacto_Total', ascending=False).head(10)[
        ['Nombre', 'Equipo', 'Posicion', 'Partidos_jugados', 'Goles', 'Impacto_Total']
    ]

    st.dataframe(top_10_df, hide_index=True, use_container_width=True)

if __name__ == '__main__':
    main()
