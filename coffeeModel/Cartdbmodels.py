class ReviewsModel():
    def select(self):
        """
        Gets all entries from the database
        :return: Tuple containing all rows of database
        """
        pass

    def insert(self, id, name, rating, text, time_created, url, cart_id):
        """
        Inserts entry into database
        :param id: String Primary Key
        :param name: String
        :param rating: Int
        :param text: String
        :param time_created: String
        :param url: String
        :param cart_id: String Foreign Key for FoodCartModel(id)
        :return: none
        :raises: Database errors on connection and insertion
        """
        pass

    def selectSome(self, queryID):
        """
        Selects all entries in reviews where the cartId field matches the queryId
        :param queryID: String
        :return: Tuple containing all rows that pass the predicate
        """
class EmailModel():
    def select(self):
        """
        get all emails
        """
        pass
    def insert(self, email):
        """
        insert an email address
        """
        pass

class CoffeeShopModel():
    def select(self):
        """
        Gets all reviews from the database
        :return: Tuple containing all rows of database
        """
        pass

    def updateReviewCount(self, matchId):
        """
        update priority, begin_date, and end date of a task
        :param matchId: String
        :return: cart id
        """
        pass
   

    def insert(self, name, phone, rating, review_count, url, image_url, is_closed, id, distance, street, city, state, zip):
        """
        Inserts entry into database
        :param name: String
        :param phone: String
        :param rating: Int
        :param review_count: Int
        :param url: String
        :param location: location object, foreign key?
        :param image_url: String
        :param is_closed: Boolean
        :param id: String Primary Key
        :Param distance: Int
        :param street: String
        :param city: String
        :param state: String
        :param zip: String
        :return: none
        :raises: Database errors on connection and insertion
        """
        pass

    
