from flask import request, render_template
import json
import plotly
from informatics_classroom.networkbuilder import network_bp
from informatics_classroom.networkbuilder.network import networkGraph, OhdsiGroups, OHDSIForm
from informatics_classroom.azure_func import init_cosmos

@network_bp.route("/NetworkGame", methods=["GET","POST"])
def ohdsiNetworkGame():
    container2=init_cosmos('dashboard','ohdsi-impact-engine')
    query="SELECT * FROM c where c.id = 'NetworkGame'"
    items = list(container2.query_items(query=query, enable_cross_partition_query=True ))
    if request.method=='POST':
        wg1=request.form['wg1']
        wg2=request.form['wg2']
        items[0]['data'].append([wg1,wg2])
        items[0]['id'] = 'NetworkGame'
        container2.upsert_item(body = items[0])
    pairs=[]
    for wgroup in OhdsiGroups:
        pairs.append([wgroup,wgroup])
    for item in items[0]['data']:
        pairs.append(item)

    form=OHDSIForm()
    fig = networkGraph(pairs)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('networkgame.html',title='NetworkGame',form=form, graphJSON=graphJSON)
