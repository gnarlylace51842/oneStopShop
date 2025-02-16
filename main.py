from flask import Flask, render_template, redirect, request, session, flash, url_for
from bson.objectid import ObjectId
import time
import random
from pymongo.mongo_client import MongoClient
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "pwjrfpinveo"
bcrypt = Bcrypt(app)

uri = "mongodb+srv://dylanashraf56014:yqoHsZ36iqTGN7xn@cluster0.iigar.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

db = client.oneStopShop
users_collection=db.users

@app.route("/")
def index():
    return redirect("/dashBoard")

@app.route("/register", methods=["POST"])
def register():
    name=request.form.get("name")
    requestform=dict(request.form)
    requestform["password"] = bcrypt.generate_password_hash(requestform["password"])
    user_name = db.users.find_one({"name": name})
    print(dict(requestform))
    if user_name:
        flash("Username already taken.", "error")
    else:
        db.users.insert_one(dict(requestform))
    return redirect("/dashBoard")

@app.route("/login", methods=["POST"])
def login():
    name=request.form.get("name")
    password=request.form.get("password")
    user = db.users.find_one({"name": name})
    if user:
        verifier=bcrypt.check_password_hash(user["password"], password)
        if verifier==True:
            user["_id"]=str(user["_id"])
            session["user"]=user
            return redirect("/dashBoard")
        elif verifier==False:
            print("not correct")
            return redirect("/")
    else:
        print("user not found")
        return redirect("/")
    
@app.route("/registerCustomer", methods=["POST"])
def registerCustomer():
    name=request.form.get("name")
    requestform=dict(request.form)
    requestform["password"] = bcrypt.generate_password_hash(requestform["password"])
    user_name = db.users.find_one({"name": name})
    print(dict(requestform))
    if user_name:
        flash("Username already taken.", "error")
    else:
        db.users.insert_one(dict(requestform))
    return redirect("/dashBoard")

@app.route("/loginCustomer", methods=["POST"])
def loginCustomer():
    name=request.form.get("name")
    password=request.form.get("password")
    user = db.users.find_one({"name": name})
    if user:
        verifier=bcrypt.check_password_hash(user["password"], password)
        if verifier==True:
            user["_id"]=str(user["_id"])
            session["user"]=user
            return redirect("/dashBoard")
        elif verifier==False:
            print("not correct")
            return redirect("/")
    else:
        print("user not found")
        return redirect("/")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/dashBoard", methods=["GET"])
def dashBoard():
    user=session.get("user", None)
    cards=list(users_collection.find({}, {"password":0}))
    if user:
        cart_items = list(db.cart.find({"user_id": ObjectId(user["_id"])}))
    else:
        cart_items = []
    print(cart_items)
    return render_template("homePage.html", cards=cards, user=user, cart_items=cart_items)

@app.route("/shop/<email>")
def shop(email):
    user=db.users.find_one({"email": email})
    user_id=ObjectId(user.get("_id"))
    products=list(db.products.find({"owner_id": user_id}))
    currentLoggedInUser=session.get("user", None)
    if currentLoggedInUser==None:
        shopBelongsTo=False
        flash("Please log in for access to the shops.", "danger")
    elif user_id==ObjectId(currentLoggedInUser["_id"]):
        shopBelongsTo=True
    else:
        shopBelongsTo=False
    return render_template("productPage.html", ownerid=user_id, products=products, user=currentLoggedInUser, shopBelongsTo=shopBelongsTo)

@app.route("/addItem", methods=["POST"])
def addItem():
    requestform=dict(request.form)
    requestform["owner_id"]=ObjectId(session["user"]["_id"])
    db.products.insert_one(requestform)
    return redirect("/shop/"+session["user"]["email"])

@app.route("/addToCart/", methods=["POST"])
def addToCart():
    data=dict(request.form)
    data["quantity"] = int(data["quantity"])
    print(data)
    productToAdd=db.products.find_one({"_id": ObjectId(data["_id"])}, {"_id": 0})
    db.products.update_many({}, [{"$set": {"quantity": {"$toInt": "$quantity"}}}])
    """ db.products.update_one({"_id": ObjectId(data["_id"])}, {"$inc" :{"quantity": -1*(int(data["quantity"]))}}) """
    db.products.update_one(
        {"_id": ObjectId(data["_id"])}, 
        {"$inc": {"quantity": -1 * int(data["quantity"])}}
    )
    productToAdd["quantity"]=data["quantity"]
    productToAdd["user_id"]=ObjectId(session["user"]["_id"])
    productToAdd["product_id"]=ObjectId(data["_id"])
    existingProduct=db.cart.find_one({"user_id": ObjectId(session["user"]["_id"]), "product_id": ObjectId(data["_id"])})
    if existingProduct:
        db.cart.update_one(
            {"user_id": ObjectId(session["user"]["_id"]), "product_id": ObjectId(data["_id"])},
            {"$inc": {"quantity": int(data["quantity"])}}
        )
    else:
        db.cart.insert_one(productToAdd)
    return redirect("/")

@app.route("/cart")
def cart():
    cart_items = list(db.cart.find())
    return render_template("homePage.html", cart_items=cart_items)

@app.route("/delete_from_cart/<item_id>", methods=["POST"])
def delete_from_cart(item_id):
    db.cart.delete_one({"_id": ObjectId(item_id)})
    return redirect(url_for("dashBoard"))

if __name__=="__main__":
    app.run(debug=True, port=8000)