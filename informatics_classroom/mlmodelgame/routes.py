from flask import request,render_template, jsonify
import pandas as pd
from azure.cosmosdb.table.tableservice import TableService
from informatics_classroom.mlmodelgame import mlmodel_bp
from informatics_classroom.config import Keys


@mlmodel_bp.route("/submit-model",methods=['POST'])
def submit_model():
    if request.method=='POST': 
        model=request.form.to_dict()
        model['PartitionKey']=request.form['ModelKey']
        model['RowKey']=str(len(list(table_service.query_entities('models')))+1)
        table_service = TableService(account_name=Keys.account_name, account_key=Keys.storage_key)
        table_service.insert_or_replace_entity('models',model)
    return jsonify({"Message":"Model Submitted"}),200

@mlmodel_bp.route("/models")
def models():
    table_service = TableService(account_name=Keys.account_name, account_key=Keys.storage_key)
    tasks = table_service.query_entities('models', filter="PartitionKey eq 'SIIM_AutoSeg_001'")
    df=pd.DataFrame(tasks)
    df['metric']=pd.to_numeric(df.metric,errors='coerce')
    df1=df.groupby('team').metric.agg(['count','max']).reset_index().sort_values('max',ascending=False)
    fields=df.columns[3:-4]
    context={'model_name':"Segmenting kidneys in MR Images",
        'Leader_Board':df1,
        'fields':fields,
        'data':df}
    return render_template("models.html", **context)