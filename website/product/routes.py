from flask import *
import os
from website import app, db, bucket, storage_client
from .forms import ProductForm, ReviewForm
from werkzeug.utils import secure_filename
import datetime 

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
DEFAULT_LABELS = ['Product Quality', 'Delivery Service', 'Seller Service', 'Performance', 'Durability', 'Effectiveness', 'Material', 'Design']
COMPULSORY_LABELS = ['Product Quality', 'Delivery Service', 'Seller Service']


def allow_file_type(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def review_tags_list(labels):
    all_labels = DEFAULT_LABELS.copy()
    for label in labels:
        if label not in all_labels:
            all_labels.append(label)
    return all_labels


def check_product_availability(new_name, old_name):
    pro_name_list = []
    # Get all the added product from Firestore
    pro_docs = db.collection(u'products').get()
    for doc in pro_docs:
        pro_name = doc.get("productName")
        pro_name_list.append(pro_name)
    # Compare the input product name with product list from Firestore
    for product in pro_name_list:
        if product == old_name:
            continue
        elif product == new_name:
            return True
    return False


def image_storage_path(name):
    list_img = []
    # List all the image paths found in the Firebase Storage
    all_blobs = list(storage_client.list_blobs(bucket))
    # Filter the image paths to collect only the specific product name
    for bb in all_blobs:
        if bb.name.find(name) == -1:
            continue
        else:
            list_img.append(bb.name)
    return list_img


def filter_docs(all_products, character):
    # Create an empty list to store the results
    results = []
    for product in all_products:
        for element in product:
            # Check if the element contains the specified character
            # Convert both character and element into lowercase
            if character.lower() in element.lower():
                # If the element contains the specified characters, add its index to the results list
                index = all_products.index(product)
                # Avoid duplication in the results
                if index in results:
                    continue
                else:
                    results.append(all_products.index(product))
    # Return the results list
    return results


def calculate_review_tags(collection, all_review_labels, review_number_dic):
    for rev_doc in collection.stream():
        review_tag_list = rev_doc.get("reviewTags")
        # Add the tag number by 1 once the tag was found in the review_tag_list
        for tag in review_tag_list:
            for i in range(len(all_review_labels)):
                if tag == all_review_labels[i]:
                    review_number_dic[all_review_labels[i]] += 1
    return review_number_dic


def calculate_sentiment_proportion(reviews_list):
    sentiment = [0, 0, 0]
    for review in reviews_list:
        # Calculate the number of each sentiment class
        if review[5] == "Positive":
            sentiment[0]+=1
        elif review[5] == "Neutral":
            sentiment[1]+=1
        elif review[5] == "Negative":
            sentiment[2]+=1
    total = sum(sentiment)
    if total == 0:
        return []
    sentiment_propor_list = [round(n / total * 100, 2) for n in sentiment]
    return sentiment_propor_list


def calculate_review_dates(review_list):
    review_numbers = []
    current_date = datetime.date.today()
    # Total number of reviews
    review_numbers.append(len(review_list))
    # Initialize counters for years, months, and days
    year_counts = 0
    month_counts = 0
    day_counts = 0
    # Iterate over the review list
    for review in review_list:
        review_date = review[2]
        # Parse the date string into a datetime object
        date = datetime.datetime.strptime(review_date, '%Y-%m-%d')
        if date.year == current_date.year:
            year_counts +=1
        if date.month == current_date.month:
            month_counts +=1
        if date.day == current_date.day:
            day_counts +=1
    # Append results review number list
    review_numbers.append(year_counts)
    review_numbers.append(month_counts)
    review_numbers.append(day_counts)
    return review_numbers


def calculate_tag_sentiment(review_list):
    all_tag_sentiment = []
    tag_list = []
    positive_data = []
    neutral_data = []
    negative_data = []
    tag_index = 999
    # Iterate over the review list
    for review in review_list:
        # Iterate over the review tags list
        for tag in review[0]:
            # If the tag is not in tag_list, add it into the tag_list, and add 0 to the end of sentiment list and get the index no
            if tag not in tag_list:
                tag_list.append(tag)
                positive_data.append(0)
                neutral_data.append(0)
                negative_data.append(0)
                tag_index = -1
            # If the tag is not in tag_list, get the index no in the tag_list
            else:
                tag_index = tag_list.index(tag)
            # Check the sentiment of this review
            if review[1] == 'Positive':
                positive_data[tag_index] +=1
            elif review[1] == 'Neutral':
                neutral_data[tag_index] +=1
            elif review[1] == 'Negative':
                negative_data[tag_index] +=1
    all_tag_sentiment.append(tag_list)
    all_tag_sentiment.append(positive_data)
    all_tag_sentiment.append(neutral_data)
    all_tag_sentiment.append(negative_data)
    return all_tag_sentiment


def calculate_product_sentiment(review_list):
    all_product_sentiment = []
    product_list = []
    positive_data = []
    neutral_data = []
    negative_data = []
    product_index = 999
    # Iterate over the review list
    for review in review_list:
        # If the product is not in product_list, add it into the product_list, and add 0 to the end of sentiment list and get the index no
        if review[3] not in product_list:
            product_list.append(review[3])
            positive_data.append(0)
            neutral_data.append(0)
            negative_data.append(0)
            product_index = -1
        # If the product is not in product_list, get the index no in the product_list
        else:
            product_index = product_list.index(review[3])
        # Check the sentiment of this review
        if review[1] == 'Positive':
            positive_data[product_index] +=1
        elif review[1] == 'Neutral':
            neutral_data[product_index] +=1
        elif review[1] == 'Negative':
            negative_data[product_index] +=1
    all_product_sentiment.append(product_list)
    all_product_sentiment.append(positive_data)
    all_product_sentiment.append(neutral_data)
    all_product_sentiment.append(negative_data)
    return all_product_sentiment


# Product Page
@app.route("/product/<string:name>", methods=["GET", "POST"])
def product(name):
    product = []
    reviews_list = []
    img_url_list = []
    current_tag = "All Tags"
    review_number_dic = {}
    total_reviews = 0
    # Get all the product details from Firestore according to the product name
    pro_doc = db.collection(u'products').where("productName", "==", name).stream()
    for doc in pro_doc:
        # Get all the product details and store in a list
        product.append(name)
        product.append(doc.get("description"))
        product.append(doc.get("businessName"))
        # Find the product image paths from Firebase Storage
        list_img = image_storage_path(name)
        # Get the product's image URL
        for img in list_img:
            blob = bucket.blob(img)
            blob.make_public()
            url = blob.public_url
            img_url_list.append(url)
        product.append(img_url_list)
        # Get all the product reviews from Firestore according to the document ID
        review_collection = db.collection(u'products').document(doc.id).collections()
        # Check whether the product have any review
        for collection in review_collection:
            # Calculate the total numbers of customer reviews
            for rev_doc in collection.stream():
                total_reviews+=1
            product.append(total_reviews)
            # Calculate the numbers of customer reviews according to the review tags
            all_review_labels = doc.get("reviewLabel")
            for label in all_review_labels:
                review_number_dic[label] = 0
            review_number_dic = calculate_review_tags(collection, all_review_labels, review_number_dic)
            product.append(review_number_dic)
            # Filter the reviews according to the selected review tag
            if request.method == "POST":
                filter_review = request.form["button_value"]
                current_tag = filter_review
                if filter_review != "All Tags":
                    if filter_review:
                        collection = collection.where("reviewTags", u'array_contains', filter_review)
            # Get all the review details and store in a list
            for rev_doc in collection.stream():
                rev_details = []
                rev_details.append(rev_doc.get("customer"))
                rev_details.append(rev_doc.get("title"))
                rev_details.append(rev_doc.get("content"))
                rev_details.append(rev_doc.get("experienceDate"))
                rev_details.append(rev_doc.get("reviewTags"))
                rev_details.append(rev_doc.get("sentiment"))
                review_date = rev_doc.get("reviewDate")
                # Convert the review data format from %Y-%m-%d to %b %d, %Y
                temp_date = datetime.datetime.strptime(review_date, '%Y-%m-%d')
                review_date = temp_date.strftime('%b %d, %Y')
                rev_details.append(review_date)
                reviews_list.append(rev_details)
            # Calculate the proportion of each sentiment
            sentiment_propor_list= calculate_sentiment_proportion(reviews_list)
            product.append(sentiment_propor_list)
            product.append(current_tag)
    return render_template('product/index.html', title='Product Detail Page', product=product, reviews_list=reviews_list)


# Product Analysis
@app.route('/analysis', methods=['GET', 'POST'])
def product_analysis():
    review_list = []
    review_numbers = []
    all_tag_sentiment = []
    all_product_sentiment = []
    # Get all the product details from Firestore according to the business name
    pro_doc = db.collection(u'products').where("businessName", "==", session['name']).stream()
    for doc in pro_doc:
        # Get the sub-collection from Firestore according to the document ID
        review_collection = db.collection(u'products').document(doc.id).collections()
        # Check whether the product have any review
        for collection in review_collection:
            # Get the review details and store in a list
            for rev_doc in collection.stream():
                rev_details = []
                rev_details.append(rev_doc.get("reviewTags"))
                rev_details.append(rev_doc.get("sentiment"))
                rev_details.append(rev_doc.get("reviewDate"))
                rev_details.append(doc.get("productName"))
                review_list.append(rev_details)
    # Calculation for "Total Number of Customer Reviews"
    review_numbers = calculate_review_dates(review_list)
    # Calculation for "Sentiment Breakdown by Review Tags"
    all_tag_sentiment = calculate_tag_sentiment(review_list)
    all_product_sentiment = calculate_product_sentiment(review_list)
    return render_template('product/analysis.html',title='Product Analysis Page', review_numbers=review_numbers, all_tag_sentiment=all_tag_sentiment, all_product_sentiment=all_product_sentiment)


# Add Product
@app.route("/addproduct", methods=["GET", "POST"])
def add_product():
    # Create instance of product form
    form = ProductForm()
    # When the connected html passing POST request (Submit Button is clicked)
    if request.method == "POST":
        exist_in_database = False
        review_labels = []
        file_names = []
        business_name = session['name']
        product_name = form.name.data
        description = form.description.data
        files = request.files.getlist('files[]')
        selected_labels = request.form.getlist('selected_labels[]')
        review_labels = COMPULSORY_LABELS + selected_labels
        # Create a new list to temporarily store the all the labels (default labels & self-added labels)
        all_labels = review_tags_list(review_labels)
        # Check the product name availability
        exist_in_database = check_product_availability(product_name, None)
        if exist_in_database:
            flash("This product has been added to database", 'danger')
            return render_template('product/addproduct.html', title='Add Product Page', form=form, all_labels=all_labels, compulsory_labels=COMPULSORY_LABELS, selected_labels=selected_labels)
        # Check the uploaded file types
        for file in files:
            if file and allow_file_type(file.filename):
                filename = secure_filename(file.filename)
                file_names.append(filename)
                # Save image file to project root
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
            else:
                flash('Allowed image types are -> png, jpg, jpeg, gif', 'danger')
                return render_template('product/addproduct.html', title='Add Product Page', form=form, all_labels=all_labels, compulsory_labels=COMPULSORY_LABELS, selected_labels=selected_labels)
        # Upload images to Firebase Storage
        for image in file_names:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image)
            sto_path = product_name + '/' + image
            blob = bucket.blob(sto_path)
            blob.upload_from_filename(image_path)
            # Delete images from project root
            os.remove(image_path)
        # Define product details
        data = {
            u'productName': product_name,
            u'description': description,
            u'businessName': business_name,
            u'reviewLabel': review_labels
        }
        # Add a new doc in collection 'products' with random document ID
        db.collection(u'products').document().set(data)
        flash(f'The product ({product_name}) was successfully added in database', 'success')
        return redirect(url_for('business'))
    return render_template('product/addproduct.html', title='Add Product Page', form=form, all_labels=DEFAULT_LABELS, compulsory_labels=COMPULSORY_LABELS)


# Edit Product
@app.route('/editproduct/<string:name>', methods=["GET", "POST"])
def edit_product(name):
    img_url_list = []
    form = ProductForm()
    # Get all the product details from Firestore
    pro_docs = db.collection(u'products').where("productName", "==", name).stream()
    for doc in pro_docs:
        pre_product_name = doc.get("productName")
        pre_description = doc.get("description")
        pre_review_labels = doc.get("reviewLabel")
    # Create a new list to store the default labels and the self-added labels
    all_labels = review_tags_list(pre_review_labels)
    # Find the product image path from Firebase Storage
    list_img = image_storage_path(name)
    # Get the products' image URL
    for img in list_img:
        blob = bucket.blob(img)
        blob.make_public()
        url = blob.public_url
        img_url_list.append(url)
    #  When the connected html passing POST request (Submit Button is clicked)
    if request.method == "POST":
        exist_in_database = False
        review_labels = []
        file_names = []
        business_name = session['name']
        product_name = form.name.data
        description = form.description.data
        files = request.files.getlist('files[]')
        selected_labels = request.form.getlist('selected_labels[]')
        review_labels = COMPULSORY_LABELS + selected_labels
        # Create a new list to temporarily store the all the labels (default labels & self-added labels)
        all_labels = review_tags_list(review_labels)
        # Check the product name availability
        exist_in_database = check_product_availability(product_name, pre_product_name)
        if exist_in_database:
            flash("This product has been added to database", 'danger')
            return render_template('product/editproduct.html', title='Edit Product Page', form=form, all_labels=all_labels, compulsory_labels=COMPULSORY_LABELS, selected_labels=selected_labels, img_url_list=img_url_list)
        # Check the uploaded file types
        for file in files:
            if file and allow_file_type(file.filename):
                filename = secure_filename(file.filename)
                file_names.append(filename)
                # Save image file to project root
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
            else:
                flash('Allowed image types are -> png, jpg, jpeg, gif', 'danger')
                return render_template('product/editproduct.html', title='Edit Product Page', form=form, all_labels=all_labels, compulsory_labels=COMPULSORY_LABELS, selected_labels=selected_labels, img_url_list=img_url_list)
        # # Delete product previous photos in Firebase Storage
        # for img in list_img:
        #     blob = bucket.blob(img)
        #     blob.delete()
        # Upload images to Firebase Storage
        for image in file_names:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image)
            sto_path = product_name + '/' + image
            blob = bucket.blob(sto_path)
            blob.upload_from_filename(image_path)
            # Delete images from project root
            os.remove(image_path)
        # Define product details for storing in Firestore
        data = {
            u'productName': product_name,
            u'description': description,
            u'businessName': business_name,
            u'reviewLabel': review_labels
        }
        # Update the product's document in collection 'products'
        db.collection(u'products').document(doc.id).set(data)
        flash(f'The product was successfully updated', 'success')
        return redirect(url_for('business'))
    form.name.data = pre_product_name
    form.description.data = pre_description
    return render_template('product/editproduct.html', title='Edit Product Page', form=form, compulsory_labels=COMPULSORY_LABELS, all_labels=all_labels, selected_labels=pre_review_labels, img_url_list=img_url_list)


# Search Product
@app.route('/searchproduct', methods=["GET", "POST"])
def search_product():
    search_word = request.args.get('x')
    products = []
    all_products = []
    search_list = []
    # Get all the products from Firestore
    pro_docs = db.collection(u'products').stream()
    for doc in pro_docs:
        details = []
        # Get all the product details and store in a list
        doc_id = doc.id
        product_name = doc.get("productName")
        business_name = doc.get("businessName")
        description = doc.get("description")
        details.append(doc_id)
        details.append(product_name)
        details.append(description)
        details.append(business_name)
        # Find a product image path from Firebase Storage
        all_blobs = list(storage_client.list_blobs(bucket))
        for bb in all_blobs:
            if bb.name.find(product_name) == -1:
                continue
            else:
                img_path = bb.name
                break
        # Get the first product image URL
        blob = bucket.blob(img_path)
        blob.make_public()
        url = blob.public_url
        details.append(url)
        # Append to a list for gathering all the products
        all_products.append(details)
        # Store product and business names in search list for passing to filter_docs function
        search_list.append([product_name, business_name])
    # Filter the documents according to the input search word
    search_result_list = filter_docs(search_list, search_word)
    for i in search_result_list:
        # Add the final result product details to products list and pass to the html page for display
        products.append(all_products[i])
    if session['role'] == 'business':
        return render_template('business/index.html', title='Business page', products=products)
    else:
        return render_template('customer/index.html', title='Customer page', products=products)


# Delete Product
@app.route('/deleteproduct/<string:name>', methods=["GET", "POST"])
def delete_product(name):
    try:
        list_img = []
        # Find the product's document from Firestore
        docs = db.collection(u'products').where("productName", "==", name).stream()
        for doc in docs:
            data = {
                u'productName': doc.get("productName"),
                u'description': doc.get("description"),
                u'businessName': doc.get("businessName"),
                u'reviewLabel': doc.get("reviewLabel")
            }
            # Save a copy of deleted product into 'deleted_products' collection
            db.collection(u'deleted_products').document(doc.id).set(data)
            # Delete the product from 'products' collection
            db.collection(u'products').document(doc.id).delete()
        # Find the product image path from Firebase Storage
        list_img = image_storage_path(name)
        # Delete product photos in Firebase Storage
        for img in list_img:
            blob = bucket.blob(img)
            blob.delete()
        flash(f'The product {name} was deleted from your database', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        flash(f'Can not delete the product. Error: {str(e)}', 'danger')
        return redirect(url_for('home'))


# Product Review
@app.route('/addreview/<string:name>', methods=['GET', 'POST'])
def add_review(name):
    form = ReviewForm()
    tag_data_list = [('none', 'Choice ...')]
    products = [name]
     # Get all the product details from Firestore according to the product name
    pro_docs = db.collection(u'products').where("productName", "==", name).stream()
    for doc in pro_docs:
        review_labels = doc.get("reviewLabel")
    # Feedback Tag List
    for label in review_labels:
        tag_data = (label, label)
        tag_data_list.append(tag_data)
    form.tag_1.choices = form.tag_2.choices = form.tag_3.choices = tag_data_list
    # Find the product image paths from Firebase Storage
    list_img = image_storage_path(name)
    # Get the first product image URL
    for img in list_img:
        blob = bucket.blob(img)
        blob.make_public()
        url = blob.public_url
        break
    products.append(url)
    # When the connected html passing POST request (Submit Button is clicked)
    if request.method == "POST":
        customer_username = session['name']
        review_title = form.title.data
        review_content = form.feedback.data
        review_date = str(datetime.date.today())
        experience_date = str(form.date.data)
        tag_1 = form.tag_1.data
        tag_2 = form.tag_2.data
        tag_3 = form.tag_3.data
        review_tag = [tag_1, tag_2, tag_3]
        # Check the availability of review tag
        review_tag = [value for value in review_tag if value != 'none']
        # To ensure at least one review tag is selected 
        if not review_tag:
            flash(f'Please select at least one tag!', 'danger')
            return render_template('product/addreview.html',title='Add Review Page', form=form, products=products)  
        # To ensure not repeated review tag selected 
        if tag_1==tag_2!="none" or tag_1==tag_3!="none" or tag_2==tag_3!="none":
            # if tag_1==tag_2!="none" or tag_1==tag_3 or tag_2==tag_3:
            flash(f'Please do not select the same tags!', 'danger')
            return render_template('product/addreview.html',title='Add Review Page', form=form, products=products)  
        try:
            # Define review details for storing in Firestore
            review_data = {
                u'customer': customer_username,
                u'title': review_title,
                u'content': review_content,
                u'experienceDate': experience_date,
                u'reviewTags': review_tag,
                u'reviewDate': review_date,
                u'sentiment': None
            }
            # Add the customer review as a new 'customer_review' document in the 'products' collection
            review_doc = db.collection(u'products').document(doc.id).collection(u'customer_reviews').add(review_data)
            # Define review details for storing in Firestore
            sentiment_analysis_data = {
                u'review': review_content,
                u'customer': customer_username,
                u'productDocID': doc.id,
                u'reviewDocID': review_doc[1].id
            }
            # Add the customer review to the 'Review_q' collection for processing with the sentiment analysis model
            db.collection(u'Review_q').document().set(sentiment_analysis_data)
            flash(f'The review ({review_title}) was successfully added to database', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Can not add the review. Error: {str(e)}', 'danger')
            return render_template('product/addreview.html',title='Add Review Page', form=form, products=products)      
    return render_template('product/addreview.html',title='Add Review Page', form=form, products=products)


