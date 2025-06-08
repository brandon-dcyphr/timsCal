# %%
# Load libraries
import pandas as pd
from dash import Dash, dcc, html, Input, Output, callback
import sqlite3
import plotly.express as px
import plotly
import lxml
import numpy as np
import os

pd.options.mode.chained_assignment = None  # default='warn'

# %%
# Process history.sqlite Data
import sqlite3
import pandas as pd
# Import data
con = sqlite3.connect("C:/Data_analysis/timsQC/history.sqlite")
cur = con.cursor()
data = pd.read_sql_query(f"SELECT * FROM InstrumentParameterHistory", con)

data[['Date', 'Time']] = data['DateTime'].str.split('T', expand=True)
# MZ cal
mzCal = data[data['Comment'].str.contains("Calibration of type 'm/z'")]
mzCal[['score']] = mzCal['Comment'].str.extract(fr'{"score"}\s+(.*?)\s+{"absolute"}')
mzCal['score'] = mzCal['score'].str.strip("'")
mzCal['score'] = mzCal['score'].str.replace(r'%.*$',"",regex=True)
mzCal['score'] = pd.to_numeric(mzCal['score'], errors='coerce')
mzCal[['relative_deviation']] = mzCal['Comment'].str.extract(fr'{"relative deviation"}\s+(.*?)\s+')
mzCal['relative_deviation'] = mzCal['relative_deviation'].str.strip("'")
mzCal['relative_deviation'] = pd.to_numeric(mzCal['relative_deviation'], errors='coerce')

# Mobility
mobCal = data[data['Comment'].str.contains("Calibration of type 'mobility'")]
mobCal[['score']] = mobCal['Comment'].str.extract(fr'{"score"}\s+(.*?)\s+{"and"}')
mobCal['score'] = mobCal['score'].str.strip("'")
mobCal['score'] = mobCal['score'].str.replace("%","",regex=False)
mobCal['score'] = pd.to_numeric(mobCal['score'], errors='coerce')
mobCal[['relative_deviation']] = mobCal['Comment'].str.extract(fr'{"deviation"}\s+(.*?)\s+')
mobCal['relative_deviation'] = mobCal['relative_deviation'].str.strip("'")
mobCal['relative_deviation'] = pd.to_numeric(mobCal['relative_deviation'], errors='coerce')

# ToF Tuning
tofTuning = data[data['Comment'].str.contains("TofDetectorTuning")]
# Cap cleaning
capCleaning = data[data['Comment'].str.contains("Update capillary cleaning date")]

# Make data wide for heatmaps
mobCal_wide = mobCal.pivot(columns='Date', index='Time', values='score')

mobCal['Date'] = pd.to_datetime(mobCal['Date'])
mzCal['Date'] = pd.to_datetime(mzCal['Date'])

# %%
# file list walker function

def get_files_one_level_deep(directory, file_extension):
    """
    Gets a list of files with a specific extension within a directory,
    recursively, but only one level deep.

    Args:
        directory (str): The path to the directory to search.
        file_extension (str): The file extension to look for (e.g., ".txt").

    Returns:
        list: A list of file paths that match the criteria.
    """
    matching_files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and item.lower().endswith(file_extension):
            matching_files.append(item_path)
        elif os.path.isdir(item_path):
            for sub_item in os.listdir(item_path):
              sub_item_path = os.path.join(item_path, sub_item)
              if os.path.isfile(sub_item_path) and sub_item.lower().endswith(file_extension):
                  matching_files.append(sub_item_path)
    return matching_files

# %%
# XML importer for ISO-8859-1

import xml.etree.ElementTree as ET

def parse_xml_iso_8859_1(filename):
    """Parses an XML file with ISO-8859-1 encoding."""
    try:
        tree = ET.parse(filename)
        return tree
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Example usage:
xml_file = "../new_microTOFQImpacTemAcquisition.method"  # Replace with your file path
tree_element = parse_xml_iso_8859_1(xml_file)
root_element = tree_element.getroot()

# %%
# Imports from .method file

target_directory = "./InstrumentHistory"  # Replace with your directory path
target_extension = ".method"  # Replace with your desired file extension
methList = get_files_one_level_deep(target_directory, target_extension)

massCalMaster=pd.DataFrame()
massCalMaster_wide=pd.DataFrame()
mobilityCalMaster=pd.DataFrame()
for i in methList:
    # print(i)
    CalLists = []
    CalVals = []   
    tree_element = parse_xml_iso_8859_1(i)
    root_element = tree_element.getroot()
    tree=tree_element
    root=root_element
# transfers XML structure to dataframes for positive calibrations ONLY
    for container in root.findall('instrument/qtofimpactemacq/'):
        for element in container.iter('dependent'):
            if element.get('polarity')=='positive' and element.get('source') is None:
                # print(element.get('source'))
                # numbers (para_double)
                for item in element.findall('para_double'):
                    child_dict = {}
                    child_dict['tag'] = item.get('permname')
                    child_dict['value'] = item.get('value')
                    child_dict['file'] = i
                    if item.text:
                        child_dict['text'] = item.text.strip()
                    CalVals.append(child_dict)
                # numbers (para_int)
                for item in element.findall('para_int'):
                    child_dict = {}
                    child_dict['tag'] = item.get('permname')
                    child_dict['value'] = item.get('value')
                    child_dict['file'] = i
                    if item.text:
                        child_dict['text'] = item.text.strip()
                    CalVals.append(child_dict)
                # strings (para_string)
                for item in element.findall('para_string'):
                    child_dict = {}
                    child_dict['tag'] = item.get('permname')
                    child_dict['value'] = item.get('value')
                    child_dict['file'] = i
                    if item.text:
                        child_dict['text'] = item.text.strip()
                    CalVals.append(child_dict)
                # lists (para_vec_double)
                for item in element.findall('para_vec_double'):
                    for child in item:
                        child_dict = {}
                        child_dict['tag'] = item.get('permname')
                        child_dict['value'] = child.get('value')
                        child_dict['file'] = i
                        if child.text:
                            child_dict['text'] = child.text.strip()
                        CalVals.append(child_dict)
    #df_CalVals=pd.json_normalize(CalVals) # single values
    df_CalVals=pd.DataFrame(CalVals)
    # write raw file 
    filename=i.replace("../", "")
    df_CalVals.to_csv(f'C:/Data_analysis/timsQC/timsCal/{filename}.csv', header=None, index=None, sep=',', mode='w')
        
# Separation
# MassCal
    massCal_df=df_CalVals[df_CalVals['tag'].isin(['Calibration_LastCalibrationDate',
                                            'Calibration_Score',
                                            'Calibration_StdDev',
                                            'Calibration_StdDevInPPM',
                                            'Calibration_LastCalibrationCurrentMass'])]

    massCalFrame_df=df_CalVals[df_CalVals['tag'].isin(['Calibration_LastCalibrationReferenceMass',
                                                    'Calibration_LastCalibrationCurrentMass',
                                                    'Calibration_LastCalibrationMassError',
                                                    'Calibration_LastCalibrationMassIntensity',
                                                    'file'])]
    massCalFrame_df['dateTag'] = massCalFrame_df['file'].str.replace(r'^.*?\\', '', regex=True)
    massCalFrame_df['dateTag'] = massCalFrame_df['dateTag'].str.replace(r'\\.*?$', '', regex=True)
    calDate=df_CalVals[df_CalVals['tag'].isin(['Calibration_LastCalibrationDate'])]['value']
    calDate=calDate.tolist()
    # print(calDate)
    massCalFrame_df=massCalFrame_df.assign(date=calDate[0])
    massCalFrame_df.insert(1, 'tagRep', massCalFrame_df.groupby('tag').cumcount() + 1)
    massCalFrame_df['tag'] = massCalFrame_df.apply(lambda x: x['tag'].replace('Calibration_LastCalibration', ''), axis=1)
    #massCalFrame_df.insert(1, 'seq', massCalFrame_df.groupby('dateTag').cumcount() + 1)
    massCalFrame_df.insert(1, 'seq', value=np.arange(len(massCalFrame_df)) + 1)
    massCalFrame_df['date']=massCalFrame_df['date'].str.replace(r'T.*', '', regex=True)
# Mobility
    mobilityCal_df=df_CalVals[df_CalVals['tag'].isin(['IMS_Calibration_LastCalibrationDate',
                                                    'IMS_Calibration_LastCalibrationReferenceMassList',
                                                    'IMS_Calibration_Score',
                                                    'IMS_Calibration_StdDev'])]

    mobilityCalFrame_df=df_CalVals[df_CalVals['tag'].isin(['IMS_Calibration_LastCalibrationReferenceMass',
                                                    'IMS_Calibration_LastCalibrationReferenceMobility',
                                                    'IMS_Calibration_LastCalibrationResultMobility',
                                                    'IMS_Calibration_LastCalibrationMassIntensity'])]
    mobilityCalFrame_df['dateTag'] = mobilityCalFrame_df['file'].str.replace(r'^.*?\\', '', regex=True)
    mobilityCalFrame_df['dateTag'] = mobilityCalFrame_df['dateTag'].str.replace(r'\\.*?$', '', regex=True)
    calDate=df_CalVals[df_CalVals['tag'].isin(['IMS_Calibration_LastCalibrationDate'])]['value']
    calDate=calDate.tolist()
    # print(calDate)
    mobilityCalFrame_df=mobilityCalFrame_df.assign(date=calDate[0])
    mobilityCalFrame_df.insert(1, 'tagRep', mobilityCalFrame_df.groupby('tag').cumcount() + 1)
    mobilityCalFrame_df['tag'] = mobilityCalFrame_df.apply(lambda x: x['tag'].replace('IMS_Calibration_LastCalibration', ''), axis=1)
    #mobilityCalFrame_df.insert(1, 'seq', mobilityCalFrame_df.groupby('dateTag').cumcount() + 1)
    mobilityCalFrame_df.insert(1, 'seq', value=np.arange(len(mobilityCalFrame_df)) + 1)
    mobilityCalFrame_df['date']=mobilityCalFrame_df['date'].str.replace(r'T.*', '', regex=True)

    # mobilityCalFrame_df['tag'] = mobilityCalFrame_df.apply(lambda x: x['tag'].replace('IMS_Calibration_LastCalibration', ''), axis=1)
    # mobilityCalFrame_df.insert(1, 'seq', mobilityCalFrame_df.groupby('tag').cumcount() + 1)
    # calDate=df_CalVals[df_CalVals['tag'].isin(['IMS_Calibration_LastCalibrationDate'])]['value']
    # calDate=calDate.tolist()
    # mobilityCalFrame_df=mobilityCalFrame_df.assign(date=calDate[0])
    # mobilityCalFrame_wide_df=mobilityCalFrame_df.pivot(index='seq', columns='tag', values='value')
    # mobilityCalFrame_wide_df=mobilityCalFrame_wide_df.assign(date=calDate[0])
    # mobilityCalFrame_wide_df['date']=mobilityCalFrame_wide_df['date'].str.replace(r'T.*', '', regex=True)
    # mobilityCalFrame_df['date']=mobilityCalFrame_df['date'].str.replace(r'T.*', '', regex=True)

    tofCal_df=df_CalVals[df_CalVals['tag'].isin(['TOF_DetectorTof_LastCalibrationDate',
                                                'Calibration_Tof2Score',
                                                'Calibration_Tof2StdDev',
                                                'Calibration_Tof2StdDevInPPM'])]

    quadCal=df_CalVals[df_CalVals['tag'].isin(['Quadrupole_Ramping_LastCalibrationDate'])]

    massCalMaster=pd.concat([massCalMaster, massCalFrame_df])
    mobilityCalMaster=pd.concat([mobilityCalMaster, mobilityCalFrame_df])


# %%
# reformatting
massCalMaster['value']=massCalMaster['value'].astype('float')
massCalMaster['tagRep']=massCalMaster['tagRep'].astype('string')
massCalMaster['tagGroup']=massCalMaster['dateTag']+'_'+massCalMaster['tagRep']

mobilityCalMaster['value']=mobilityCalMaster['value'].astype('float')
mobilityCalMaster['tagRep']=mobilityCalMaster['tagRep'].astype('string')
mobilityCalMaster['tagGroup']=mobilityCalMaster['dateTag']+'_'+mobilityCalMaster['tagRep']

# Make wide
massCalMaster_wide=massCalMaster.pivot_table(index='tagGroup', columns='tag', values='value')
massCalMaster_wide = pd.merge(massCalMaster_wide, massCalMaster[['tagGroup', 'date', 'dateTag']].drop_duplicates(), on='tagGroup', how='left')

mobilityCalMaster_wide=mobilityCalMaster.pivot_table(index='tagGroup', columns='tag', values='value')
mobilityCalMaster_wide = pd.merge(mobilityCalMaster_wide, mobilityCalMaster[['tagGroup', 'date', 'dateTag']].drop_duplicates(), on='tagGroup', how='left')

# # long format for callback compatibility
massCalMaster_long=pd.melt(mobilityCalMaster_wide,
                        id_vars=['date', 'ReferenceMass'],
                        value_vars='MassIntensity')


# massCalMaster.insert(1, 'seq2', value=np.arange(len(massCalMaster)) + 1)
# massCalMaster_wide=massCalMaster.pivot(index='seq2', columns='tag', values='value')
# massCalMaster_wide=massCalMaster_wide.assign(date=calDate[0])
# massCalMaster_wide['date']=massCalMaster_wide['date'].str.replace(r'T.*', '', regex=True)
# mobilityCalMaster.insert(1, 'seq', value=np.arange(len(mobilityCalMaster)) + 1)
# mobilityCalMaster_wide=mobilityCalMaster.pivot(index='seq', columns='tag', values='value')
# mobilityCalMaster_wide=mobilityCalMaster_wide.assign(date=calDate[0])
# mobilityCalMaster_wide['date']=mobilityCalMaster_wide['date'].str.replace(r'T.*', '', regex=True)

# massCalMaster_wide=pd.concat([massCalMaster_wide, massCalFrame_wide_df])
# mobilityCalMaster_wide=pd.concat([mobilityCalMaster_wide, mobilityCalFrame_wide_df])

# massCalMaster_wide['CurrentMass']=massCalMaster_wide['CurrentMass'].astype('float')
# massCalMaster_wide['ReferenceMass']=massCalMaster_wide['ReferenceMass'].astype('category')
# massCalMaster_wide['MassError']=massCalMaster_wide['MassError'].astype('float')
# massCalMaster_wide['MassIntensity']=massCalMaster_wide['MassIntensity'].astype('float')
# massCalMaster['value']=massCalMaster['value'].astype('float')



# %%
# Dash

import plotly.graph_objects as go
import pandas as pd
from dash import Dash, dcc, html
from datetime import date
from plotly_calplot import calplot
from dash.dependencies import Input, Output, State
from jupyter_dash import JupyterDash
import dash_bootstrap_components as dbc


#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__)
today=date.today()
# mass cal
# massCalMaster_wide_sorted=massCalMaster_wide.sort_values(by='ReferenceMass')
# massCalFig=px.line(massCalMaster_wide, x='date', y='MassIntensity', color='ReferenceMass', title='Time Series Plot')
# massCalFig.update_traces(mode='lines+markers')
# massCalFig.update_layout(xaxis_range=['2023-06-01',today.strftime("%Y-%m-%d")])

# # mobility cal
# mobilityCalMaster_wide_sorted=mobilityCalMaster_wide.sort_values(by='ReferenceMass')
# mobilityCalFig=px.line(mobilityCalMaster_wide, x='date', y='MassIntensity', color='ReferenceMass', title='Time Series Plot')
# mobilityCalFig.update_traces(mode='lines+markers')
# mobilityCalFig.update_layout(xaxis_range=['2023-06-01',today.strftime("%Y-%m-%d")])

# # Set title
# massCalFig.update_layout(title_text="Mass Calibration")
# mobilityCalFig.update_layout(title_text="Mobility Calibration")

# main

app.layout = html.Div([
    html.H1(children="TIMS ToF Calibration Analytics"),
    dcc.Tabs([
        dcc.Tab(label='Calibration Intensity Plots', children=[
            html.H4('Choose Plot type'),
            dcc.Dropdown(['mass', 'mobility'],
                        'mass',
                id='plot-type'
            ),
            dcc.RadioItems(['Linear', 'Log'],
                'Linear',
                id='yaxis-type',
                inline=True
                ),
            dcc.Graph(id='figOut')]),
        dcc.Tab(label='Calibration Score Calendar', children=[
            html.H4('Choose Plot type'),
            dcc.Dropdown(['mass scores', 'mobility scores', 'mass deviation', 'mobility deviation'],
                        'mass scores',
                id='cal-type'),
            # html.H4('Mobility Scores'),
            dcc.Graph(id='calOut')]),
        ]),
    ])

# Single page layout
# app.layout = html.Div([
#     html.H1(children="TIMS ToF Analytics"),
#     html.H4('Choose Plot type'),   
#     dcc.Dropdown(['mass', 'mobility'],
#                 id='plot-type'
#             ),
#     # use this for single lines per plot
#     # html.H4('Choose Masses'),   
#     # dcc.Dropdown(massCalMaster_wide['ReferenceMass'].unique(),
#     #             massCalMaster_wide['ReferenceMass'].unique()[0],
#     #             # multi=True,
#     #             id='yaxis-column'),
#     dcc.RadioItems(['Linear', 'Log'],
#                 'Linear',
#                 id='yaxis-type',
#                 inline=True
#                 ),
#     dcc.Graph(id='figOut')
#     # html.H4('Mobility Calibration Intensity Plots'),
#     # html.H4('Mass Calibration Intensity Plots'),    
#     # dcc.Graph(figure=mobilityCalFig),
#     # html.H4('Mobility Scores'),
#     # dcc.Graph(figure=mobScorePlot),
#     # html.H4('Mobility Relative Deviation'),
#     # dcc.Graph(figure=mobDeviationPlot),
#     # html.H4('MZ Scores'),
#     # dcc.Graph(figure=mzScorePlot),
#     # html.H4('MZ Relative Deviation'),
#     # dcc.Graph(figure=mzDeviationPlot)
#     # dcc.Graph(figure=fig_mob),
# ])

# Callbacks
@callback(
    Output('figOut', 'figure'),
    Input('plot-type', 'value'),
    # use this for single lines per plot
    # Input('yaxis-column', 'value'),
    Input('yaxis-type', 'value'))

def update_graph(plot_type, yaxis_type):
    if plot_type == 'mass':
        dff=massCalMaster_wide
    if plot_type == 'mobility':
        dff=mobilityCalMaster_wide
    # use this for single lines per plot
    # fig = px.line(x=dff[dff['ReferenceMass'] == yaxis_column_name]['date'],
    #             y=dff[dff['ReferenceMass'] == yaxis_column_name]['MassIntensity'])
    fig = px.line(x=dff['date'],
            y=dff['MassIntensity'],
            color=dff['ReferenceMass'])
    fig.update_traces(mode='lines+markers')
    fig.update_layout(xaxis_range=['2023-06-01',today.strftime("%Y-%m-%d")])
    fig.update_yaxes(title='Intensity',
                    type='linear' if yaxis_type == 'Linear' else 'log')
    # fig.update_layout(yaxis_tickformat=".3e") # Formats to scientific notation with 2 decimal places
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                    label="1m",
                    step="month",
                    stepmode="backward"),
                    dict(count=6,
                    label="6m",
                    step="month",
                    stepmode="backward"),
                    dict(count=1,
                    label="YTD",
                    step="year",
                    stepmode="todate"),
                    dict(count=1,
                    label="1y",
                    step="year",
                    stepmode="backward"),
                    dict(step="all")
                    ])
                ),
            rangeslider=dict(
                visible=True
                ),
            type="date"
            )
        )
    return fig

@callback(
    Output('calOut', 'figure'),
    Input('cal-type', 'value'))

def update_CalGraph(plot_type):
    if plot_type == 'mass scores':
        ddf2=mzCal
        calOut = calplot(ddf2, x='Date', y="score",  years_title=True, dark_theme=False, showscale = True)
    if plot_type == 'mass deviation':
        ddf2=mzCal
        calOut=calplot(ddf2, x='Date', y="relative_deviation",  years_title=True, dark_theme=False, showscale = True)
    if plot_type == 'mobility scores':
        ddf2=mobCal
        calOut=calplot(ddf2, x='Date', y="score", years_title=True, dark_theme=False, showscale = True)
    if plot_type == 'mobility deviation':
        ddf2=mobCal
        calOut=calplot(ddf2, x='Date', y="relative_deviation",  years_title=True, dark_theme=False, showscale = True)
    return calOut

app.run(debug=True)  # Turn off reloader if inside Jupyter


