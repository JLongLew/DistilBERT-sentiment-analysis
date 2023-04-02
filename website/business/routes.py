from flask import *
from website import app, auth, db, bucket, storage_client
from .forms import LoginForm, RegistrationForm

# Home
@app.route('/')
def home():
    if ('usrID' in session):
        if (session['role'] == 'business'):
            return redirect(url_for('business'))
    return redirect(url_for('customer'))


# Business HomePage
@app.route('/business')
def business():
    products = []
    # Get all the added products from Firestore according to the session's business name
    pro_docs = db.collection(u'products').where("businessName", "==", session['name']).stream()
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
    return render_template('business/index.html', title='Business page', products=products)


# User Login
@app.route("/login", methods=["GET", "POST"])
def login():
    # Create instance of login form
    form = LoginForm()
    # If the form is valid on submission
    if form.validate_on_submit():
        bus_email_list = []
        cus_email_list = []
        input_email = form.email.data
        password = form.password.data
        role = form.role.data
        # Ensure the input role has a valid value
        if role == 'none':
            flash(f'Please select a role!', 'danger')
            return render_template("login.html", title='Login page', form=form)
        # Get all the registered email from Firestore
        docs = db.collection(u'users').get()
        for doc in docs:
            if doc.get("role") == "business":
                bus_email = doc.get("email")
                bus_email_list.append(bus_email)
            else:
                cus_email = doc.get("email")
                cus_email_list.append(cus_email)
        # Classify the user role
        email_list = []
        if role == 'bus':
            email_list = bus_email_list
        else:
            email_list = cus_email_list
        # Check the input email with the email list
        for email in email_list:
            if input_email == email:
                try:
                    # login the user
                    user = auth.sign_in_with_email_and_password(input_email, password)
                    user_id = user['idToken']
                    # set the session
                    session['usrID'] = user_id
                    session['email'] = input_email
                    if role == 'bus':
                        bus_docs = db.collection(u'businesses').where("email", "==", input_email).get()
                        for doc in bus_docs:
                            user_name = doc.get("name")
                        session['role'] = 'business'
                        session['name'] = user_name
                        flash(f'Successfully Login! Welcome {user_name}!', 'success')
                        return redirect(url_for('business'))
                    elif role == 'cus':
                        cus_docs = db.collection(u'customers').where("email", "==", input_email).get()
                        for doc in cus_docs:
                            user_name = doc.get("username")
                        session['role'] = 'customer'
                        session['name'] = user_name
                        flash(f'Successfully Login! Welcome {user_name}!', 'success')
                        return redirect(url_for('customer'))
                except:
                    flash(f'Wrong password!', 'danger')
                    return render_template("login.html", title='Login page', form=form)
        else:
            flash(f'Email is not registered!', 'danger')
            return render_template("login.html", title='Login page', form=form)
    return render_template('login.html', title='Login page', form=form)


# User Logout
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Reset the session
    session.pop('usrID', None)
    session.pop('email', None)
    session.pop('role', None)
    session.pop('name', None)
    # session.pop('usrID', None)
    # session.pop('usrID', None)
    flash("You Have Been Logged Out!", 'warning')
    return redirect(url_for('login'))


# Business Registration
@app.route('/business/register', methods=['GET', 'POST'])
def business_register():
    # Create instance of registration form
    form = RegistrationForm()
    # If the form is valid on submission
    if form.validate_on_submit():
        input_email = form.email.data
        input_name = form.name.data
        password = form.password.data
        email_list = []
        name_list = []
        # Get all the registered email and business name from 'users' collection
        docs = db.collection(u'users').get()
        for doc in docs:
            all_email = doc.get("email")
            all_name = doc.get("username")
            email_list.append(all_email)
            name_list.append(all_name)
        # Check the availability of business name
        for name in name_list:
            if input_name == name:
                flash("This business name have been registered", 'danger')
                return render_template("business/register.html", title='Business Registration', form=form)
        # Check the availability of email address
        for email in email_list:
            if input_email == email:
                flash("This email have been registered", 'danger')
                return render_template("business/register.html", title='Business Registration', form=form)
        try:
            # Add email and password into authentication
            user = auth.create_user_with_email_and_password(input_email, password)
            login_data = {
                        u'username': form.name.data,
                        u'email': form.email.data,
                        u'role': 'business'
                    }
            # Add a new doc in collection 'users' with random document ID
            db.collection(u'users').document().set(login_data)
            data = {
                        u'name': form.name.data,
                        u'email': form.email.data,
                        u'contact': form.contact.data,
                        u'address': form.address.data,
                        u'city': form.city.data,
                        u'country': form.country.data,
                        u'role': 'business'
                    }
            # Add a new doc in collection 'businesses' with random document ID
            db.collection(u'businesses').document().set(data)
            # Set the session
            session['usrID'] = user['idToken']
            session['email'] = form.email.data
            session['name'] = form.name.data
            session['role'] = 'business'
            flash(f'Welcome {form.name.data}! Thanks for registering', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Can not register the customer. Error: {str(e)}', 'danger')
            return render_template('customer/register.html',title='Customer Registration', form=form)
    return render_template('business/register.html',title='Business Registration', form=form)




