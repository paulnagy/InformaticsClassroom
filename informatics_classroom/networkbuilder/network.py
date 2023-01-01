from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
import plotly.graph_objects as go
import networkx as nx
import pandas as pd

OhdsiGroups=sorted(['Vocab', 'CDM','PLP','PLE',
'HADES','Data Quality','Pheno','ATLAS','Clin Trials','FHIR & OMOP',
'GIS','Devices','Imaging','NLP','Registry','Vaccine','Health Equity',
'Surgery','Onc','Psych','Africa','Asia Pacific','Latin Am',
'Early Stage','Open Source','Health Systems','Ed','Steering','Eye Care'
])

class OHDSIForm(FlaskForm):

    wg1 = SelectField('Working Group 1', choices=OhdsiGroups)
    wg2 = SelectField('Working Group 2', choices=OhdsiGroups)
    submit = SubmitField('Submit New Connection')

# Plotly figure
def networkGraph(pairs):
  
    edges = pairs
    G = nx.Graph()
    G.add_edges_from(edges)
    pos = nx.spring_layout(G)

    # edges trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(color='black', width=2),
        hoverinfo='none',
        showlegend=False,
        mode='lines')

    # nodes trace
    node_x = []
    node_y = []
    text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        text.append(node.replace(' ','<br>'))

    node_trace = go.Scatter(
        x=node_x, y=node_y, text=text,
        mode='markers+text',
        showlegend=False,
        hoverinfo='none',
        marker=dict(
            color='pink',
            size=50,
            line=dict(color='black', width=1)))

    # layout
    layout = dict(plot_bgcolor='white',
                  paper_bgcolor='white',
                  margin=dict(t=10, b=10, l=10, r=40, pad=0),
                  xaxis=dict(linecolor='black',
                             showgrid=False,
                             showticklabels=False,
                             mirror=True),
                  yaxis=dict(linecolor='black',
                             showgrid=False,
                             showticklabels=False,
                             mirror=True),
                height=800,
                width=1200)

    # figure
    fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
    return fig