from .Cartdbmodels import CoffeeShopModel
from decimal import *
import boto3


class coffeeShopModelDB(CoffeeShopModel):
    def __init__(self):
        self.resource = boto3.resource("dynamodb", region_name="us-east-1")
        self.table = self.resource.Table('foodcarts')
        try:
            self.table.load()
        except:
            self.resource.create_table(
                TableName="foodcarts",
                KeySchema=[
                    {
                        "AttributeName": "id",
                        "KeyType": "HASH"
                    },
                ],
                AttributeDefinitions=[
                    {
                        "AttributeName": "id",
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
        return([ dict(id=f['id'], name=f['name'], phone=f['phone'], rating=int(float(f['rating'])), review_count=int(f['review_count']), url=f['url'], image_url=f['image_url'], is_closed=f['is_closed'], distance=float(f['distance']), street=f['street'], city=f['city'], state=f['state'], zip_code=f['zip_code'], latitude=float(f['latitude']), longitude=float(f['longitude']), reviews=f['reviews']) for f in results['Items']]) 

    # def updateReviewCount(self, matchId):
    #     """
    #      update priority, begin_date, and end date of a task
    #      :param matchId: String
    #      :return: cart id
    #     """
    #     connection = sqlite3.connect(DB_FILE)
    #     cursor = connection.cursor()
    #     cursor.execute(
    #         "UPDATE foodcarts SET review_count= review_count + 1 WHERE id=?", (matchId,))
    #     connection.commit()

    def addReview(self, id, review):
        print(review)
        print(id)
        result = self.table.update_item(
            Key={
                'id': id
            },
            UpdateExpression="SET reviews = list_append(reviews, :i)",
            ExpressionAttributeValues = {
                ':i': [review],
            },
            ReturnValues="UPDATED_NEW"
        )
        if result['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in result:
            return result['Attributes']['reviews']

        


    def insert(self, id, name, phone, rating, review_count, url, image_url, is_closed, distance, street, city, state, zip_code, latitude, longitude, reviews):
        """
        Inserts entry into database
        :param name: String
        :param phone: String
        :param rating: Int
        :param review_count: Int
        :param reviews: lookinto best way to do this. will be an array of review objects, foreign key to other table?
        :param url: String
        :param location: location object, foreign key?
        :param image_url: String
        :param is_closed: Boolean
        :param id: String
        :Param distance: Int
        :param street: String
        :param city: String
        :param state: String
        :param zip: String
        :return: True
        :raises: Database errors on connection and insertion
        """
        item = {'id': str(id), 'name': name, 'phone': phone, 'rating': str(rating), 'review_count': str(review_count), 'url': url, 'image_url': image_url, 'is_closed': str(is_closed),
                  'distance': str(distance), 'street': street, 'city': city, 'state': state, 'zip_code': zip_code, 'latitude': str(latitude), 'longitude': str(longitude), 'reviews': reviews}
        try:
            self.table.put_item(Item=item)
        except:
            return False
        return True
