import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np

from dash.dependencies import Input, Output
from plotly import graph_objs as go
from plotly.graph_objs import *
from datetime import datetime as dt


app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server


# Plotly mapbox public token
mapbox_access_token = "pk.eyJ1IjoicGFibG9lbWFudWVsbCIsImEiOiJja2hzZmhzZDkwZnk3MzRvNWh1MzV4b2MyIn0.yQ_6iq1pk9DXqqFydgzCBg"

# Localizações importantes
# Código retirado de https://gist.github.com/ricardobeat/674646
list_of_locations = {
	"AC": [-8.77, -70.55],
	"AL": [-9.62, -36.82],
	"AM": [-3.47, -65.10],
	"AP": [1.41, -51.77],
	"BA": [-13.29, -41.71],
	"CE": [-5.20, -39.53],
	"DF": [-15.83, -47.86],
	"ES": [-19.19, -40.34],
	"GO": [-15.98, -49.86],
	"MA": [-5.42, -45.44],
	"MT": [-12.64, -55.42],
	"MS": [-20.51, -54.54],
	"MG": [-18.10, -44.38],
	"PA": [-3.79, -52.48],
	"PB": [-7.28, -36.72],
	"PR": [-24.89, -51.55],
	"PE": [-8.38, -37.86],
	"PI": [-6.60, -42.28],
	"RJ": [-22.25, -42.66],
	"RN": [-5.81, -36.59],
	"RO": [-10.83, -63.34],
	"RS": [-30.17, -53.50],
	"RR": [1.99, -61.33],
	"SC": [-27.45, -50.95],
	"SE": [-10.57, -37.45],
	"SP": [-22.19, -48.79],
	"TO": [-9.46, -48.26]
}

# Initialize data frame
df = pd.read_csv(
    "./data/acidentes.csv",
    index_col='id'
)

df.data_inversa = df.data_inversa.astype('datetime64')
df['data'] = df.data_inversa.dt.strftime("%d/%m/%Y")
df['horario'] = df.data_inversa.dt.strftime("%H:%M")

# Layout of Dash App
app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.H2("ACIDENTES EM RODOVIAS FEDERAIS"),
                        html.P(
                            """Escolha intevalos de data no menu de seleção abaixo ou intervalos de horário no histograma."""
                        ),
                        html.Span(
                            "Data inicial"
                        ),
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                dcc.DatePickerSingle(
                                    id="start-date-picker",
                                    min_date_allowed=dt(2020, 1, 1),
                                    max_date_allowed=dt(2020, 9, 30),
                                    initial_visible_month=dt(2020, 1, 1),
                                    date=dt(2020, 1, 1).date(),
                                    display_format="DD/MM/YYYY",
                                    style={"border": "0px solid black"},
                                )
                            ],
                        ),
                        html.Span(
                            "Data Final"
                        ),
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                dcc.DatePickerSingle(
                                    id="end-date-picker",
                                    min_date_allowed=dt(2020, 1, 1),
                                    max_date_allowed=dt(2020, 9, 30),
                                    initial_visible_month=dt(2020, 11, 20),
                                    date=dt(2020, 11, 20).date(),
                                    display_format="DD/MM/YYYY",
                                    style={"border": "0px solid black"},
                                )
                            ],
                        ),
                        # Change to side-by-side for mobile layout
                        html.Div(
                            className="row",
                            children=[
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        # Dropdown for locations on map
                                        dcc.Dropdown(
                                            id="location-dropdown",
                                            options=[
                                                {"label": i, "value": i}
                                                for i in list_of_locations
                                            ],
                                            placeholder="Selecione a UF",
                                        )
                                    ],
                                ),
                                html.Span(
                                    "Obs.: A UF não afeta os dados apresentados"
                                ),
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        # Dropdown to select times
                                        dcc.Dropdown(
                                            id="bar-selector",
                                            options=[
                                                {
                                                    "label": str(n) + ":00",
                                                    "value": str(n),
                                                }
                                                for n in range(24)
                                            ],
                                            multi=True,
                                            placeholder="Selecione os horários",
                                        )
                                    ],
                                ),
                            ],
                        ),
                        html.P(id="total-acidentes"),
                        html.P(id="total-acidentes-selection"),
                        dcc.Markdown(
                            children=[
                                "Fonte: [Polícia Rodoviária Federal](https://antigo.prf.gov.br/dados-abertos-acidentes)  ",
                                "Layout feito pela comunidade do Plotly, disponível na [Galeria do Dash](https://dash-gallery.plotly.host/Portal/)."
                            ]
                        ),
                    ],
                ),
                # Column for app graphs and plots
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Graph(id="map-graph"),
                        html.Div(
                            className="text-padding",
                            children=[
                                "Use as barras do histograma para selecionar os horários."
                            ],
                        ),
                        dcc.Graph(id="histogram"),
                    ],
                ),
            ],
        )
    ]
)

# Get the amount of acidentes per hour based on the time selected
# This also higlights the color of the histogram bars based on
# if the hours are selected
def get_selection(data, selection):
    xVal = []
    yVal = []
    xSelected = []
    colorVal = [
        "#F4EC15",
        "#DAF017",
        "#BBEC19",
        "#9DE81B",
        "#80E41D",
        "#66E01F",
        "#4CDC20",
        "#34D822",
        "#24D249",
        "#25D042",
        "#26CC58",
        "#28C86D",
        "#29C481",
        "#2AC093",
        "#2BBCA4",
        "#2BB5B8",
        "#2C99B4",
        "#2D7EB0",
        "#2D65AC",
        "#2E4EA4",
        "#2E38A4",
        "#3B2FA0",
        "#4E2F9C",
        "#603099",
    ]

    # Put selected times into a list of numbers xSelected
    xSelected.extend([int(x) for x in selection])

    for i in range(24):
        # If bar is selected then color it white
        if i in xSelected and len(xSelected) < 24:
            colorVal[i] = "#FFFFFF"
        xVal.append(i)
        # Get the number of acidentes at a particular time
        yVal.append(data[data.data_inversa.dt.hour == i].shape[0])
    return [np.array(xVal), np.array(yVal), np.array(colorVal)]


# Selected Data in the Histogram updates the Values in the DatePicker
@app.callback(
    Output("bar-selector", "value"),
    [Input("histogram", "selectedData"), Input("histogram", "clickData")],
)
def update_bar_selector(value, clickData):
    holder = []
    if clickData:
        holder.append(str(int(clickData["points"][0]["x"])))
    if value:
        for x in value["points"]:
            holder.append(str(int(x["x"])))
    return list(set(holder))


# Clear Selected Data if Click Data is used
@app.callback(Output("histogram", "selectedData"), [Input("histogram", "clickData")])
def update_selected_data(clickData):
    if clickData:
        return {"points": []}

@app.callback(Output("end-date-picker", "min_date_allowed"),[Input("start-date-picker", "date")])
def update_valid_end_date(startDatePicked): 
    return startDatePicked

@app.callback(Output("start-date-picker", "max_date_allowed"),[Input("end-date-picker", "date")])
def update_valid_end_date(endDatePicked): 
    return endDatePicked


# Update the total number of acidentes Tag
@app.callback(Output("total-acidentes", "children"), [Input("start-date-picker", "date"), Input("end-date-picker", "date")])
def update_total_acidentes(startDatePicked, endDatePicked):
    start_date_picked = dt.strptime(startDatePicked, "%Y-%m-%d")
    end_date_picked = dt.strptime(endDatePicked, "%Y-%m-%d")
    total = ((df.data_inversa >= start_date_picked) & (df.data_inversa <= end_date_picked)).sum()
    return f"Número total de acidentes: {total}"


# Update the total number of acidentes in selected times
@app.callback(
    Output("total-acidentes-selection", "children"),
    [Input("start-date-picker", "date"), Input("end-date-picker", "date"), Input("bar-selector", "value")],
)
def update_total_acidentes_selection(startDatePicked, endDatePicked, selectedData):
    start_date_picked = dt.strptime(startDatePicked, "%Y-%m-%d")
    end_date_picked = dt.strptime(endDatePicked, "%Y-%m-%d")
    total = 0
    if(selectedData != None and selectedData != []):
        total = ((df.data_inversa >= start_date_picked) & (df.data_inversa <= end_date_picked) & 
        (df.data_inversa.dt.hour.isin(selectedData))).sum()
    else: 
        total = ((df.data_inversa >= start_date_picked) & (df.data_inversa <= end_date_picked)).sum()
    
    return f"Número total de acidentes nos horários selecionados: {total}"


# Update Histogram Figure based on Month, Day and Times Chosen
@app.callback(
    Output("histogram", "figure"),
    [Input("start-date-picker", "date"), Input("end-date-picker", "date"), Input("bar-selector", "value")],
)
def update_histogram(startDatePicked, endDatePicked, selectedData):

    start_date_picked = dt.strptime(startDatePicked, "%Y-%m-%d")
    end_date_picked = dt.strptime(endDatePicked, "%Y-%m-%d")

    data = df[(df.data_inversa >= start_date_picked) & (df.data_inversa <= end_date_picked)]
    if(selectedData != None and selectedData != []):
        data = data[data.data_inversa.dt.hour.isin(selectedData)]

    [xVal, yVal, colorVal] = get_selection(data, selectedData)
    
    layout = go.Layout(
        bargap=0.01,
        bargroupgap=0,
        barmode="group",
        margin=go.layout.Margin(l=10, r=0, t=0, b=50),
        showlegend=False,
        plot_bgcolor="#323130",
        paper_bgcolor="#323130",
        dragmode="select",
        font=dict(color="white"),
        xaxis=dict(
            range=[-0.5, 23.5],
            showgrid=False,
            nticks=25,
            fixedrange=True,
            ticksuffix=":00",
        ),
        yaxis=dict(
            range=[0, max(yVal) + max(yVal) / 4],
            showticklabels=False,
            showgrid=False,
            fixedrange=True,
            rangemode="nonnegative",
            zeroline=False,
        ),
        annotations=[
            dict(
                x=xi,
                y=yi,
                text=str(yi),
                xanchor="center",
                yanchor="bottom",
                showarrow=False,
                font=dict(color="white"),
            )
            for xi, yi in zip(xVal, yVal)
        ],
    )

    return go.Figure(
        data=[
            go.Bar(x=xVal, y=yVal, marker=dict(color=colorVal), hoverinfo="x"),
            go.Scatter(
                opacity=0,
                x=xVal,
                y=yVal / 2,
                hoverinfo="none",
                mode="markers",
                marker=dict(color="rgb(66, 134, 244, 0)", symbol="square", size=40),
                visible=True,
            ),
        ],
        layout=layout,
    )


# Update Map Graph based on date-picker, selected data on histogram and location dropdown
@app.callback(
    Output("map-graph", "figure"),
    [
        Input("start-date-picker", "date"),
        Input("end-date-picker", "date"),
        Input("bar-selector", "value"),
        Input("location-dropdown", "value"),
    ],
)
def update_graph(startDatePicked, endDatePicked, selectedData, selectedLocation):
    zoom = 7.0
    latInitial = list_of_locations["RN"][0]
    lonInitial = list_of_locations["RN"][1]
    bearing = 0

    if selectedLocation:
        zoom = 7.0
        latInitial = list_of_locations[selectedLocation][0]
        lonInitial = list_of_locations[selectedLocation][1]

    start_date_picked = dt.strptime(startDatePicked, "%Y-%m-%d")
    end_date_picked = dt.strptime(endDatePicked, "%Y-%m-%d")

    data = df[(df.data_inversa >= start_date_picked) & (df.data_inversa <= end_date_picked)]
    if(selectedData != None and selectedData != []):
        data = data[data.data_inversa.dt.hour.isin(selectedData)]

    return go.Figure(
        data=[
            # Data for all acidentes based on date and time
            Scattermapbox(
                lat=data.latitude,
                lon=data.longitude,
                mode="markers",
                customdata=data[['causa_acidente', 'tipo_acidente','classificacao_acidente', 'data', 'condicao_metereologica',
                    "pessoas", "mortos", "feridos_leves", "feridos_graves", "ilesos", "ignorados", "veiculos", "horario"
                ]],
                hovertemplate = "<extra></extra>"+
                    "Causa: %{customdata[0]}<br>Tipo: %{customdata[1]}<br>Classificacao: %{customdata[2]}<br>"+
                    "Horário:%{customdata[12]}<br>Data: %{customdata[3]}<br>Condição meteorológica: %{customdata[4]}<br>"+
                    "Pessoas: %{customdata[5]}<br>Mortos: %{customdata[6]}<br>Feridos leves: %{customdata[7]}<br>"+
                    "Feridos graves: %{customdata[8]}<br>Ilesos: %{customdata[9]}<br>Ignorados: %{customdata[10]}<br>"+
                    "Veiculos: %{customdata[11]}",
                marker=dict(
                    showscale=True,
                    color=pd.concat([pd.Series([0]), data.data_inversa.dt.hour,  pd.Series([23])]),
                    opacity=0.5,
                    size=5,
                    colorscale=[
                        [0, "#F4EC15"],
                        [0.04167, "#DAF017"],
                        [0.0833, "#BBEC19"],
                        [0.125, "#9DE81B"],
                        [0.1667, "#80E41D"],
                        [0.2083, "#66E01F"],
                        [0.25, "#4CDC20"],
                        [0.292, "#34D822"],
                        [0.333, "#24D249"],
                        [0.375, "#25D042"],
                        [0.4167, "#26CC58"],
                        [0.4583, "#28C86D"],
                        [0.50, "#29C481"],
                        [0.54167, "#2AC093"],
                        [0.5833, "#2BBCA4"],
                        [1.0, "#613099"],
                    ],
                    colorbar=dict(
                        title="Horário",
                        x=0.93,
                        xpad=0,
                        nticks=24,
                        tickfont=dict(color="#d8d8d8"),
                        titlefont=dict(color="#d8d8d8"),
                        thicknessmode="pixels",
                    ),
                ),
            ),
            # Plot of important locations on the map
            Scattermapbox(
                lat=[list_of_locations[i][0] for i in list_of_locations],
                lon=[list_of_locations[i][1] for i in list_of_locations],
                mode="markers",
                hoverinfo="text",
                text=[i for i in list_of_locations],
                marker=dict(size=8, color="#ffa0a0"),
            ),
        ],
        layout=Layout(
            autosize=True,
            margin=go.layout.Margin(l=0, r=35, t=0, b=0),
            showlegend=False,
            mapbox=dict(
                accesstoken=mapbox_access_token,
                center=dict(lat=latInitial, lon=lonInitial),
                style="dark",
                bearing=bearing,
                zoom=zoom,
            ),
            updatemenus=[
                dict(
                    buttons=(
                        [
                            dict(
                                args=[
                                    {
                                        "mapbox.zoom": 12,
                                        "mapbox.center.lon": "-73.991251",
                                        "mapbox.center.lat": "40.7272",
                                        "mapbox.bearing": 0,
                                        "mapbox.style": "dark",
                                    }
                                ],
                                label="Reset Zoom",
                                method="relayout",
                            )
                        ]
                    ),
                    direction="left",
                    pad={"r": 0, "t": 0, "b": 0, "l": 0},
                    showactive=False,
                    type="buttons",
                    x=0.45,
                    y=0.02,
                    xanchor="left",
                    yanchor="bottom",
                    bgcolor="#323130",
                    borderwidth=1,
                    bordercolor="#6d6d6d",
                    font=dict(color="#FFFFFF"),
                )
            ],
        ),
    )


if __name__ == "__main__":
    app.run_server(debug=False)
