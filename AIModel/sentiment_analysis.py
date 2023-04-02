import os
# Remove tensorflow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

from transformers import DistilBertTokenizerFast, TFDistilBertForSequenceClassification, logging
import tensorflow as tf
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import firestore
import threading
import time


# Global Variables
LABELS = ['Negative', 'Neutral', 'Positive']
LOADED_MODEL = TFDistilBertForSequenceClassification.from_pretrained("./AIModel/DistilBERT_model")
TOKENIZER = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
# Declaration that connect to the Firebase project
CRED = credentials.Certificate("./serviceAccountKey.json")
# Initialize Firebase admin
APP = firebase_admin.initialize_app(CRED, {'storageBucket': 'SentimentAnalysis.appspot.com'})
# Cloud Storage buckets
BUCKET = storage.bucket()
# Firestore database instance
DB = firestore.client()
CONDITION = True
logging.set_verbosity_error()


# Create a callback on_snapshot function to capture changes
def on_snapshot(col_snapshot, changes, read_time):
    # Listener that listen to review document
    print(u'Callback review document')
    review_queue = []
    customer_name_list = []
    doc_list = []
    for change in changes:
        # When there is a document added to the "Review_q" collection, it will start the process
        if change.type.name == 'ADDED':
            print(f'New document: {change.document.to_dict()}')
            dic = change.document.to_dict()
            if (change.document.id == 'default'):
                # Skip the default file that no need to process 
                print('Skip the default file')
                continue
            else:
                queue_doc_id = change.document.id
                # Get all the fields saved in the Firestore
                customer_name = dic.get("customer")
                review = dic.get("review")
                product_doc = dic.get("productDocID")
                review_doc = dic.get("reviewDocID")
                # Add review into queue list
                review_queue.append(review)
                customer_name_list.append(customer_name)
                # Save all the document ID into a list
                doc_id = []
                doc_id.append(queue_doc_id)
                doc_id.append(product_doc)
                doc_id.append(review_doc)
                doc_list.append(doc_id)

    # To check whether a review added to the queue
    if (len(review_queue) != 0):
        # Start looping to process every request 
        for i in range(len(review_queue)):
            try:
                sentiment = None
                print()
                print('Process Sentiment Analysis!!')
                # Save the sentiment in a variable
                sentiment = analyze_sentiment(review_queue[i])
                # Print out the details of the review, sentiment, and document ID
                print("Review: " + review_queue[i])
                print("Sentiment: " + sentiment)
                print("Review_q Doc ID: " + doc_list[i][0])
                print("Product Doc ID: " + doc_list[i][1])
                print("Customer Review Doc ID: " + doc_list[i][2])
                # Upload the sentiment to the review document
                DB.collection(u'products').document(doc_list[i][1]).collection(u'customer_reviews').document(doc_list[i][2]).update({u'sentiment': sentiment})
                print(f'The review ({doc_list[i][2]}) was successfully added for product ({doc_list[i][1]}) in Firestore')
            except Exception as e:
                # Create an exception for recording the fail processes
                print(f'Can not compute the sentiment. Error: {str(e)}')
                data = {
                    u'customer': customer_name_list,
                    u'productDocID': doc_list[i][1],
                    u'review': review_queue[i],
                    u'reviewDocID': doc_list[i][2],
                }
                # Upload the fail document to fail_review_q document in Firestore
                DB.collection(u'fail_review_q').document(doc_list[i][0]).set(data)
            # After done upload to review/fail_review_q document. Delete it from Review_q 
            DB.collection(u'Review_q').document(doc_list[i][0]).delete()
    # callback_done.set()


# Create a function for analyzing sentiment
def analyze_sentiment(review):
    # Convert the review sentence into a list of tokens according to the model's requirement
    predict_input = TOKENIZER.encode(review, truncation=True, padding=True, return_tensors="tf")
    # Apply pre-trained DistilBERT Model for predicting the sentiment
    tf_output = LOADED_MODEL.predict(predict_input)[0]
    # Map the model output to either 0, 1, or 2
    tf_prediction = tf.nn.softmax(tf_output, axis=1)
    # Remain only the largest value across axes of a tensor
    label = tf.argmax(tf_prediction, axis=1)
    label = label.numpy()
    return LABELS[label[0]]

# MAIN
print("Program Start")
# Create an event for notifying main thread.
callback_done = threading.Event()
# Start to listen to Firestore document
doc_ref = DB.collection(u'Review_q')

# Watch the document in real-time
doc_ref.on_snapshot(on_snapshot)


# Simulate a delay for waiting a document uploaded to the Firestore
while CONDITION:
    # Sleep for 60 seconds
    time.sleep(60)
    print('Processing...')
