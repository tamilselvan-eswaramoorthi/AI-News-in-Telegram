from datetime import datetime
from google.cloud import bigquery
from google.api_core import exceptions
from google.oauth2.service_account import Credentials

from config import Config



class BigQueryDatabase():
    """BigQuery-based database for production use"""
    
    def __init__(self):
        self.project_id = Config.gcp_project_id
        self.dataset_id = Config.bigquery_dataset
        self.table_id = Config.bigquery_table
        credentials = Credentials.from_service_account_file(Config.gcp_key_path)
        self.client = bigquery.Client(project=self.project_id, credentials=credentials)
        self.full_table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
    
    def initialize(self) -> bool:
        """Create BigQuery dataset and table if they don't exist"""
        try:
            # Create dataset if it doesn't exist
            dataset_ref = self.client.dataset(self.dataset_id)
            try:
                self.client.get_dataset(dataset_ref)
                print(f"Dataset {self.dataset_id} already exists")
            except exceptions.NotFound:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                self.client.create_dataset(dataset)
                print(f"Created dataset {self.dataset_id}")
            
            # Create table if it doesn't exist
            schema = [
                bigquery.SchemaField("date", "STRING", mode="REQUIRED", description="Date in YY-MM-DD format"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED", description="When the news was sent"),
                bigquery.SchemaField("status", "STRING", mode="NULLABLE", description="Status of the send operation"),
            ]
            
            table_ref = dataset_ref.table(self.table_id)
            try:
                self.client.get_table(table_ref)
                print(f"Table {self.table_id} already exists")
            except exceptions.NotFound:
                table = bigquery.Table(table_ref, schema=schema)
                self.client.create_table(table)
                print(f"Created table {self.table_id}")
            
            return True
            
        except Exception as e:
            print(f"Error initializing BigQuery database: {e}")
            return False
    
    def is_date_sent(self, date_str: str) -> bool:
        """Check if news for this date has already been sent"""
        try:
            query = f"""
                SELECT COUNT(*) as count
                FROM `{self.full_table_id}`
                WHERE date = @date_str
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("date_str", "STRING", date_str)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                return row.count > 0
            
            return False
            
        except Exception as e:
            print(f"Error checking sent dates in BigQuery: {e}")
            return False
    
    def log_sent_date(self, date_str: str, status: str = "success") -> bool:
        """Log the date when news was successfully sent"""
        try:
            rows_to_insert = [
                {
                    "date": date_str,
                    "timestamp": datetime.now().isoformat(),
                    "status": status
                }
            ]
            
            errors = self.client.insert_rows_json(self.full_table_id, rows_to_insert)
            
            if errors:
                print(f"Errors inserting rows to BigQuery: {errors}")
                return False
            
            print(f"Logged sent date to BigQuery: {date_str}")
            return True
            
        except Exception as e:
            print(f"Error logging sent date to BigQuery: {e}")
            return False


def get_database():
    db = BigQueryDatabase()
    db.initialize()
    return db

