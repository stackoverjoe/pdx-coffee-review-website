import json
import os
from flask import Flask, render_template, request, abort, Response, redirect, url_for, escape
import requests
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import uuid
from datetime import datetime
from coffeeModel.coffeeshop_dynamodb import coffeeShopModelDB
from coffeeModel.emails import emailModelDB
from sendgrid import SendGridAPIClient
from emailformat import emailGenerator
from sendgrid.helpers.mail import Mail
import time
import asyncio
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)


# carts list will keep carts and reviews retrieved from the database on the heap for fast retrieval and to minimize retrievals
carts = []
emails = []
"""
ReviewList is used to minimize calls to my API key while developing.
Once sqlite3 database is installed it will be removed in favor of that.
"""

#app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# apikey read from .env file
yelpAPI = os.getenv("yelpAPI")


'''
For this app I am adding, among other requirements, the functionality of a real food cart review
site via yelp's Fusion API. I registered an account with them and obtained an api key that is good
for 5000 requests a day. The following block sets up the necessary headers and paramaters to get
information back from yelp that will be used to populate templates. Now that data is read from the db
this will be moved over to a polling logic that updates some x amount of time per day or week.
'''
headers = {'Authorization': 'Bearer {}'.format(yelpAPI)}
url = 'https://api.yelp.com/v3/businesses/search'
params = {'term': 'coffee', 'location': 'Portland'}

# if reviewsList has already been populated - do not make an api call
# if(len(reviewsList) == 0):
#     req = requests.get(url, params=params, headers=headers)
#     print('The status code is {}'.format(req.status_code))
#     getit = json.loads(req.text)
#     for i in getit['businesses']:
#         reviews = requests.get(
#             url=('https://api.yelp.com/v3/businesses/'+i['id']+'/reviews'), headers=headers)
#         reviewsVal = json.loads(reviews.text)
#         i['reviews'] = reviewsVal
#         reviewsList.append(i)

#carts = reviewsList
'''
Models instantiated and carts initialized from database. Len carts probably isn't necessary and will most likely only happen once,
but putting it there for unforseen events as a safeguard
'''
cartdb = coffeeShopModelDB()
emailsdb = emailModelDB()
if(len(carts) == 0):
    carts = cartdb.select()


# xx = json.dumps(carts[0]['reviews']['reviews'])
# print(xx)
# for i in carts:
#     cartdb.insert(i['id'], i['name'], i['phone'], i['rating'], i['review_count'], i['url'], i['image_url'], i['is_closed'], i['distance'], i['location']['address1'], i['location']['city'], i['location']['state'], i['location']['zip_code'], i['coordinates']['latitude'], i['coordinates']['longitude'], i['reviews']['reviews'])
'''
Used to update db from yelp call, will also be moved to the polling event once created.
'''
# for i in reviewsList:
#     cartModel.insert(i['id'], i['name'], i['phone'], i['rating'], i['review_count'], i['url'], i['image_url'], i['is_closed'], i['distance'], i['location']['address1'], i['location']['city'], i['location']['state'], i['location']['zip_code'], i['coordinates']['latitude'], i['coordinates']['longitude'])
#     for x in i['reviews']['reviews']:
#         reviewModel.insert(x['id'], x['user']['name'], x['rating'], x['text'], x['time_created'], x['url'], i['id'])

'''
Root path leads to landing page which is index.html.
'''
@app.route("/")
def sessions():
    return render_template("index.html", businesses=carts)


'''
Path to display all carts, passes in 'carts' list and a boolean. the boolean is used in the template logic
to decide if the header should read 'All reviews' or if they navigated there as a result of a search query in 
which case it would display the name of the query.
'''
@app.route("/allshops", methods=["GET", "POST"])
def allshops():
    submit = request.args.get('submit')
    return render_template("allshops.html", businesses=carts, searched=False, submit=submit)


'''
Thank you page is navigated to after a user submits a cart to the site, passes along the name and id for displaying 
and the ability to jump to the cart they just added
'''
@app.route("/thank-you")
def thankYou():
    name = request.args.get('name')
    cartId = request.args.get('cartId')
    return render_template("thankyou.html", name=name, cartId=cartId)


'''
This is the end point that is hit when a user submits a review.
A dict is created to add to the heap storage and the cart is added to the db. Likewise the review count for the
appropriate cart is updated in storage and in the carts list.
'''
@app.route("/submit-review", methods=["POST"])
def reviewPost(methods=["POST"]):
    now = datetime.now()
    currentTime = now.strftime("%m-%d-%Y")
    print(currentTime)
    cartId = request.form['cartId']
    review = escape(request.form['txtMsg'])
    rating = request.form['rating']
    name = escape(request.form['name'])
    uuidId = uuid.uuid4()
    reviewDict = dict({'user': {'name': str(name)}}, id=str(uuidId), name=name, rating=rating,
                      text=review, time_created=currentTime, url=None, cart_id=cartId)
    reviewDict2 = dict({'user': {'name': str(name)}}, id=str(uuidId), name=str(name), rating=str(rating),
                       text=str(review), time_created=str(currentTime), url=None, cart_id=str(cartId))
    cartdb.addReview(str(cartId), reviewDict2)
    for i in carts:
        if(i['id'] == cartId):
            i['review_count'] = i['review_count'] + 1
            i['reviews'].append(reviewDict)
            break
    return redirect(url_for("allshops", _anchor='reviewContainer{}'.format(cartId), submit=True))


'''
End point for when a new food cart is submitted escape used to convert symbols to html
safe string to prevent scritps from being uploaded to db. Geocode api is hit in this
function so that coordinates can be pulled from the provided address and the new cart 
can be displayed on the google maps view.
'''
@app.route("/submit-shop", methods=["POST"])
def reviewSubmitCart(methods=["POST"]):
    now = datetime.now()
    currentTime = now.strftime("%m-%d-%Y")
    cartId = uuid.uuid4()
    reviewId = uuid.uuid4()
    cartName = escape(request.form['cartName']).capitalize()
    cartPhone = escape(request.form['cartPhone'])
    cartStreet = escape(request.form['cartStreet'])
    userName = escape(request.form['userName'])
    userReview = escape(request.form['userReview'])
    userRating = request.form['userRating']
    cartCity = escape(request.form['cartCity'])
    cartState = escape(request.form['cartState'])
    cartZip = escape(request.form['cartZip'])
    cartPic = escape(request.form['cartPic'])
    cartLat = None
    cartLng = None
    req = requests.get("https://maps.googleapis.com/maps/api/geocode/json?address={},+{},+{},+{}&key=AIzaSyDtfxiToGiuDo3zqHl58wbr19abdhQTQQM".format(
        cartStreet, cartCity, cartState, cartZip))
    resp = json.loads(req.text)

    if resp['status'] == 'OK':
        cartLat = resp['results'][0]['geometry']['location']['lat']
        cartLng = resp['results'][0]['geometry']['location']['lng']

    cartDict = dict(id=str(cartId), name=cartName, phone=cartPhone, rating=userRating, review_count=1, url=None, image_url=cartPic,
                    is_closed=0, distance=0, street=cartStreet, city=cartCity, state=cartState, zip_code=cartZip, latitude=cartLat, longitude=cartLng)
    reviewDict = dict({'user': {'name': userName}}, id=str(reviewId), rating=userRating,
                      text=userReview, time_created=currentTime, url=None, cart_id=str(cartId))
    cartDict['reviews'] = []
    cartDict['reviews'].append(reviewDict)
    i = cartDict
    cartdb.insert(i['id'], i['name'], i['phone'], i['rating'], i['review_count'], i['url'], i['image_url'], i['is_closed'],
                  i['distance'], i['street'], i['city'], i['state'], i['zip_code'], i['latitude'], i['longitude'], i['reviews'])
    carts.append(cartDict)
    #async run email campaign
    message = emailGenerator(cartName, "http://stackoverjoe.com/allshops#reviewContainer{}".format(cartId))
    print(message)
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.run(email(message, cartName))
    return redirect(url_for("thankYou", name=cartName, cartId=cartId))


'''
Reviewwriter is actually a submitcart page and the name needs to be refactored
to reflect that.
'''
@app.route("/reviewwriter")
def review():
    return render_template("submitshop.html", businesses=carts)


@app.route("/subscribe", methods=["GET", "POST"])
def subscribe():
    return render_template("subscribe.html", subscribed = False)


@app.route("/submitsubscribe", methods=["GET", "POST"])
def submitsubscribe():
    email = escape(request.form['email'])
    emailsdb.insert(str(email))
    return render_template("subscribe.html", subscribed = True)

'''
Search method is hit from the navbar search functionality and uses a library called
'fuzzywuzzy' to do searches with spelling mistake allowance. It then renders the all carts
pade with just a list of carts matching the query
'''
@app.route("/search")
def searchForCart():
    query = request.args.get('query')
    # searchParams = {'term': (query+"+foodcart"), 'location': 'Portland'}
    # response2 = requests.get(url='https://api.yelp.com/v3/businesses/search', headers=headers, params=searchParams)
    #print('The status code is {}'.format(req.status_code))
    result = []
    result2 = process.extract(query, carts)
    for i in result2:
        if(i[1] > 50):
            result.append(i[0])
    #responseVal = json.loads(response2.text)
    if(len(result) == 0):
        return render_template("searchresult.html", query=query)
    else:
        # for i in responseVal['businesses']:
        #     reviews = requests.get(
        #         url=('https://api.yelp.com/v3/businesses/'+i['id']+'/reviews'), headers=headers)
        #     reviewsVal = json.loads(reviews.text)
        #     i['reviews'] = reviewsVal
        return render_template("allshops.html", businesses=result, searched=True, query=query)
    # something

async def email(content, name):
    emails = emailsdb.select()
    for i in emails:
        message = Mail(
            from_email='jml27@pdx.edu',
            to_emails= i['email'],
            subject='{} has been added on Portland Roast!'.format(name).capitalize(),
            html_content=content)
        try:
            sg = SendGridAPIClient(os.getenv('mailAPI'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            return False

if __name__ == "__main__":
    app.run(port=80, host='0.0.0.0', debug=False)
