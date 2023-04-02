# Sentiment Analysis of Product Reviews using Machine Learning

## Overview
This project is a web-based product review analysis system that is able to extract the information from words, sentences, or paragraphs by existing customers and classify the polarity of the information, which would provide e-commerce businesses with better insight into their products and optimize potential customers’ decision-making.<br />
* Poster
<div align="center">
<img src="https://user-images.githubusercontent.com/92619008/228438310-b58e1e7d-fa9c-4151-b047-44c0d8f3762d.png">
</div>



* Model Performance Testing Result
<div align="center">
<img src="https://user-images.githubusercontent.com/92619008/228439113-00e98918-89a8-4c80-98a2-5cb0df529cdc.png">
</div>

<br />

<div align="center">

Result | Precision | Recall | F1-Score
--- | --- | --- | --- 
Negative | 0.8891 | 0.9321 | 0.9101
Neutral | 0.6474 | 0.4632 | 0.54
Positive	| 0.954 |	0.9738	| 0.9638
Micro Averaging	| 0.918	| 0.918	| 0.918
Macro Averaging	| 0.8302 |	0.7897 |	0.8046
Weighted Averaging |	0.9109	| 0.918	| 0.9129

</div>


* (Website Screenshots) Sample 1: Customer Homepage
<div align="center">
<img src="https://user-images.githubusercontent.com/92619008/228441053-a8013c0b-e7c5-4b26-a0f7-38666067c614.png">
</div>



* (Website Screenshots) Sample 2: Customer Reviews
<div align="center">
<img src="https://user-images.githubusercontent.com/92619008/228441101-8be97537-9c34-4594-bb2e-d7309b2eae25.png">
</div>



* (Website Screenshots) Sample 3: Product Analysis
<div align="center">
<img src="https://user-images.githubusercontent.com/92619008/228441107-fefd1598-6900-49b1-ba55-2df18aaacdc7.png">
</div>



## Requirements
- Python 3.8 or higher
- Flask 1.1.1 or higher
- HTML5
- CSS3

## Installation

1. Clone the repository:
```bash
git clone git@github.com:JLongLew/DistilBERT-sentiment-analysis.git
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Train a DistilBERT AI Model by navigating to AIModel/DistilBERT_Model_Training.ipynb and run the program

4. Once the model is fine-tuned successfully (a new folder called 'DistilBERT_model' will be created in AIModel folder), run the following command to start the real-time sentiment analysis:
```bash
python AIModel/sentiment_analysis.py
```

5. Run the following command to start the Flask application:
```bash
python run.py
```

6. Navigate to http://localhost:5000 to use the application.

## Credits
The Sentiment Analysis model was fine-tuned using the DistilBERT model from [Hugging Face Transformers library](https://github.com/huggingface/transformers).
