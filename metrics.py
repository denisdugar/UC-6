import boto3
import logging
from datetime import datetime
from datetime import timedelta
import json
import uuid
logger = logging.getLogger()
logger.setLevel(logging. INFO)
logger.setLevel(logging. ERROR)
ec2 = boto3.resource('ec2')
cw = boto3.client('cloudwatch')
s3 = boto3.resource('s3')
s3client = boto3.client('s3')
ec2_client = boto3.client('ec2')

def lambda_handler(event, context):
    try:
        volumes = ec2.volumes.all()
        bucketname = 'dduga-s3'

        for volume in volumes:
            volume_id = volume.id
            metrics_list_response = cw.list_metrics(Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}])
            print("metrics_list_response-->", metrics_list_response)
            metrics_response = get_metrics(metrics_list_response, cw)
            try:
                metrics_response["DEVICE"]= volume_id
            except:
                print("No metrics")
            instanceData = json.dumps (metrics_response, default=datetime_handler)
            print("metrics_response--->", metrics_response)
            bucket_name = bucketname
            filename = str(uuid.uuid4())+"__"+volume_id +'_InstanceMetrics.json'
            key = volume_id + "/" + filename
            s3client.put_object (Bucket=bucket_name, Key=key, Body=instanceData)
    except Exception as e:
        logger.exception("Error while getting Volume cloudwatch metrics (0)".format(e))

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

def get_metrics (metrics_list_response, cw):
    metric_data_queries = []
    metrices=metrics_list_response.get('Metrics')
    for metrics in metrices:
        namespace=metrics.get("Namespace")
        dimensions=metrics.get("Dimensions")
        metric_name=metrics.get("MetricName")
        metric_id = metric_name
        metrics_data_query = {"Id": metric_id.lower(), "MetricStat": {
        "Metric": {"Namespace": namespace,
                    "MetricName": metric_name,
                    "Dimensions": dimensions},
        "Period": 60000,
        "Stat": "Average"
        }, "Label": metric_name + "Response", "ReturnData": True}
        metric_data_queries.append(metrics_data_query)
        print("metric_data_queries --->",metric_data_queries)
    if metric_data_queries!=[]:
        metrics_response = cw.get_metric_data(
        MetricDataQueries=metric_data_queries,
        StartTime=datetime.now()+timedelta(minutes=-60),
        EndTime=datetime.now()
        )
        return metrics_response