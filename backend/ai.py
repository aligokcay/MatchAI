import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from keras import models, layers
import joblib

# 1. VERİ HAZIRLAMA
data = pd.read_json("fixtureData.json")

# Veriyi üç parçaya böl
num_samples = len(data)
low, mid = num_samples // 3, 2 * (num_samples // 3)

data["weight"] = 0.5
data.loc[low:mid, "weight"] = 0.75
data.loc[mid:, "weight"] = 1.25

# Kategorik değişkenleri one-hot encode et
categorical_features = ['competition', 'home_away', 'formation', 'opponent_formation']
encoder = OneHotEncoder()
encoded_features = encoder.fit_transform(data[categorical_features]).toarray()

print("Kategoriler ve kodlamalar:")
#for feature, categories in zip(categorical_features, encoder.categories_):
    #print(f"{feature}: {categories}")

# Sayısal değişkenleri ölçekle
scaler = StandardScaler()
numerical_features = scaler.fit_transform(data[['opponent_market_value']])

# Girdi verilerini birleştir
X = np.hstack((numerical_features, encoded_features))
#print(X)

# Çıktı verilerini hazırla
result_categories = ['W', 'D', 'L']
y_result = pd.get_dummies(data['result'])
# Sonuçları 'W', 'D', 'L' sırasına göre sıralayın
y_result = y_result.reindex(columns=result_categories, fill_value=0)
print(y_result)
y_goals = data[['goals_for', 'goals_against']].values  # Gol tahmini için

# Eğitim ve test setlerini ayır
X_train, X_test, y_result_train, y_result_test, y_goals_train, y_goals_test, w_train, w_test = train_test_split(
    X, y_result, y_goals, data["weight"].values, test_size=0.2, random_state=42
)

# 2. MODEL TANIMLAMA
# Sonuç tahmini için Classification modeli
result_model = models.Sequential([
    layers.Input(shape=(X.shape[1],)),  # İlk katmanda Input() kullanıldı
    layers.Dense(128, activation='relu'),
    layers.Dense(64, activation='relu'),
    layers.Dense(3, activation='softmax')  # W, D, L için 3 sınıf
])
result_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Gol tahmini için Regression modeli
goals_model = models.Sequential([
    layers.Input(shape=(X.shape[1],)),  # İlk katmanda Input() kullanıldı
    layers.Dense(128, activation='relu'),
    layers.Dense(64, activation='relu'),
    layers.Dense(2)  # goals_for ve goals_against için 2 çıktı
])
goals_model.compile(optimizer='adam', loss='mse', metrics=['mae']) # mean absolute error

# 3. MODEL EĞİTİMİ
# Sonuç tahmini için model eğitimi
print("Training result prediction model...")
result_model.fit(X_train, y_result_train, sample_weight=w_train, epochs=50, batch_size=16, validation_data=(X_test, y_result_test))

# Gol tahmini için model eğitimi
print("Training goals prediction model...")
goals_model.fit(X_train, y_goals_train, sample_weight=w_train, epochs=50, batch_size=16, validation_data=(X_test, y_goals_test))

# 4. MODEL VE SCALER KAYDETME
result_model.save("result_model.h5", save_format="h5")
goals_model.save("goals_model.h5", save_format="h5")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(encoder, "encoder.pkl")

print("Modeller ve dönüştürücüler kaydedildi.")
