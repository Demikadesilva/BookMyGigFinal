BookMyGig

Exploring how data driven intelligence can improve fairness, personalization, and trust in musicians - client booking systems.

Overview

BookMyGig is an AI-powered musician booking and recommendation platform designed to enhance decision-making in service-based digital marketplaces. The system integrates multiple machine learning components into a unified pipeline to address key challenges such as cold start, recommendation accuracy, data reliability, and pricing transparency.

This project was developed as a final year research study and focuses on combining recommendation systems, sentiment analysis, anomaly detection, dynamic pricing, and explainable AI within a single architecture.

Key Features
Hybrid Recommendation System (Content-Based + Collaborative Filtering)
Sentiment Analysis using VADER and DistilBERT
Anomaly Detection using Isolation Forest
Dynamic Pricing using Linear Regression and LightGBM
Demand Forecasting with time-series features
Explainable AI using SHAP
Cold Start Handling using adaptive hybrid strategies


System Architecture

The system follows a modular pipeline:

Data Layer
Synthetic datasets generated for musicians, clients, bookings, and reviews.

Preprocessing & Feature Engineering
-Missing value handling
-Encoding (Label / One-hot)
-Normalization
-Feature creation (review length, sentiment gap, aggregated sentiment)

Model Layer (Parallel Execution)
-Recommendation System
-Sentiment Analysis
-Anomaly Detection
-Dynamic Pricing
-Demand Forecasting

Decision Layer
-Hybrid scoring
-Sentiment-based ranking adjustment
-Anomaly filtering
-SHAP-based explainability

Output Layer
-Top-N recommendations
-Predicted pricing
-Sentiment insights
-Explainability graphs

Evaluation Layer
-Recommendation: Precision@K, Recall@K, NDCG
-Sentiment: Accuracy, Precision, Recall, F1-score
-Pricing: RMSE, MAE, R²
-Anomaly Detection: Distribution analysis


Project Structure
New V1/
│
├── data/               # Synthetic and processed datasets  
├── models/             # Model definitions  
├── training/           # Training scripts  
├── pipelines/          # End-to-end ML pipelines  
├── evaluation/         # Model evaluation scripts  
├── notebooks/          # Experimentation notebooks  
├── utils/              # Helper functions  
├── logs/               # Logging outputs  
├── saved_models/       # Trained model artifacts  
├── config.py           # Configuration file  
├── requirements.txt    # Dependencies  

Technologies Used
-Python
-Scikit-learn
-LightGBM
-Transformers (DistilBERT)
-VADER Sentiment
-SHAP
-Pandas, NumPy

Installation

Clone the repository:

git clone https://github.com/your-username/BookMyGig.git
cd BookMyGig

Install dependencies:

pip install -r requirements.txt
Usage

Run the pipeline:
python pipelines/main_pipeline.py

Or explore experiments via:
notebooks/


Research Contributions
-Introduces an adaptive hybrid recommendation system for cold start handling
-Integrates sentiment analysis directly into recommendation ranking
-Improves data reliability through anomaly filtering
-Applies explainable AI (SHAP) to pricing decisions
-Demonstrates a unified architecture combining multiple AI techniques

Limitations
-Uses synthetic data (Faker-based)
-Limited dataset scale
-Evaluated in offline environment
-Does not include real-time deployment

Future Work
-Apply system on real-world datasets
-Implement deep learning-based recommendation models
-Add real-time recommendation and pricing
-Extend explainability to recommendation outputs
-Incorporate user feedback loops and live evaluation

License
This project is licensed under the terms of the LICENSE file included in the repository.

Author
Demika De Silva
BSc Artificial Intelligence and Data Science
Final Year Research Project
