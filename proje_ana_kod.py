import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
import glob
import os

print("STAGE 1: Loading and Merging Datasets...")

# Find all CSV files in the directory
csv_files = glob.glob("*.csv")
df_list = []

for file in csv_files:
    try:
        temp_df = pd.read_csv(file, low_memory=False)
        # Only extract files/columns that have review text and sentiment score
        if 'Yorum_Metni' in temp_df.columns and 'Tutum_Skoru' in temp_df.columns:
            df_list.append(temp_df[['Yorum_Metni', 'Tutum_Skoru']])
        elif 'text' in temp_df.columns and 'sentiment' in temp_df.columns:
            # Catch alternative naming and standardize
            temp = temp_df[['text', 'sentiment']].rename(columns={'text': 'Yorum_Metni', 'sentiment': 'Tutum_Skoru'})
            df_list.append(temp)
    except Exception as e:
        pass

# Merge all data into a single dataframe
df = pd.concat(df_list, ignore_index=True)
print(f"Successfully merged {len(df)} reviews from {len(df_list)} suitable files.")

print("\nSTAGE 2: Data Preprocessing...")
# Drop missing values
df = df.dropna(subset=['Yorum_Metni', 'Tutum_Skoru'])

# XGBoost and LightGBM require labels to be consecutive integers like 0, 1, 2.
def correct_label(value):
    if str(value).strip() in ['-1', '-1.0', 'Olumsuz', 'Negative']: return 0
    if str(value).strip() in ['0', '0.0', 'Nötr', 'Neutral']: return 1
    if str(value).strip() in ['1', '1.0', 'Olumlu', 'Positive']: return 2
    return None

df['Target'] = df['Tutum_Skoru'].apply(correct_label)
df = df.dropna(subset=['Target']) # Drop undefined labels
df['Target'] = df['Target'].astype(int)

X = df['Yorum_Metni']
y = df['Target']

# Train-Test Split (80% Train, 20% Test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# TF-IDF Vectorization
vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

print("\nSTAGE 3: Training Ensemble Models...")
models = {
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "XGBoost": xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42),
    "LightGBM": lgb.LGBMClassifier(random_state=42, verbose=-1)
}

results = {}

for name, model in models.items():
    print(f"-> Training and testing {name}...")
    model.fit(X_train_vec, y_train)
    y_pred = model.predict(X_test_vec)
    
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    cm = confusion_matrix(y_test, y_pred)
    results[name] = {'Accuracy': acc, 'F1-Score': f1, 'CM': cm}

print("\nSTAGE 4: Performance Results (For the Paper)")
for name, metrics in results.items():
    print(f"[{name}] Accuracy: {metrics['Accuracy']:.4f} | F1-Score: {metrics['F1-Score']:.4f}")

# Generate high-resolution plot for the paper
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
classes = ['Negative (0)', 'Neutral (1)', 'Positive (2)']

for i, (name, metrics) in enumerate(results.items()):
    sns.heatmap(metrics['CM'], annot=True, fmt='d', cmap='Blues', ax=axes[i], 
                xticklabels=classes, yticklabels=classes)
    axes[i].set_title(f'{name}\nAccuracy: {metrics["Accuracy"]:.4f}')
    axes[i].set_ylabel('True Class')
    axes[i].set_xlabel('Predicted Class')

plt.tight_layout()
plt.savefig('confusion_matrices.png', dpi=300)
print("\nSUCCESS! 'confusion_matrices.png' has been saved for use in the paper.")