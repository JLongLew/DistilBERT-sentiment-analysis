from flask import *
from website import app, auth, db, bucket, storage_client
from .forms import RegistrationForm
import datetime


# Customer HomePage
@app.route('/customer')
def customer():
    products = []
    # Get all the products from Firestore
    pro_docs = db.collection(u'products').stream()
    for doc in pro_docs:
        details = []
        # Get all the product details and store in a list
        doc_id = doc.id
        product_name = doc.get("productName")
        description = doc.get("description")
        business_name = doc.get("businessName")
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
        # Append to a list passing to the html page for display
        products.append(details)
    return render_template('customer/index.html', title='Customer page', products=products)


# Customer Registration
@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    # Create instance of registration form
    form = RegistrationForm()
    # If the form is valid on submission
    if form.validate_on_submit():
        input_username = form.username.data
        input_email = form.email.data
        password = form.password.data
        email_list = []
        username_list = []
        # Get all the registered username and email
        docs = db.collection(u'users').get()
        for doc in docs:
            all_username = doc.get("username")
            all_email = doc.get("email")
            username_list.append(all_username)
            email_list.append(all_email)
        # Check the availability of username
        for username in username_list:
            if input_username == username:
                flash("This username have been registered", 'danger')
                return render_template("customer/register.html", title='Customer Registration', form=form)
        # Check the availability of email address
        for email in email_list:
            if input_email == email:
                flash("This email have been registered", 'danger')
                return render_template("customer/register.html", title='Customer Registration', form=form)
        try:
            # Add email and password into authentication
            user = auth.create_user_with_email_and_password(input_email, password)
            login_data = {
                        u'username': form.username.data,
                        u'email': form.email.data,
                        u'role': 'customer'
                    }
            # Add a new doc in collection 'users' with random document ID
            db.collection(u'users').document().set(login_data)
            age = datetime.date.today().year - form.dob.data.year
            data = {
                        u'username': form.username.data,
                        u'firstName': form.firstName.data,
                        u'lastName': form.lastName.data,
                        u'gender': form.gender.data,
                        u'age': age,
                        u'dob': str(form.dob.data),
                        u'email': form.email.data,
                        u'contact': form.contact.data,
                        u'address': form.address.data,
                        u'city': form.city.data,
                        u'country': form.country.data,
                        u'role': 'customer'
                    }
            # Add a new doc in collection 'businesses' with random document ID
            db.collection(u'customers').document().set(data)
            # Set the session
            session['usrID'] = user['idToken']
            session['email'] = form.email.data
            session['name'] = form.username.data
            session['role'] = 'customer'
            flash(f'Welcome {form.firstName.data}! Thanks for registering', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Can not register the customer. Error: {str(e)}', 'danger')
            return render_template('customer/register.html',title='Customer Registration', form=form)
    return render_template('customer/register.html',title='Customer Registration', form=form)

