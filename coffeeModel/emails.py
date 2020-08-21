from .Cartdbmodels import EmailModel
from decimal import *
import boto3


class emailModelDB(EmailModel):
    def __init__(self):
        self.resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table = self.resource.Table('emails')
        try:
            self.table.load()
        except:
            self.resource.create_table(
                TableName="emails",
                KeySchema=[
                    {
                        "AttributeName": "email",
                        "KeyType": "HASH"
                    },
                ],
                AttributeDefinitions=[
                    {
                        "AttributeName": "email",
                        "AttributeType": "S"
                    },
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 30,
                    "WriteCapacityUnits": 30
                },
                
            )

    def select(self):
        """
        Gets all rows from the database
        Each row contains: name, email, date, message
        :return: List of lists containing all rows of database
        """
        try:
            results = self.table.scan()
        except Exception as e:
            print(e)
            return
        return([ dict(email=f['email']) for f in results['Items']]) 

    def insert(self, email):
        item = {'email': email}
        try:
            response = self.table.put_item(Item=item)
            return response
        except Exception as e:
            print(e)
            return False
        return True
            
